# Quick Start Guide - GoFish

## Project Overview

GoFish helps anglers find the optimal fishing location based on:
- **Fish preferences** (what species they want to catch)
- **Location** (where they want to fish)
- **Weather data** (METAR, TAFS, and conditions)
- **Regional fish availability** (what can be found where)
- **Camera scanning** (identify caught fish by type and weight)
- **Community info** (tournaments, events, active fishing spots)

## Step 1: Install Dependencies

### Backend:
```bash
pip install -r requirements.txt
```

### Frontend:
```bash
npm install
```

## Step 2: Set Up Environment Variables

Create a `.env` file in the root directory:
```
MONGO_URL=your_mongodb_connection_string
```

## Step 3: Train the Fish Classification Model (Optional)

If you have new fish image data in `Fish_Data/raw_images/`, train the model:

```bash
python train_fish_model.py
```

This creates `models/fish_classifier.pth` for camera scanning.

## Step 4: Seed the Database

Populate MongoDB with fish reference data:

```bash
python seed_db.py
```

## Step 5: Run the Application

**Terminal 1 - Backend (API Server):**
```bash
uvicorn main:app --reload --port 8000
```

**Terminal 2 - Frontend (React App):**
```bash
npm run dev
```

Open `http://localhost:5173` in your browser.

## Features

### Core Features (MVP)
- **Input**: Fish species + location preference
- **Output**: Optimal fishing locations based on weather and data
- **Camera Scan**: Identify caught fish type and weight
- **Weather Integration**: METAR, TAF, and current conditions
- **Regional Data**: Fish species by location
- **Community**: View tournaments, events, and active fishing spots

### Future Features
- Marketplace for fishing gear and bait
- Advanced fish weight prediction
- Social fishing community

## Project Structure

```
GoFish/
├── main.py                 # FastAPI backend
├── train_fish_model.py     # Train fish classification model
├── seed_db.py              # Populate MongoDB with fish data
├── requirements.txt        # Python dependencies
├── package.json            # Frontend dependencies
├── src/
│   ├── App.jsx            # React main app
│   ├── FishScanner.jsx    # Camera/scan component
│   ├── main.jsx           # React entry
│   └── index.css          # Styles
├── models/                 # Trained ML models
├── Fish_Data/              # Fish training images
└── QUICK_START.md         # This file
```

## Next Steps

1. **Add fish species data** to MongoDB with regional information
2. **Integrate weather APIs** (METAR, TAFS)
3. **Build recommendation engine** to suggest optimal locations
4. **Implement community features** for events/tournaments
5. **Enhance camera scanning** with more fish species

## Commands Summary

```bash
# Install dependencies
pip install -r requirements.txt
npm install

# Train model (if you have new fish images)
python train_fish_model.py

# Seed database
python seed_db.py

# Start backend
uvicorn main:app --reload --port 8000

# Start frontend (in another terminal)
npm run dev
```

## Troubleshooting

**MongoDB connection failed**
- Verify `MONGO_URL` in `.env` is correct
- Check database credentials and IP whitelist

**CORS errors in browser**
- Backend CORS middleware is configured in `main.py`
- Ensure backend is running on port 8000

**Camera not working**
- Check browser permissions for camera access
- Some browsers require HTTPS for camera access
