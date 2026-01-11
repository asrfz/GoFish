# 🚀 Quick Start Guide

## The Problem
- **Backend** (port 8000) is NOT running
- **Frontend** needs the backend to work
- You need to start BOTH servers

---

## ✅ Solution: Start Both Servers

### Step 1: Start Backend (Terminal 1)

Open PowerShell and run:
```powershell
cd C:\github\go-fish\GoFish
.\venv\Scripts\Activate.ps1
python app.py
```

**✅ Success looks like:**
```
✅ GoFish API Ready!
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**❌ Keep this terminal open!** Don't close it.

---

### Step 2: Start Frontend (Terminal 2)

Open a **NEW** PowerShell window and run:
```powershell
cd C:\github\go-fish\GoFish\frontend
npm run dev
```

**✅ Success looks like:**
```
- Local:        http://localhost:3000
```

---

### Step 3: Open Browser

1. Go to: `http://localhost:3000` (or 3001 if 3000 is busy)
2. You should see the Instagram-style GoFish app!

---

## 🔍 Verify Backend is Working

While backend is running, open in browser:
- `http://localhost:8000` → Should show API status
- `http://localhost:8000/api/health` → Should show health check

---

## ⚠️ Common Issues

### Issue: "Port 8000 already in use"
```powershell
# Kill the process
netstat -ano | findstr :8000
# Find the PID number, then:
Stop-Process -Id <PID> -Force
```

### Issue: "Module not found"
```powershell
# Make sure venv is activated
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Issue: Backend crashes
- Check if MongoDB URL is needed (optional - backend will work without it)
- Check terminal for error messages

---

## 📝 Important Notes

1. **TWO terminals needed** - one for backend, one for frontend
2. **Backend must start FIRST** before frontend
3. **Keep both terminals open** - closing them stops the servers
4. **Port 3000 vs 3001** - both work, just use whichever the frontend says

---

## 🎯 You're Done When:

✅ Backend running on port 8000  
✅ Frontend running on port 3000/3001  
✅ Browser shows GoFish app  
✅ You can click tabs (Feed, Spots, Scan, Brain)
