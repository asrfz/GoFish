import os
import io
import base64
import pickle
import re
from contextlib import asynccontextmanager
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pydantic import BaseModel
from PIL import Image
import torch
import torch.nn as nn
from torchvision import transforms, models
from sentence_transformers import SentenceTransformer
import numpy as np

load_dotenv()

# Environment variables
MONGO_URL = os.getenv("MONGO_URL")

# Configuration
CLIP_MODEL_NAME = "clip-ViT-B-32"
EMBEDDING_DIMENSIONS = 512
DB_NAME = "castnet"
REFERENCE_COLLECTION = "fish_reference"
CATCHES_COLLECTION = "catches"
MODEL_PATH = "./models/fish_classifier.pth"
LABEL_ENCODER_PATH = "./models/label_encoder.pkl"

# Global variables for models (loaded in lifespan)
pytorch_model = None
label_encoder = None
clip_model = None
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Image transforms for PyTorch model
IMG_SIZE = 224
transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

# Pydantic models
class ScanFishRequest(BaseModel):
    image_base64: str

class ScanFishResponse(BaseModel):
    species: str
    confidence: float  # Combined confidence score (0-1)
    pytorch_confidence: Optional[float] = None  # PyTorch model confidence
    vector_confidence: Optional[float] = None  # Vector search confidence
    method: str  # "pytorch", "vector", or "hybrid"

class CatchModel(BaseModel):
    species: str
    confidence: float
    scanned_at: datetime

def create_pytorch_model(num_classes):
    """Create ResNet50 model (same architecture as training)"""
    model = models.resnet50(weights=None)  # We'll load our trained weights
    num_features = model.fc.in_features
    model.fc = nn.Linear(num_features, num_classes)
    return model

# Lifespan context manager for MongoDB connection and model loading
@asynccontextmanager
async def lifespan(app: FastAPI):
    global pytorch_model, label_encoder, clip_model
    
    # --- STARTUP LOGIC ---
    print("🚀 Starting CastNet Backend...")
    
    # Load PyTorch Classification Model
    print("⏳ Loading PyTorch fish classification model...")
    try:
        if os.path.exists(MODEL_PATH):
            # Load label encoder
            with open(LABEL_ENCODER_PATH, 'rb') as f:
                label_encoder = pickle.load(f)
            
            num_classes = len(label_encoder.classes_)
            pytorch_model = create_pytorch_model(num_classes)
            
            # Load trained weights
            checkpoint = torch.load(MODEL_PATH, map_location=device)
            pytorch_model.load_state_dict(checkpoint['model_state_dict'])
            pytorch_model.to(device)
            pytorch_model.eval()
            
            print(f"✅ PyTorch model loaded successfully!")
            print(f"   Model accuracy: {checkpoint.get('val_acc', 'N/A'):.2f}%")
            print(f"   Classes: {num_classes}")
        else:
            print("⚠️ PyTorch model not found. Run train_fish_model.py first.")
            print("   App will use vector search only mode.")
    except Exception as e:
        print(f"❌ Failed to load PyTorch model: {e}")
        print("   App will use vector search only mode.")
    
    # Load CLIP Model for vector embeddings
    print(f"⏳ Loading CLIP model for vector embeddings: {CLIP_MODEL_NAME}...")
    try:
        clip_model = SentenceTransformer(CLIP_MODEL_NAME)
        print(f"✅ CLIP model loaded successfully!")
        print(f"   Embedding dimensions: {EMBEDDING_DIMENSIONS}")
    except Exception as e:
        print(f"❌ Failed to load CLIP model: {e}")
        print("⚠️ Vector embeddings will not be available.")
    
    # Connect to MongoDB
    if not MONGO_URL:
        print("⚠️ WARNING: No MONGO_URL found in .env - database features will be disabled")
    else:
        print("⏳ Connecting to MongoDB...")
        try:
            app.mongodb_client = AsyncIOMotorClient(MONGO_URL)
            app.mongodb = app.mongodb_client.get_database(DB_NAME)
            await app.mongodb.command("ping")
            print("✅ SUCCESS: Connected to MongoDB Atlas!")
            
            try:
                collection = app.mongodb[REFERENCE_COLLECTION]
                count = await collection.count_documents({})
                print(f"   Reference collection '{REFERENCE_COLLECTION}' has {count} documents")
            except Exception as e:
                print(f"⚠️ Could not check reference collection: {e}")
        except Exception as e:
            print(f"❌ CONNECTION FAILED: {e}")
    
    yield  # The app runs here
    
    # --- SHUTDOWN LOGIC ---
    if hasattr(app, 'mongodb_client'):
        app.mongodb_client.close()
        print("🛑 Database connection closed.")
    print("🛑 Shutting down...")

