"""
GoFish Unified API - Complete Fishing Application
Integrates:
1. Fish Scanner (PyTorch + Vector Search) - camera identification
2. Fishing Spots API - Ontario habitat data with weather
3. Safety & Recipes (Moorcheh Brain) - evidence-based guidance
"""

import os
import io
import json
import base64
import pickle
import math
import asyncio
import httpx
from contextlib import asynccontextmanager
from typing import Optional, Dict, List, Any
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
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

# ============================================================================
# ENVIRONMENT & CONFIG
# ============================================================================
MONGO_URL = os.getenv("MONGO_URL")
DB_NAME = os.getenv("DB_NAME", "castnet")
PORT = int(os.getenv("PORT", "8000"))

# Fish Scanner Config
CLIP_MODEL_NAME = "clip-ViT-B-32"
EMBEDDING_DIMENSIONS = 512
REFERENCE_COLLECTION = "fish_reference"
CATCHES_COLLECTION = "catches"
MODEL_PATH = Path(__file__).parent / "fish-scan" / "models" / "fish_classifier.pth"
LABEL_ENCODER_PATH = Path(__file__).parent / "fish-scan" / "models" / "label_encoder.pkl"

# Fishing Spots Config
GEOJSON_PATH = Path(__file__).parent / "backend" / "fish_hab_type_wgs84_scored.geojson"
OPEN_METEO_API = "https://api.open-meteo.com/v1/forecast"

SPECIES_KEYWORDS = {
    "walleye": ["walleye", "pickerel", "yellow pickerel"],
    "bass": ["bass", "smallmouth", "largemouth", "smallmouth bass", "largemouth bass"],
    "trout": ["trout", "brook trout", "rainbow trout", "lake trout"],
    "pike": ["pike", "northern pike", "muskellunge", "muskie", "gar pike"],
    "perch": ["perch", "yellow perch"],
}

# Moorcheh Config
MOORCHEH_API_KEY = os.getenv("MOORCHEH_API_KEY", "")
MOORCHEH_API_URL = os.getenv("MOORCHEH_API_URL", "https://api.moorcheh.com")
NS_SAFETY = os.getenv("NS_SAFETY", "safety_memory")
NS_RECIPES = os.getenv("NS_RECIPES", "recipe_memory")
NS_COMMUNITY = os.getenv("NS_COMMUNITY", "community_memory")

# ============================================================================
# GLOBAL STATE
# ============================================================================
pytorch_model = None
label_encoder = None
clip_model = None
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Fish Scanner transforms
IMG_SIZE = 224
transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

# Fishing Spots data
fishing_spots = []
SCORE_MIN = 1.0
SCORE_MAX = 1.0

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

# --------- Fish Scanner Models ---------
class ScanFishRequest(BaseModel):
    image_base64: str

class ScanFishResponse(BaseModel):
    species: str
    confidence: float
    pytorch_confidence: Optional[float] = None
    vector_confidence: Optional[float] = None
    method: str  # "pytorch", "vector", or "hybrid"

# --------- Fishing Spots Models ---------
class FishingSpotResult(BaseModel):
    id: str
    name: str
    latitude: float
    longitude: float
    bite_score: int
    status: str
    reasoning: str
    weather: Dict[str, float]

class FishingSpotsResponse(BaseModel):
    timestamp: str
    species: str
    total_spots: int
    returned: int
    spots: List[FishingSpotResult]

# --------- Safety & Recipes Models ---------
class Preferences(BaseModel):
    avoid_high_mercury: bool = False
    pregnant: bool = False
    catch_and_release: bool = False

class IdentifyRequest(BaseModel):
    species: str
    spot: Optional[str] = None
    preferences: Preferences = Preferences()

class RecipeCard(BaseModel):
    title: str
    steps: List[str]
    source_snippet: str

class SnippetResponse(BaseModel):
    text: str
    score: float
    metadata: Dict[str, Any]
    namespace: Optional[str] = None

class IdentifyResponse(BaseModel):
    species: str
    spot: Optional[str]
    edibility_label: str
    safety_summary: List[str]
    recipes: List[RecipeCard]
    community_alerts: List[str]
    evidence: Dict[str, List[SnippetResponse]]

# ============================================================================
# LIFESPAN & INITIALIZATION
# ============================================================================

