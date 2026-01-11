"""
Fish Classification Model Training Script

This script:
1. Loads fish images from Fish_Data/raw_images/
2. Extracts species from filenames
3. Trains a PyTorch CNN using transfer learning (ResNet50)
4. Saves the trained model for use in the app

Usage:
    python train_fish_model.py
"""

import os
import sys
import re
from pathlib import Path
from collections import Counter
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader, random_split
from torchvision import transforms, models
from PIL import Image
from sklearn.preprocessing import LabelEncoder
import numpy as np

# Configuration
DATA_DIR = "Fish_Data/raw_images"
MODEL_SAVE_PATH = "models/fish_classifier.pth"
BATCH_SIZE = 32
EPOCHS = 10
LEARNING_RATE = 0.001
IMG_SIZE = 224
TEST_SPLIT = 0.2
VAL_SPLIT = 0.1

# Device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

def extract_species_from_filename(filename):
    """Extract species name from filename (same logic as seed_db.py)"""
    name_without_ext = Path(filename).stem
    name_clean = re.sub(r'[_-]\d+$', '', name_without_ext)
    
    if '_' in name_clean and name_clean[0].islower():
        parts = name_clean.split('_')
        if len(parts) >= 2:
            genus = parts[0].capitalize()
            species = parts[1].capitalize()
            return f"{genus} {species}"
        else:
            return parts[0].capitalize()
    
    if '_' in name_clean:
        parts = name_clean.split('_')
        species = parts[0].strip()
    elif '-' in name_clean:
        parts = name_clean.split('-')
        species = parts[0].strip()
    else:
        species = name_clean
    
    species = re.sub(r'\d+$', '', species).strip()
    if species:
        species = species[0].upper() + species[1:].lower() if len(species) > 1 else species.upper()
    
    return species if species else "Unknown"

class FishDataset(Dataset):
    """PyTorch Dataset for fish images"""
    def __init__(self, image_paths, labels, transform=None):
        self.image_paths = image_paths
        self.labels = labels
        self.transform = transform
    
    def __len__(self):
        return len(self.image_paths)
    
    def __getitem__(self, idx):
        image_path = self.image_paths[idx]
        label = self.labels[idx]
        
        try:
            image = Image.open(image_path)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            if self.transform:
                image = self.transform(image)
            
            return image, label
        except Exception as e:
            print(f"Error loading {image_path}: {e}")
            # Return a blank image if there's an error
            blank = Image.new('RGB', (IMG_SIZE, IMG_SIZE), color='black')
            if self.transform:
                blank = self.transform(blank)
            return blank, label

def load_fish_data(data_dir):
    """Load all fish images and extract species labels"""
    print(f"📁 Loading fish data from: {data_dir}")
    
    data_path = Path(data_dir)
    if not data_path.exists():
        raise ValueError(f"Data directory {data_dir} does not exist!")
    
    image_files = []
    species_labels = []
    
    # Get all image files
    for ext in ['.jpg', '.jpeg', '.png']:
        image_files.extend(list(data_path.glob(f'*{ext}')))
    
    print(f"   Found {len(image_files)} images")
    
    # Extract species from filenames
    for img_file in image_files:
        species = extract_species_from_filename(img_file.name)
        species_labels.append(species)
    
    # Filter out species with too few samples (need at least 2 for train/val split)
    species_counts = Counter(species_labels)
    min_samples = 3
    
    filtered_files = []
    filtered_labels = []
    for img_file, label in zip(image_files, species_labels):
        if species_counts[label] >= min_samples:
            filtered_files.append(img_file)
            filtered_labels.append(label)
    
    print(f"   After filtering (min {min_samples} samples per species): {len(filtered_files)} images")
    print(f"   Number of species: {len(set(filtered_labels))}")
    
    return filtered_files, filtered_labels

def create_data_loaders(image_files, labels, batch_size, test_split, val_split):
    """Create train/val/test data loaders"""
    
    # Encode labels to integers
    label_encoder = LabelEncoder()
    encoded_labels = label_encoder.fit_transform(labels)
    
    print(f"   Encoded {len(label_encoder.classes_)} unique species")
    
    # Data transforms
    train_transform = transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(10),
        transforms.ColorJitter(brightness=0.2, contrast=0.2),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    val_test_transform = transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    # Split dataset
    dataset = list(zip(image_files, encoded_labels))
    total_size = len(dataset)
    
    test_size = int(total_size * test_split)
    val_size = int(total_size * val_split)
    train_size = total_size - test_size - val_size
    
    train_data, val_data, test_data = random_split(
        dataset, 
        [train_size, val_size, test_size],
        generator=torch.Generator().manual_seed(42)
    )
    
    # Create datasets
    train_dataset = FishDataset(
        [item[0] for item in train_data],
        [item[1] for item in train_data],
        transform=train_transform
    )
    
    val_dataset = FishDataset(
        [item[0] for item in val_data],
        [item[1] for item in val_data],
        transform=val_test_transform
    )
    
    test_dataset = FishDataset(
        [item[0] for item in test_data],
        [item[1] for item in test_data],
        transform=val_test_transform
    )
    
    # Create data loaders
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=0)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False, num_workers=0)
    
    return train_loader, val_loader, test_loader, label_encoder

