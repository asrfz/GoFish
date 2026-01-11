"""
Seed Database Script - Populate MongoDB with Fish Embeddings

This script:
1. Loads the CLIP model (clip-ViT-B-32)
2. Walks through fish image folders: ./fish_images/{species_name}/*.jpg
3. Generates embeddings for each image
4. Saves them to MongoDB collection 'fish_reference'

Usage:
    python seed_db.py

Requirements:
    - Folder structure: ./fish_images/Bass/*.jpg, ./fish_images/Trout/*.jpg, etc.
    - MongoDB connection string in .env as MONGO_URL
    - sentence-transformers installed
"""

import os
import sys
import re
from pathlib import Path
from PIL import Image
from dotenv import load_dotenv
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
import numpy as np

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

load_dotenv()

# Configuration - Use raw_images folder with species in filenames
FISH_IMAGES_DIR = "Fish_Data/raw_images"  # Direct path to raw images

MONGO_URL = os.getenv("MONGO_URL")
DB_NAME = "castnet"
COLLECTION_NAME = "fish_reference"

# CLIP model configuration
MODEL_NAME = "clip-ViT-B-32"
EMBEDDING_DIMENSIONS = 512  # CLIP ViT-B-32 uses 512 dimensions

def load_model():
    """Load the CLIP model (this is slow, so we do it once)"""
    print(f"⏳ Loading CLIP model: {MODEL_NAME}...")
    print("   (This may take a minute on first run - model will be downloaded)")
    try:
        model = SentenceTransformer(MODEL_NAME)
        print(f"✅ Model loaded successfully!")
        return model
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        sys.exit(1)

def extract_species_from_filename(filename):
    """
    Extract species name from filename.
    Handles patterns like:
    - acanthaluteres_brownii_1.jpg -> "Acanthaluteres Brownii"
    - genus_species_number.jpg -> "Genus Species"
    - A73EGS-P_1.jpg -> "A73EGS-P" (code-based)
    """
    # Remove file extension
    name_without_ext = Path(filename).stem
    
    # Remove trailing number pattern (_123 or -123)
    name_clean = re.sub(r'[_-]\d+$', '', name_without_ext)
    
    # Pattern 1: Scientific name format (genus_species)
    if '_' in name_clean and name_clean[0].islower():
        # Scientific name format: genus_species
        parts = name_clean.split('_')
        if len(parts) >= 2:
            # Take genus and species, format as "Genus Species"
            genus = parts[0].capitalize()
            species = parts[1].capitalize()
            return f"{genus} {species}"
        else:
            # Just genus
            return parts[0].capitalize()
    
    # Pattern 2: Code-based or single identifier (e.g., A73EGS-P, Bass_001)
    if '_' in name_clean:
        parts = name_clean.split('_')
        species = parts[0].strip()
    elif '-' in name_clean:
        # Take part before last hyphen if it looks like a number
        parts = name_clean.split('-')
        if parts and parts[-1].isdigit():
            species = '-'.join(parts[:-1])
        else:
            species = name_clean
    else:
        species = name_clean
    
    # Clean up: remove trailing numbers
    species = re.sub(r'\d+$', '', species).strip()
    
    # Format: capitalize first letter, rest lowercase (for codes, preserve format)
    if species:
        # If it's all uppercase or mixed case code, preserve it
        if species.isupper() or re.match(r'^[A-Z0-9-]+$', species):
            return species
        # Otherwise capitalize properly
        species = species[0].upper() + species[1:].lower() if len(species) > 1 else species.capitalize()
    
    return species if species else "Unknown"

def get_image_files(root_dir):
    """Walk through fish_images directory and collect all images"""
    image_files = []
    root_path = Path(root_dir)
    
    if not root_path.exists():
        print(f"❌ Error: Directory '{root_dir}' does not exist!")
        sys.exit(1)
    
    print(f"   Using directory: {root_dir}")
    print("   Extracting species names from filenames")
    
    # Supported image extensions
    image_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}
    
    # Check if we have species subfolders
    subdirs = [d for d in root_path.iterdir() if d.is_dir()]
    has_species_folders = any(d.is_dir() and any(f.suffix.lower() in image_extensions for f in d.iterdir() if f.is_file()) for d in subdirs)
    
    if has_species_folders:
        # Standard structure: root_dir/{species_name}/*.jpg
        print("   Detected species folder structure")
        for species_folder in root_path.iterdir():
            if not species_folder.is_dir():
                continue
            
            species_name = species_folder.name
            
            # Find all images in this species folder
            for image_file in species_folder.iterdir():
                if image_file.is_file() and image_file.suffix.lower() in image_extensions:
                    image_files.append((species_name, image_file))
    else:
        # Flat structure: extract species from filename
        print("   Detected flat folder structure - parsing species from filenames")
        
        for image_file in root_path.iterdir():
            if image_file.is_file() and image_file.suffix.lower() in image_extensions:
                species_name = extract_species_from_filename(image_file.name)
                image_files.append((species_name, image_file))
    
    return image_files