# Initialize FastAPI app
app = FastAPI(
    title="CastNet API",
    description="Fish Scanner Backend (PyTorch + Vector Embeddings)",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    reference_count = 0
    if hasattr(app, 'mongodb'):
        try:
            collection = app.mongodb[REFERENCE_COLLECTION]
            reference_count = await collection.count_documents({})
        except:
            pass
    
    return {
        "message": "CastNet Backend is Online!",
        "status": "Connected to DB" if hasattr(app, 'mongodb') else "DB not configured",
        "pytorch_model_loaded": pytorch_model is not None,
        "clip_model_loaded": clip_model is not None,
        "reference_fish_count": reference_count,
        "device": str(device)
    }

def classify_with_pytorch(image: Image.Image) -> Optional[dict]:
    """
    Classify fish using trained PyTorch model.
    Returns: {species: str, confidence: float} or None if model not loaded
    """
    global pytorch_model, label_encoder
    
    if pytorch_model is None or label_encoder is None:
        return None
    
    try:
        # Preprocess image
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        image_tensor = transform(image).unsqueeze(0).to(device)
        
        # Get prediction
        with torch.no_grad():
            outputs = pytorch_model(image_tensor)
            probabilities = torch.nn.functional.softmax(outputs[0], dim=0)
            confidence, predicted_idx = torch.max(probabilities, 0)
        
        species_name = label_encoder.inverse_transform([predicted_idx.item()])[0]
        
        return {
            "species": species_name,
            "confidence": float(confidence.item())
        }
    except Exception as e:
        print(f"❌ Error in PyTorch classification: {e}")
        import traceback
        traceback.print_exc()
        return None

def encode_image_to_embedding(image: Image.Image) -> list:
    """Convert PIL Image to embedding vector using CLIP."""
    global clip_model
    
    if clip_model is None:
        raise ValueError("CLIP model not loaded.")
    
    try:
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        embedding = clip_model.encode(image, convert_to_numpy=True)
        return embedding.tolist()
    except Exception as e:
        print(f"❌ Error encoding image: {e}")
        raise

async def search_similar_fish_vector(query_embedding: list, top_k: int = 5) -> Optional[list]:
    """
    Search for similar fish using vector embeddings.
    Returns: List of {species: str, score: float} or None
    """
    if not hasattr(app, 'mongodb') or clip_model is None:
        return None
    
    try:
        collection = app.mongodb[REFERENCE_COLLECTION]
        
        # Try vector search first
        try:
            pipeline = [
                {
                    "$vectorSearch": {
                        "index": "vector_index",
                        "path": "embedding",
                        "queryVector": query_embedding,
                        "numCandidates": 100,
                        "limit": top_k
                    }
                },
                {
                    "$project": {
                        "species": 1,
                        "score": {"$meta": "vectorSearchScore"}
                    }
                }
            ]
            
            cursor = collection.aggregate(pipeline)
            results = await cursor.to_list(length=top_k)
            
            if results:
                return [{"species": r["species"], "score": float(r["score"])} for r in results]
        except Exception as e:
            print(f"⚠️ Vector search failed: {e}, using fallback...")
            pass
        
        # Fallback: manual cosine similarity
        query_vec = np.array(query_embedding)
        all_fish = await collection.find({}).to_list(length=1000)  # Limit for performance
        
        matches = []
        for fish in all_fish:
            if "embedding" not in fish:
                continue
            
            ref_vec = np.array(fish["embedding"])
            if query_vec.shape != ref_vec.shape:
                continue
            
            dot_product = np.dot(query_vec, ref_vec)
            norm_query = np.linalg.norm(query_vec)
            norm_ref = np.linalg.norm(ref_vec)
            
            if norm_query > 0 and norm_ref > 0:
                similarity = dot_product / (norm_query * norm_ref)
                matches.append({
                    "species": fish["species"],
                    "score": float(similarity)
                })
        
        # Sort by score and return top_k
        matches.sort(key=lambda x: x["score"], reverse=True)
        return matches[:top_k] if matches else None
        
    except Exception as e:
        print(f"❌ Error in vector search: {e}")
        return None

@app.post("/api/scan-fish", response_model=ScanFishResponse)
async def scan_fish(request: ScanFishRequest):
    """
    Scan fish image: Use PyTorch model for classification, refine with vector search.
    """
    try:
        # Decode Base64 image
        try:
            if ',' in request.image_base64:
                image_data = base64.b64decode(request.image_base64.split(',')[-1])
            else:
                image_data = base64.b64decode(request.image_base64)
            
            image = Image.open(io.BytesIO(image_data))
            if image.mode != 'RGB':
                image = image.convert('RGB')
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to decode image: {str(e)}")
        
        # Step 1: Classify with PyTorch model
        pytorch_result = classify_with_pytorch(image)
        
        # Step 2: Get vector embedding and search
        vector_result = None
        vector_confidence = None
        
        if clip_model is not None:
            try:
                query_embedding = encode_image_to_embedding(image)
                vector_matches = await search_similar_fish_vector(query_embedding, top_k=3)
                
                if vector_matches and len(vector_matches) > 0:
                    vector_result = vector_matches[0]  # Top match
                    vector_confidence = vector_result["score"]
            except Exception as e:
                print(f"⚠️ Vector search error: {e}")
        
        # Step 3: Combine results (hybrid approach)
        final_species = None
        final_confidence = 0.0
        method = "unknown"
        
        if pytorch_result and vector_result:
            # Both models agree - use weighted average
            pytorch_conf = pytorch_result["confidence"]
            vector_conf = vector_confidence
            
            if pytorch_result["species"] == vector_result["species"]:
                # Models agree - boost confidence
                final_species = pytorch_result["species"]
                final_confidence = 0.7 * pytorch_conf + 0.3 * vector_conf
                method = "hybrid_agree"
            else:
                # Models disagree - use PyTorch (more reliable for classification)
                final_species = pytorch_result["species"]
                final_confidence = pytorch_conf * 0.8  # Reduce confidence when they disagree
                method = "hybrid_disagree"
        elif pytorch_result:
            # Only PyTorch model available
            final_species = pytorch_result["species"]
            final_confidence = pytorch_result["confidence"]
            method = "pytorch"
        elif vector_result:
            # Only vector search available
            final_species = vector_result["species"]
            final_confidence = vector_confidence
            method = "vector"
        else:
            raise HTTPException(
                status_code=404,
                detail="No model available. Please train the PyTorch model or ensure vector database is populated."
            )
        
        # Step 4: Save to MongoDB
        if hasattr(app, 'mongodb'):
            try:
                catch_document = {
                    "species": final_species,
                    "confidence": final_confidence,
                    "pytorch_confidence": pytorch_result["confidence"] if pytorch_result else None,
                    "vector_confidence": vector_confidence,
                    "method": method,
                    "scanned_at": datetime.utcnow()
                }
                
                collection = app.mongodb[CATCHES_COLLECTION]
                await collection.insert_one(catch_document)
                print(f"✅ Saved catch: {final_species} (confidence: {final_confidence:.2%}, method: {method})")
            except Exception as e:
                print(f"⚠️ Failed to save: {e}")
        
        return ScanFishResponse(
            species=final_species,
            confidence=final_confidence,
            pytorch_confidence=pytorch_result["confidence"] if pytorch_result else None,
            vector_confidence=vector_confidence,
            method=method
        )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error scanning fish: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing fish scan: {str(e)}")

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    reference_count = 0
    if hasattr(app, 'mongodb'):
        try:
            collection = app.mongodb[REFERENCE_COLLECTION]
            reference_count = await collection.count_documents({})
        except:
            pass
    
    return {
        "status": "healthy",
        "mongodb_connected": hasattr(app, 'mongodb'),
        "pytorch_model_loaded": pytorch_model is not None,
        "clip_model_loaded": clip_model is not None,
        "reference_fish_count": reference_count
    }