def create_pytorch_model(num_classes):
    """Create ResNet50 model (same architecture as training)"""
    model = models.resnet50(weights=None)
    num_features = model.fc.in_features
    model.fc = nn.Linear(num_features, num_classes)
    return model

def load_fishing_spots_from_geojson():
    """Load GeoJSON fishing spots data"""
    global fishing_spots, SCORE_MIN, SCORE_MAX
    try:
        if not GEOJSON_PATH.exists():
            print(f"⚠️ GeoJSON file not found at {GEOJSON_PATH}")
            print("   Fishing spots feature will be disabled")
            return
        
        with open(GEOJSON_PATH, "r") as f:
            data = json.load(f)
            fishing_spots = data.get("features", [])
        
        scores = [
            f["properties"].get("potential_score", 0) 
            for f in fishing_spots 
            if f["properties"].get("potential_score") is not None and f["properties"].get("potential_score") > 0
        ]
        if scores:
            SCORE_MIN = min(scores)
            SCORE_MAX = max(scores)
        
        print(f"✅ Loaded {len(fishing_spots)} fishing spots from GeoJSON")
        print(f"   Score range: {SCORE_MIN:.2f} to {SCORE_MAX:.2f}")
    except Exception as e:
        print(f"❌ Failed to load fishing spots: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    global pytorch_model, label_encoder, clip_model
    
    # ===== STARTUP =====
    print("\n" + "="*70)
    print("🚀 Starting GoFish Unified API...")
    print("="*70)
    
    # Load PyTorch model
    print("\n📦 Loading PyTorch Fish Classifier...")
    try:
        if MODEL_PATH.exists():
            with open(LABEL_ENCODER_PATH, 'rb') as f:
                label_encoder = pickle.load(f)
            
            num_classes = len(label_encoder.classes_)
            pytorch_model = create_pytorch_model(num_classes)
            
            checkpoint = torch.load(MODEL_PATH, map_location=device)
            pytorch_model.load_state_dict(checkpoint['model_state_dict'])
            pytorch_model.to(device)
            pytorch_model.eval()
            
            print(f"✅ PyTorch model loaded!")
            print(f"   Classes: {num_classes}, Accuracy: {checkpoint.get('val_acc', 'N/A'):.2f}%")
        else:
            print(f"⚠️ Model not found at {MODEL_PATH} (PyTorch classification will be disabled)")
    except Exception as e:
        print(f"⚠️ PyTorch model loading failed: {e}")
    
    # Load CLIP model
    print("\n📦 Loading CLIP Model for Vector Embeddings...")
    try:
        clip_model = SentenceTransformer(CLIP_MODEL_NAME)
        print(f"✅ CLIP model loaded! (Dimensions: {EMBEDDING_DIMENSIONS})")
    except Exception as e:
        print(f"⚠️ CLIP loading failed: {e}")
    
    # Load Fishing Spots data
    print("\n📦 Loading Fishing Spots Data...")
    load_fishing_spots_from_geojson()
    
    # Connect to MongoDB
    print("\n📦 Connecting to MongoDB...")
    if not MONGO_URL:
        print("⚠️ No MONGO_URL in .env - database features disabled")
    else:
        try:
            app.mongodb_client = AsyncIOMotorClient(MONGO_URL)
            app.mongodb = app.mongodb_client.get_database(DB_NAME)
            await app.mongodb.command("ping")
            print("✅ Connected to MongoDB Atlas!")
            
            try:
                ref_count = await app.mongodb[REFERENCE_COLLECTION].count_documents({})
                catch_count = await app.mongodb[CATCHES_COLLECTION].count_documents({})
                print(f"   Reference fish: {ref_count}, Catches: {catch_count}")
            except:
                pass
        except Exception as e:
            print(f"❌ MongoDB connection failed: {e}")
    
    print("\n" + "="*70)
    print("✅ GoFish API Ready!")
    print("="*70 + "\n")
    
    yield
    
    # ===== SHUTDOWN =====
    if hasattr(app, 'mongodb_client'):
        app.mongodb_client.close()
        print("🛑 Database closed.")
    print("🛑 Shutting down GoFish API...")

# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title="GoFish Unified API",
    description="Complete fishing application: Scanner + Spots + Safety",
    version="2.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://localhost:3001", 
        "http://localhost:5173", 
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# FISH SCANNER ENDPOINTS
# ============================================================================

def classify_with_pytorch(image: Image.Image) -> Optional[dict]:
    """Classify fish using PyTorch model"""
    global pytorch_model, label_encoder
    
    if pytorch_model is None or label_encoder is None:
        return None
    
    try:
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        image_tensor = transform(image).unsqueeze(0).to(device)
        
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
        print(f"❌ PyTorch error: {e}")
        return None

def encode_image_to_embedding(image: Image.Image) -> list:
    """Encode image to vector embedding"""
    global clip_model
    
    if clip_model is None:
        raise ValueError("CLIP model not loaded")
    
    try:
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        embedding = clip_model.encode(image, convert_to_numpy=True)
        return embedding.tolist()
    except Exception as e:
        print(f"❌ Encoding error: {e}")
        raise

async def search_similar_fish_vector(query_embedding: list, top_k: int = 5) -> Optional[list]:
    """Vector similarity search in MongoDB"""
    if not hasattr(app, 'mongodb') or clip_model is None:
        return None
    
    try:
        collection = app.mongodb[REFERENCE_COLLECTION]
        
        # Try vector search
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
                {"$project": {"species": 1, "score": {"$meta": "vectorSearchScore"}}}
            ]
            
            cursor = collection.aggregate(pipeline)
            results = await cursor.to_list(length=top_k)
            
            if results:
                return [{"species": r["species"], "score": float(r["score"])} for r in results]
        except:
            pass
        
        # Fallback: manual cosine similarity
        query_vec = np.array(query_embedding)
        all_fish = await collection.find({}).to_list(length=1000)
        
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
        
        matches.sort(key=lambda x: x["score"], reverse=True)
        return matches[:top_k] if matches else None
        
    except Exception as e:
        print(f"❌ Vector search error: {e}")
        return None