def encode_image(model, image_path):
    """Convert an image to an embedding vector"""
    try:
        # Load and preprocess image
        image = Image.open(image_path)
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Encode image to embedding
        embedding = model.encode(image, convert_to_numpy=True)
        
        # Convert numpy array to list (required for MongoDB)
        return embedding.tolist()
    except Exception as e:
        print(f"   ⚠️ Error encoding {image_path}: {e}")
        return None

def seed_database(model, image_files, collection):
    """Process all images and insert into MongoDB"""
    print(f"\n🔄 Processing {len(image_files)} images...")
    
    inserted_count = 0
    skipped_count = 0
    
    for idx, (species_name, image_path) in enumerate(image_files, 1):
        print(f"   [{idx}/{len(image_files)}] Processing {species_name}/{image_path.name}...", end="")
        
        # Generate embedding
        embedding = encode_image(model, image_path)
        
        if embedding is None:
            skipped_count += 1
            print(" ❌ Skipped")
            continue
        
        # Create document
        document = {
            "species": species_name,
            "embedding": embedding,
            "filename": image_path.name,
            "filepath": str(image_path)
        }
        
        # Insert into MongoDB
        try:
            collection.insert_one(document)
            inserted_count += 1
            print(f" ✅ Inserted")
        except Exception as e:
            skipped_count += 1
            print(f" ❌ Failed: {e}")
    
    print(f"\n✅ Seeding complete!")
    print(f"   Inserted: {inserted_count}")
    print(f"   Skipped: {skipped_count}")
    print(f"   Total in collection: {collection.count_documents({})}")

def main():
    print("Fish Database Seeder")
    print("=" * 50)
    
    # Check MongoDB connection
    if not MONGO_URL:
        print("❌ Error: MONGO_URL not found in .env file")
        sys.exit(1)
    
    print(f"⏳ Connecting to MongoDB...")
    try:
        client = MongoClient(MONGO_URL)
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]
        
        # Test connection
        client.admin.command('ping')
        print("✅ Connected to MongoDB!")
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        sys.exit(1)
    
    # Load model
    model = load_model()
    
    # Get all image files
    print(f"\n📁 Scanning for images...")
    print(f"   Found data directory: {FISH_IMAGES_DIR}")
    image_files = get_image_files(FISH_IMAGES_DIR)
    
    if not image_files:
        print(f"❌ No images found in {FISH_IMAGES_DIR}")
        print(f"   Expected structure: {FISH_IMAGES_DIR}/{{species_name}}/*.jpg")
        sys.exit(1)
    
    print(f"✅ Found {len(image_files)} images across {len(set(s for s, _ in image_files))} species")
    
    # Show species breakdown
    species_counts = {}
    for species, _ in image_files:
        species_counts[species] = species_counts.get(species, 0) + 1
    print(f"\n   Species breakdown:")
    for species, count in sorted(species_counts.items()):
        print(f"     - {species}: {count} images")
    
    # Confirm before proceeding
    response = input(f"\n❓ Proceed with seeding? (y/n): ").strip().lower()
    if response != 'y':
        print("❌ Cancelled")
        sys.exit(0)
    
    # Seed database
    seed_database(model, image_files, collection)
    
    print("\n📋 Next Steps:")
    print("   1. Go to MongoDB Atlas UI")
    print("   2. Navigate to: Search -> Vector Search -> Create Index")
    print("   3. Select collection: fish_reference")
    print("   4. Use this configuration:")
    print()
    print('   {')
    print('     "fields": [')
    print('       {')
    print('         "type": "vector",')
    print(f'         "path": "embedding",')
    print(f'         "numDimensions": {EMBEDDING_DIMENSIONS},')
    print('         "similarity": "cosine"')
    print('       }')
    print('     ]')
    print('   }')
    print()

if __name__ == "__main__":
    main()
