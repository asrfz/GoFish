# How to Start GoFish Servers

## Quick Start

You need to run **TWO** terminals - one for backend, one for frontend.

---

## Terminal 1: Backend Server (Port 8000)

```powershell
# Navigate to project folder
cd C:\github\go-fish\GoFish

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Start backend
python app.py
```

**OR** use the batch file:
```powershell
.\start_backend.bat
```

**Wait for:** You should see:
```
✅ GoFish API Ready!
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## Terminal 2: Frontend Server (Port 3000 or 3001)

```powershell
# Navigate to frontend folder
cd C:\github\go-fish\GoFish\frontend

# Start frontend
npm run dev
```

**OR** use the batch file:
```powershell
cd C:\github\go-fish\GoFish
.\start_frontend.bat
```

**Wait for:** You should see:
```
- Local:        http://localhost:3000
```
(or port 3001 if 3000 is busy)

---

## Verify It's Working

1. **Check Backend**: Open browser to `http://localhost:8000`
   - Should see: `{"message":"GoFish Unified API",...}`

2. **Check Backend Health**: `http://localhost:8000/api/health`
   - Should see status JSON

3. **Check Frontend**: Open browser to `http://localhost:3000` (or 3001)
   - Should see the Instagram-style GoFish app

---

## Troubleshooting

### "Port 8000 already in use"
```powershell
# Find process using port 8000
netstat -ano | findstr :8000

# Kill it (replace PID with the number you found)
Stop-Process -Id <PID> -Force
```

### "Port 3000 already in use"
Next.js will automatically use port 3001 instead. That's fine!

### "Module not found" errors
Make sure virtual environment is activated:
```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Backend won't start
Check if MongoDB URL is set in `.env` file:
```
MONGO_URL=mongodb+srv://...
```

### Frontend can't connect to backend
1. Make sure backend is running on port 8000
2. Check browser console for errors
3. Verify CORS is enabled (it should be)

---

## Need Help?

- Backend logs appear in Terminal 1
- Frontend logs appear in Terminal 2
- Check browser console (F12) for frontend errors