@app.post("/api/scan-fish", response_model=ScanFishResponse)
async def scan_fish(request: ScanFishRequest):
    """
    POST /api/scan-fish
    Scan a fish image: PyTorch classification + vector search refinement
    """
    try:
        # Decode image
        try:
            if ',' in request.image_base64:
                image_data = base64.b64decode(request.image_base64.split(',')[-1])
            else:
                image_data = base64.b64decode(request.image_base64)
            
            image = Image.open(io.BytesIO(image_data))
            if image.mode != 'RGB':
                image = image.convert('RGB')
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Image decode failed: {str(e)}")
        
        # PyTorch classification
        pytorch_result = classify_with_pytorch(image)
        
        # Vector search
        vector_result = None
        vector_confidence = None
        
        if clip_model is not None:
            try:
                query_embedding = encode_image_to_embedding(image)
                vector_matches = await search_similar_fish_vector(query_embedding, top_k=3)
                
                if vector_matches:
                    vector_result = vector_matches[0]
                    vector_confidence = vector_result["score"]
            except Exception as e:
                print(f"⚠️ Vector search skipped: {e}")
        
        # Combine results
        final_species = None
        final_confidence = 0.0
        method = "unknown"
        
        if pytorch_result and vector_result:
            pytorch_conf = pytorch_result["confidence"]
            vector_conf = vector_confidence
            
            if pytorch_result["species"] == vector_result["species"]:
                final_species = pytorch_result["species"]
                final_confidence = 0.7 * pytorch_conf + 0.3 * vector_conf
                method = "hybrid_agree"
            else:
                final_species = pytorch_result["species"]
                final_confidence = pytorch_conf * 0.8
                method = "hybrid_disagree"
        elif pytorch_result:
            final_species = pytorch_result["species"]
            final_confidence = pytorch_result["confidence"]
            method = "pytorch"
        elif vector_result:
            final_species = vector_result["species"]
            final_confidence = vector_confidence
            method = "vector"
        else:
            raise HTTPException(status_code=404, detail="No model available")
        
        # Save to database
        if hasattr(app, 'mongodb'):
            try:
                catch_doc = {
                    "species": final_species,
                    "confidence": final_confidence,
                    "pytorch_confidence": pytorch_result["confidence"] if pytorch_result else None,
                    "vector_confidence": vector_confidence,
                    "method": method,
                    "scanned_at": datetime.utcnow()
                }
                
                collection = app.mongodb[CATCHES_COLLECTION]
                await collection.insert_one(catch_doc)
                print(f"✅ Saved catch: {final_species} ({final_confidence:.1%}, {method})")
            except Exception as e:
                print(f"⚠️ Save failed: {e}")
        
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
        print(f"❌ Scan error: {e}")
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")

