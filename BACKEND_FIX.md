# Backend Connection Issues - Fix Guide

## 🔴 Problem
Both `/api/brain/advise` and `/api/fishing-spots` are failing with "Failed to fetch" errors.

## ✅ Solution

### Step 1: Restart Backend
The backend server is not responding. Restart it:

```powershell
# Stop any running backend (Ctrl+C if running)
# Then restart:
cd C:\github\go-fish\GoFish
.\venv\Scripts\Activate.ps1
python app.py
```

**Wait for:**
```
✅ GoFish API Ready!
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 2: Verify Backend is Working
Open in browser: `http://localhost:8000/api/health`

Should return:
```json
{
  "status": "healthy",
  "version": "2.0.0",
  ...
}
```

### Step 3: Test Endpoints
- `http://localhost:8000/api/species` - Should return species list
- `http://localhost:8000/api/fishing-spots?species=walleye&limit=10` - Should return spots

## 📝 What I Fixed

1. **Better Error Messages**: Now shows specific connection errors
2. **Health Check**: Components verify backend before making requests
3. **Timeout Handling**: Proper timeout and abort signal handling
4. **Error Display**: Errors shown in UI with helpful messages

## 🖼️ Images Added to Posts

Hardcoded posts now include fish images from Unsplash:
- Bass post: Bass fishing image
- Trout post: Trout fishing image  
- Walleye post: Walleye fishing image

## 🔧 If Still Not Working

1. **Check Backend Terminal**: Look for error messages
2. **Check Port**: Make sure nothing else is using port 8000
3. **Check Firewall**: Windows Firewall might be blocking
4. **Try Different Port**: Edit `.env` or `app.py` to use port 8001

## ⚡ Quick Test

After restarting backend, the frontend should automatically:
- ✅ Connect to backend
- ✅ Fetch fishing spots
- ✅ Get brain advice
- ✅ Display images in posts