def create_model(num_classes):
    """Create ResNet50 model with transfer learning"""
    # Load pre-trained ResNet50
    model = models.resnet50(weights='IMAGENET1K_V2')
    
    # Freeze early layers
    for param in model.parameters():
        param.requires_grad = False
    
    # Unfreeze last few layers
    for param in model.layer4.parameters():
        param.requires_grad = True
    for param in model.fc.parameters():
        param.requires_grad = True
    
    # Replace final layer for our number of classes
    num_features = model.fc.in_features
    model.fc = nn.Linear(num_features, num_classes)
    
    return model

def train_model(model, train_loader, val_loader, num_epochs, learning_rate, device):
    """Train the model"""
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(filter(lambda p: p.requires_grad, model.parameters()), lr=learning_rate)
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=5, gamma=0.1)
    
    best_val_acc = 0.0
    model.to(device)
    
    for epoch in range(num_epochs):
        # Training phase
        model.train()
        train_loss = 0.0
        train_correct = 0
        train_total = 0
        
        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item()
            _, predicted = torch.max(outputs.data, 1)
            train_total += labels.size(0)
            train_correct += (predicted == labels).sum().item()
        
        train_acc = 100 * train_correct / train_total
        
        # Validation phase
        model.eval()
        val_loss = 0.0
        val_correct = 0
        val_total = 0
        
        with torch.no_grad():
            for images, labels in val_loader:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                loss = criterion(outputs, labels)
                
                val_loss += loss.item()
                _, predicted = torch.max(outputs.data, 1)
                val_total += labels.size(0)
                val_correct += (predicted == labels).sum().item()
        
        val_acc = 100 * val_correct / val_total
        scheduler.step()
        
        print(f"Epoch {epoch+1}/{num_epochs}:")
        print(f"  Train Loss: {train_loss/len(train_loader):.4f}, Train Acc: {train_acc:.2f}%")
        print(f"  Val Loss: {val_loss/len(val_loader):.4f}, Val Acc: {val_acc:.2f}%")
        
        # Save best model
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save({
                'model_state_dict': model.state_dict(),
                'val_acc': val_acc,
                'epoch': epoch
            }, MODEL_SAVE_PATH)
            print(f"  ✅ Saved best model (val acc: {val_acc:.2f}%)")
        print()
    
    return model

def main():
    print("🐟 Fish Classification Model Training")
    print("=" * 50)
    
    # Create models directory
    os.makedirs("./models", exist_ok=True)
    
    # Load data
    image_files, species_labels = load_fish_data(DATA_DIR)
    
    if len(image_files) == 0:
        print("❌ No images found!")
        sys.exit(1)
    
    # Create data loaders
    print("\n📊 Creating data loaders...")
    train_loader, val_loader, test_loader, label_encoder = create_data_loaders(
        image_files, species_labels, BATCH_SIZE, TEST_SPLIT, VAL_SPLIT
    )
    
    # Save label encoder for inference
    import pickle
    with open("./models/label_encoder.pkl", "wb") as f:
        pickle.dump(label_encoder, f)
    print(f"✅ Saved label encoder with {len(label_encoder.classes_)} classes")
    
    # Create model
    num_classes = len(label_encoder.classes_)
    print(f"\n🏗️ Creating ResNet50 model for {num_classes} classes...")
    model = create_model(num_classes)
    
    # Train model
    print(f"\n🚀 Starting training for {EPOCHS} epochs...")
    print(f"   Batch size: {BATCH_SIZE}")
    print(f"   Learning rate: {LEARNING_RATE}")
    print(f"   Device: {device}")
    print()
    
    trained_model = train_model(model, train_loader, val_loader, EPOCHS, LEARNING_RATE, device)
    
    # Test model
    print("\n📊 Testing on test set...")
    trained_model.eval()
    test_correct = 0
    test_total = 0
    
    with torch.no_grad():
        for images, labels in test_loader:
            images, labels = images.to(device), labels.to(device)
            outputs = trained_model(images)
            _, predicted = torch.max(outputs.data, 1)
            test_total += labels.size(0)
            test_correct += (predicted == labels).sum().item()
    
    test_acc = 100 * test_correct / test_total
    print(f"✅ Test Accuracy: {test_acc:.2f}%")
    
    print(f"\n✅ Training complete! Model saved to: {MODEL_SAVE_PATH}")
    print("\n📋 Next steps:")
    print("   1. The model is ready to use in main.py")
    print("   2. Restart your FastAPI server to load the model")
    print("   3. Use the model for classification, then refine with vector search")

if __name__ == "__main__":
    main()