# ============================================================================
# FISHING SPOTS ENDPOINTS
# ============================================================================

def normalize_score(raw_score: float) -> float:
    """Normalize score to 0-100 using log scale"""
    if raw_score <= 0:
        return 0
    log_score = math.log(raw_score)
    log_min = math.log(SCORE_MIN)
    log_max = math.log(SCORE_MAX)
    if log_max == log_min:
        return 50
    return 100 * (log_score - log_min) / (log_max - log_min)

def species_matches_habitat(species: str, habitat_fe: str) -> tuple[float, str]:
    """Check if species matches habitat type"""
    if not habitat_fe:
        return 0.5, "Unknown habitat"
    
    habitat_lower = habitat_fe.lower()
    keywords = SPECIES_KEYWORDS.get(species, [])
    
    for kw in keywords:
        if kw in habitat_lower:
            return 1.5, f"Known {species} habitat"
    
    if any(term in habitat_lower for term in ["spawning", "nursery", "feeding", "rearing"]):
        return 1.0, "Favorable habitat type"
    
    return 0.5, "Generic habitat"

async def fetch_weather(lat: float, lon: float) -> dict:
    """Fetch weather from Open-Meteo API"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:  # Reduced timeout for faster response
            response = await client.get(
                OPEN_METEO_API,
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "current": "temperature_2m,pressure_msl,wind_speed_10m",
                    "timezone": "America/Toronto"
                }
            )
            if response.status_code == 200:
                current = response.json().get("current", {})
                return {
                    "temperature": current.get("temperature_2m", 10),
                    "pressure": current.get("pressure_msl", 1013),
                    "wind_speed": current.get("wind_speed_10m", 10),
                }
    except Exception as e:
        print(f"⚠️ Weather error: {e}")
    return {"temperature": 10, "pressure": 1013, "wind_speed": 10}

def calculate_score(species: str, base_score: float, habitat_multiplier: float, weather: dict, hour: int) -> dict:
    """Calculate species-specific bite score"""
    reasons = []
    
    is_low_light = hour < 7 or hour > 19
    temp = weather["temperature"]
    pressure = weather["pressure"]
    wind = weather["wind_speed"]
    
    # Habitat score
    if habitat_multiplier >= 1.5:
        habitat_score = base_score
        reasons.append(f"Prime {species} habitat")
    elif habitat_multiplier >= 1.0:
        habitat_score = base_score * 0.7
        reasons.append("Favorable habitat")
    else:
        habitat_score = base_score * 0.4
        reasons.append("Unknown habitat")
    
    # Weather score
    weather_score = 50
    
    if species == "walleye":
        if pressure < 1010:
            weather_score += 20
            reasons.append("Falling pressure")
        if 10 <= temp <= 18:
            weather_score += 20
            reasons.append("Optimal temp")
        elif temp < 5 or temp > 22:
            weather_score -= 20
    elif species == "trout":
        if 8 <= temp <= 16:
            weather_score += 30
            reasons.append("Ideal cool water")
        elif temp > 20:
            weather_score -= 30
        if wind < 10:
            weather_score += 10
    elif species == "bass":
        if temp > 20:
            weather_score += 30
            reasons.append("Prime warm water")
        elif temp < 12:
            weather_score -= 20
    elif species == "pike":
        if 15 <= temp <= 22:
            weather_score += 25
            reasons.append("Optimal pike temp")
    elif species == "perch":
        if 12 <= temp <= 20:
            weather_score += 20
        if pressure > 1015:
            weather_score += 15
    
    weather_score = max(0, min(100, weather_score))
    
    # Time of day score
    time_score = 50
    
    if species in ["walleye", "pike"]:
        if is_low_light:
            time_score = 90
            reasons.append("Prime feeding time")
        elif 7 <= hour <= 9 or 17 <= hour <= 19:
            time_score = 75
        else:
            time_score = 40
    elif species == "bass":
        if is_low_light:
            time_score = 80
            reasons.append("Dawn/dusk activity")
        elif 10 <= hour <= 14:
            time_score = 50
        else:
            time_score = 60
    elif species == "trout":
        if 6 <= hour <= 10:
            time_score = 85
            reasons.append("Morning feed")
        elif 16 <= hour <= 20:
            time_score = 80
        elif 11 <= hour <= 15:
            time_score = 40
    else:
        time_score = 60
    
    # Weighted final score
    final_score = (habitat_score * 0.50) + (weather_score * 0.30) + (time_score * 0.20)
    final_score = max(0, min(100, final_score))
    
    if final_score >= 75:
        status = "Great"
    elif final_score >= 55:
        status = "Good"
    elif final_score >= 35:
        status = "Fair"
    else:
        status = "Poor"
    
    return {
        "score": int(final_score),
        "status": status,
        "reasoning": "; ".join(reasons) if reasons else "Standard conditions"
    }

@app.get("/api/fishing-spots", response_model=FishingSpotsResponse)
async def get_fishing_spots(
    species: str = "walleye",
    limit: int = Query(default=20, le=50),  # Reduced default to avoid timeouts
    min_lat: Optional[float] = None,
    max_lat: Optional[float] = None,
    min_lon: Optional[float] = None,
    max_lon: Optional[float] = None,
):
    """
    GET /api/fishing-spots
    Get top fishing spots for a species with bite scores
    """
    if not fishing_spots:
        raise HTTPException(status_code=503, detail="Fishing spots data not loaded")
    
    current_hour = datetime.now().hour
    
    # Filter and calculate scores
    filtered = []
    for spot in fishing_spots:
        props = spot.get("properties", {})
        lat = props.get("centroid_lat_wgs84")
        lon = props.get("centroid_lon_wgs84")
        potential = props.get("potential_score_capped") or props.get("potential_score") or 0
        habitat_fe = props.get("HABITAT_FE", "")
        
        if lat is None or lon is None:
            continue
        
        # Bounding box filter
        if min_lat and lat < min_lat:
            continue
        if max_lat and lat > max_lat:
            continue
        if min_lon and lon < min_lon:
            continue
        if max_lon and lon > max_lon:
            continue
        
        habitat_mult, habitat_reason = species_matches_habitat(species, habitat_fe)
        base_score = normalize_score(potential)
        
        filtered.append({
            "id": props.get("UNIQID", ""),
            "name": props.get("LAKE_NAME", "Unknown"),
            "latitude": lat,
            "longitude": lon,
            "potential_score": potential,
            "base_score": round(base_score, 1),
            "habitat_type": habitat_fe,
            "habitat_desc": props.get("HABITAT_DE", ""),
            "habitat_match": habitat_mult,
            "habitat_reason": habitat_reason,
            "area": props.get("AREA", 0),
        })
    
    # Sort by habitat match, then base score
    filtered.sort(key=lambda x: (x["habitat_match"], x["base_score"]), reverse=True)
    top_spots = filtered[:limit]
    
    # Fetch weather and calculate bite scores (concurrent for better performance)
    async def process_spot(spot):
        try:
            weather = await fetch_weather(spot["latitude"], spot["longitude"])
        except:
            # Fallback weather data if API fails
            weather = {"temperature": 10, "pressure": 1013, "wind_speed": 10}
        
        bite = calculate_score(
            species, 
            spot["base_score"], 
            spot["habitat_match"], 
            weather, 
            current_hour
        )
        return FishingSpotResult(
            id=spot["id"],
            name=spot["name"],
            latitude=spot["latitude"],
            longitude=spot["longitude"],
            bite_score=bite["score"],
            status=bite["status"],
            reasoning=f"{spot['habitat_reason']}; {bite['reasoning']}",
            weather=weather
        )
    
    # Process spots concurrently (limited to avoid too many API calls)
    max_concurrent = min(len(top_spots), 20)  # Limit concurrent requests
    results = await asyncio.gather(*[process_spot(spot) for spot in top_spots[:max_concurrent]], return_exceptions=True)
    # Filter out any exceptions
    results = [r for r in results if isinstance(r, FishingSpotResult)]
    
    # Final sort by bite score
    results.sort(key=lambda x: x.bite_score, reverse=True)
    
    return FishingSpotsResponse(
        timestamp=datetime.now(timezone.utc).isoformat(),
        species=species,
        total_spots=len(fishing_spots),
        returned=len(results),
        spots=results
    )

@app.get("/api/best-spot")
async def get_best_spot(species: str = "walleye"):
    """
    GET /api/best-spot
    Get single best spot for a species
    """
    data = await get_fishing_spots(species=species, limit=1)
    if data.spots:
        return {"best": data.spots[0], "timestamp": data.timestamp}
    return {"best": None, "timestamp": data.timestamp}

@app.get("/api/species")
async def get_supported_species():
    """
    GET /api/species
    Get list of supported fish species
    """
    return {
        "species": list(SPECIES_KEYWORDS.keys()),
        "descriptions": {
            "walleye": "Best in low light, falling pressure",
            "bass": "Active in warm water, dawn/dusk",
            "trout": "Prefer cool water (8-16°C)",
            "pike": "Ambush predators, active in moderate temps",
            "perch": "Stable pressure, moderate temps",
        }
    }

# ============================================================================
# HEALTH ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint with status"""
    ref_count = 0
    catch_count = 0
    if hasattr(app, 'mongodb'):
        try:
            ref_count = await app.mongodb[REFERENCE_COLLECTION].count_documents({})
            catch_count = await app.mongodb[CATCHES_COLLECTION].count_documents({})
        except:
            pass
    
    return {
        "message": "GoFish Unified API",
        "version": "2.0.0",
        "status": "online",
        "modules": {
            "fish_scanner": pytorch_model is not None or clip_model is not None,
            "fishing_spots": len(fishing_spots) > 0,
            "safety_recipes": True,
            "database": hasattr(app, 'mongodb')
        },
        "database": {
            "connected": hasattr(app, 'mongodb'),
            "reference_fish": ref_count,
            "catches_recorded": catch_count
        },
        "device": str(device)
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    ref_count = 0
    catch_count = 0
    if hasattr(app, 'mongodb'):
        try:
            ref_count = await app.mongodb[REFERENCE_COLLECTION].count_documents({})
            catch_count = await app.mongodb[CATCHES_COLLECTION].count_documents({})
        except:
            pass
    
    return {
        "status": "healthy",
        "version": "2.0.0",
        "mongodb_connected": hasattr(app, 'mongodb'),
        "pytorch_model_loaded": pytorch_model is not None,
        "clip_model_loaded": clip_model is not None,
        "reference_fish_count": ref_count,
        "catches_count": catch_count,
        "fishing_spots_loaded": len(fishing_spots)
    }

# ============================================================================
# SAFETY & RECIPES ENDPOINTS (Placeholder)
# ============================================================================
# These would integrate with Moorcheh when API key is configured
# For now, provide basic data structure

@app.post("/api/brain/advise", response_model=IdentifyResponse)
async def brain_advise(request: IdentifyRequest):
    """
    POST /api/brain/advise
    Get safety info, recipes, and community alerts for a caught fish
    """
    species_lower = request.species.lower()
    
    # Fish-specific knowledge base
    fish_data = {
        "bass": {
            "edibility": "Safe to eat",
            "facts": [
                "Bass is a popular sport fish and excellent table fare",
                "Contains omega-3 fatty acids beneficial for heart health",
                "Firm, white flesh with mild flavor",
                "Best caught during spring and fall seasons"
            ],
            "safety": [
                "Generally safe to consume from clean waters",
                "Check local advisories for mercury content",
                "Smaller bass (< 14 inches) have lower mercury levels",
                "Clean and cook thoroughly to 145°F internal temperature"
            ],
            "recipes": [
                {
                    "title": "Pan-Fried Bass",
                    "steps": [
                        "Clean and fillet the bass, removing skin",
                        "Dredge fillets in flour mixed with salt and pepper",
                        "Heat butter and oil in skillet over medium-high heat",
                        "Cook 3-4 minutes per side until golden and flaky",
                        "Serve with lemon wedges"
                    ],
                    "source": "Traditional preparation"
                },
                {
                    "title": "Grilled Bass with Herbs",
                    "steps": [
                        "Season fillets with olive oil, garlic, and fresh herbs",
                        "Preheat grill to medium-high",
                        "Grill 4-5 minutes per side with lid closed",
                        "Fish is done when it flakes easily with a fork"
                    ],
                    "source": "Grilling method"
                }
            ]
        },
        "walleye": {
            "edibility": "Safe to eat - Excellent",
            "facts": [
                "Walleye is considered one of the best-tasting freshwater fish",
                "Native to North American lakes and rivers",
                "Named for their distinctive glassy, opaque eyes",
                "Most active during dawn and dusk"
            ],
            "safety": [
                "Very safe to eat - low mercury content",
                "Check local size and bag limits",
                "Best from clean, cold water sources",
                "Handle carefully - sharp dorsal fins"
            ],
            "recipes": [
                {
                    "title": "Beer-Battered Walleye",
                    "steps": [
                        "Mix flour, beer, and seasonings for batter",
                        "Dip walleye fillets in batter",
                        "Deep fry at 375°F for 3-4 minutes until golden",
                        "Drain on paper towels and serve immediately"
                    ],
                    "source": "Classic preparation"
                }
            ]
        },
        "trout": {
            "edibility": "Safe to eat",
            "facts": [
                "Trout prefer cold, oxygen-rich water",
                "High in protein and omega-3 fatty acids",
                "Delicate, pink to orange flesh",
                "Popular fly-fishing target"
            ],
            "safety": [
                "Safe when caught from clean, cold streams",
                "Check for fishing regulations and seasons",
                "Wild trout generally safer than farmed",
                "Cook to 145°F internal temperature"
            ],
            "recipes": [
                {
                    "title": "Pan-Seared Trout",
                    "steps": [
                        "Season whole trout with salt, pepper, and lemon",
                        "Heat butter in pan over medium-high heat",
                        "Cook 4-5 minutes per side until skin is crispy",
                        "Serve with fresh herbs and lemon"
                    ],
                    "source": "Simple preparation"
                }
            ]
        },
        "pike": {
            "edibility": "Safe to eat - with caution",
            "facts": [
                "Pike have many small Y-bones that require special filleting",
                "Aggressive predator fish",
                "Firm, white flesh when properly prepared",
                "Can grow very large"
            ],
            "safety": [
                "Edible but requires careful preparation",
                "Remove Y-bones completely before cooking",
                "Check size regulations - larger pike may have higher mercury",
                "Best prepared by experienced fish cleaners"
            ],
            "recipes": [
                {
                    "title": "Baked Pike Fillets",
                    "steps": [
                        "Carefully remove all Y-bones from fillets",
                        "Season with herbs, lemon, and butter",
                        "Bake at 400°F for 12-15 minutes",
                        "Fish is done when flaky and opaque"
                    ],
                    "source": "Baking method"
                }
            ]
        }
    }
    
    # Get species data or use defaults
    data = fish_data.get(species_lower, {
        "edibility": "Likely safe to eat - verify species",
        "facts": [
            f"{request.species} is a freshwater fish species",
            "Check with local fish and wildlife department for regulations",
            "Ensure proper identification before consumption"
        ],
        "safety": [
            "Always verify fish species before eating",
            "Check local fishing regulations and advisories",
            "Cook thoroughly to 145°F internal temperature",
            "Store on ice immediately after catching"
        ],
        "recipes": [
            {
                "title": f"Pan-Seared {request.species}",
                "steps": [
                    "Clean and fillet the fish",
                    "Season with salt, pepper, and lemon",
                    "Heat pan with olive oil to medium-high",
                    "Cook 4-5 minutes per side until golden"
                ],
                "source": "General preparation method"
            }
        ]
    })
    
    recipe_cards = [
        RecipeCard(
            title=recipe["title"],
            steps=recipe["steps"],
            source_snippet=recipe.get("source", "Traditional method")
        )
        for recipe in data["recipes"]
    ]
    
    return IdentifyResponse(
        species=request.species,
        spot=request.spot,
        edibility_label=data["edibility"],
        safety_summary=data["safety"],
        recipes=recipe_cards,
        community_alerts=[
            "Always check local fishing regulations",
            "Be aware of seasonal restrictions",
            "Follow catch and size limits"
        ],
        evidence={
            "safety": [{"text": s, "score": 1.0, "metadata": {}} for s in data["safety"]],
            "recipes": [{"text": r["title"], "score": 1.0, "metadata": {}} for r in data["recipes"]],
            "community": []
        }
    )

# ============================================================================
# Run
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
