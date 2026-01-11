# GoFish v2.0 - Quick Start Guide

## 🚀 5-Minute Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- Git LFS (for models)
- MongoDB Atlas account

### Step 1: Clone & Setup Python
```bash
cd GoFish
pip install -r requirements.txt
```

### Step 2: Setup Frontend
```bash
cd frontend
npm install
```

### Step 3: Verify .env
Check the `.env` file has:
```
MONGO_URL=mongodb+srv://proneo14:Grumpy_DOG92@proneo14.gowrhqp.mongodb.net/?appName=proneo14
DB_NAME=castnet
PORT=8000
```

### Step 4: Run Backend
```bash
# From GoFish root directory
python app.py
```

You should see:
```
✅ GoFish API Ready!
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 5: Run Frontend
```bash
# From GoFish/frontend directory
npm run dev
```

You should see:
```
▲ Next.js running on http://localhost:3000
```

### Step 6: Open in Browser
Navigate to: **http://localhost:3000**

## 🎮 Using GoFish

### Fish Scanner
1. Click **Fish Scanner** tab
2. Click **Capture & Scan** to use webcam OR **Select Image** to upload
3. Wait for AI to identify the species
4. View confidence scores and identification method

### Fishing Spots
1. Click **Fishing Spots** tab
2. Select a fish species from dropdown
3. Click **Search**
4. View top 10 locations with bite scores and weather
5. Check temperature, pressure, and wind conditions

### Safety & Recipes
1. Click **Safety & Recipes** tab
2. Select a fish species
3. View safety information and edibility status
4. Get recipe ideas with preparation steps
5. Check community alerts and health warnings

## 📊 What's Running

| Service | Port | Purpose |
|---------|------|---------|
| Backend (FastAPI) | 8000 | API server - all three modules |
| Frontend (Next.js) | 3000 | Web UI dashboard |
| MongoDB | Atlas | Database for fish data |

## 🔧 Key Features

✅ **Fish Scanner**
- PyTorch + CLIP hybrid identification
- 250+ species database
- Live webcam & file upload

✅ **Fishing Spots**
- 1,247 Ontario locations
- Real-time weather from Open-Meteo
- Species-specific bite scores

✅ **Safety & Recipes**
- Evidence-based safety info
- Quick recipe ideas
- Mercury warnings & health filters

## 📁 Important Files

```
GoFish/
├── app.py                    # Main backend (1200 lines - all modules combined)
├── requirements.txt          # Python dependencies  
├── .env                      # Configuration
├── frontend/                 # Next.js React app
│   ├── src/app/page.tsx     # Main dashboard
│   ├── src/components/      # UI components
│   └── package.json         # Frontend dependencies
├── fish-scan/               # Models & training data
│   ├── models/              # .pth files (via Git LFS)
│   └── Fish_Data/           # Training images (3,500+)
└── README.md                # Full documentation
```

## 🛠️ API Endpoints (Test with Swagger)

Open: **http://localhost:8000/docs**

### Main Endpoints:
- `POST /api/scan-fish` - Identify fish from image
- `GET /api/fishing-spots` - Find best spots by species
- `GET /api/species` - List available species
- `POST /api/brain/advise` - Get safety & recipes
- `GET /api/health` - Server status

## 🐛 Quick Troubleshooting

**Backend won't start:**
```bash
# Check port is available
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill any process on 8000 and retry
```

**Frontend won't compile:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

**Models not found:**
```bash
git lfs install
git lfs pull
```

**MongoDB can't connect:**
- Check MONGO_URL in .env
- Whitelist your IP in MongoDB Atlas
- Verify network access

## 📝 Next Steps

1. **Scan a fish** - Take a photo and identify the species
2. **Find a spot** - Get recommendations for where to fish
3. **Check safety** - Learn how to prepare your catch
4. **Explore API** - Visit http://localhost:8000/docs for all endpoints

## 📚 More Information

- Full README: `README.md`
- API Documentation: http://localhost:8000/docs
- Frontend Code: `frontend/src/`
- Backend Code: `app.py`

---

**Happy Fishing!** 🎣 Questions? Check the full README.md
