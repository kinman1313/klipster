# Klipster - Windows Setup Guide

Complete guide for running Klipster on Windows 10/11.

## Prerequisites Installation

### 1. Install Python 3.8+

**Option A: From Microsoft Store (Easiest)**
1. Open Microsoft Store
2. Search for "Python 3.12"
3. Click "Get" to install

**Option B: From Python.org**
1. Download from [python.org/downloads](https://www.python.org/downloads/)
2. Run installer
3. ✅ **IMPORTANT**: Check "Add Python to PATH" during installation
4. Click "Install Now"

**Verify Installation:**
```cmd
python --version
```

### 2. Install FFmpeg

**Option A: Using Chocolatey (Recommended)**
1. Install Chocolatey if you don't have it:
   - Open PowerShell as Administrator
   - Run:
   ```powershell
   Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
   ```

2. Install FFmpeg:
   ```powershell
   choco install ffmpeg
   ```

**Option B: Manual Installation**
1. Download FFmpeg from [ffmpeg.org/download.html](https://ffmpeg.org/download.html)
   - Choose Windows build (essentials or full)
2. Extract to `C:\ffmpeg`
3. Add to PATH:
   - Right-click "This PC" → Properties
   - Click "Advanced system settings"
   - Click "Environment Variables"
   - Under "System Variables", find "Path"
   - Click "Edit" → "New"
   - Add `C:\ffmpeg\bin`
   - Click "OK" on all dialogs

**Verify Installation:**
```cmd
ffmpeg -version
```

### 3. Get OpenAI API Key

1. Go to [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Sign in or create account
3. Click "Create new secret key"
4. Copy and save the key (you won't see it again!)

## Setup Klipster

### 1. Clone or Download Repository

**Using Git:**
```cmd
git clone https://github.com/kinman1313/klipster.git
cd klipster
```

**Or Download ZIP:**
1. Download ZIP from GitHub
2. Extract to a folder (e.g., `C:\Users\YourName\klipster`)
3. Open Command Prompt in that folder

### 2. Create Virtual Environment

```cmd
python -m venv venv
```

### 3. Activate Virtual Environment

```cmd
venv\Scripts\activate
```

You should see `(venv)` at the start of your command prompt.

### 4. Install Dependencies

```cmd
pip install -r requirements.txt
```

**If you get errors**, try:
```cmd
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Set Environment Variables

**Option A: Create .env file (Recommended)**

1. Copy the example file:
   ```cmd
   copy .env.example .env
   ```

2. Edit `.env` with Notepad:
   ```cmd
   notepad .env
   ```

3. Replace `your-openai-api-key-here` with your actual API key

4. Save and close

**Option B: Set in Command Prompt (Temporary)**
```cmd
set OPENAI_API_KEY=sk-your-actual-key-here
```

**Option C: Set System Environment Variable (Permanent)**
1. Search for "Environment Variables" in Windows Start
2. Click "Edit the system environment variables"
3. Click "Environment Variables"
4. Under "User variables", click "New"
5. Variable name: `OPENAI_API_KEY`
6. Variable value: Your OpenAI API key
7. Click "OK"

### 6. Initialize Database (Optional)

The database auto-creates on first run, but you can create it manually:

```cmd
python -c "from app import create_app; app = create_app(); app.app_context().push(); from app.models import db; db.create_all()"
```

## Running the Application

### 1. Make sure virtual environment is activated:
```cmd
venv\Scripts\activate
```

### 2. Run the app:
```cmd
python run.py
```

You should see:
```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

### 3. Open your browser to:
```
http://localhost:5000
```

## Using the Application

1. Paste a YouTube URL
2. Choose options:
   - Subtitle color (click color picker)
   - Emojis: e.g., `🔥` or `💯`
   - Effects: e.g., `speed:1.5,fadein:0.5,fadeout:0.5`
3. Click "Generate Clip"
4. Wait for processing
5. Clips will be saved in the `clips\` folder

## Common Windows Issues & Solutions

### ❌ "python is not recognized"
**Solution:** Python not in PATH. Reinstall Python and check "Add Python to PATH"

### ❌ "ffmpeg is not recognized"
**Solution:** FFmpeg not in PATH. Follow FFmpeg installation steps above.

### ❌ "Access Denied" when installing packages
**Solution:** Run Command Prompt as Administrator

### ❌ "SSL Certificate Error" when installing packages
**Solution:**
```cmd
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
```

### ❌ MoviePy errors about imagemagick
**Solution:** ImageMagick is optional. If needed:
```cmd
choco install imagemagick
```

### ❌ "Can't find vcruntime140.dll"
**Solution:** Install Visual C++ Redistributable:
- Download from [Microsoft](https://aka.ms/vs/17/release/vc_redist.x64.exe)
- Run the installer

### ❌ OpenAI API errors
**Solutions:**
- Check your API key is correct
- Ensure you have credits: [platform.openai.com/account/billing](https://platform.openai.com/account/billing)
- Verify environment variable is set: `echo %OPENAI_API_KEY%`

### ❌ Port 5000 already in use
**Solution:** Use a different port:

Edit `run.py`:
```python
if __name__ == '__main__':
    app.run(debug=True, port=5001)
```

### ❌ "Permission denied" accessing clips folder
**Solution:** Run Command Prompt as Administrator

## Project Folders (Windows Paths)

```
C:\Users\YourName\klipster\
├── venv\                    # Virtual environment
├── downloads\               # Downloaded YouTube videos
├── clips\                   # Generated clips (your output!)
├── app\                     # Application code
├── db.sqlite               # Database (auto-created)
├── .env                    # Your API key (create this)
└── run.py                  # Run this to start
```

## Tips for Windows Users

### Opening Command Prompt in Folder
- Hold `Shift` + Right-click folder → "Open PowerShell window here"
- Or type `cmd` in the folder address bar

### Finding Output Clips
```cmd
explorer clips
```

### Checking if Server is Running
```cmd
netstat -ano | findstr :5000
```

### Stopping the Server
- Press `Ctrl+C` in the Command Prompt

### Deactivating Virtual Environment
```cmd
deactivate
```

## Quick Start Batch Script

Create a file called `start.bat` in your klipster folder:

```batch
@echo off
echo Starting Klipster...
call venv\Scripts\activate
python run.py
pause
```

Then just double-click `start.bat` to run the app!

## Performance Notes

- First clip generation takes longer (downloads video)
- Typical processing time: 2-5 minutes per video
- Longer videos = more processing time
- Multiple clips generated per video

## Security Notes

- Never commit `.env` file with your API key
- Keep your OpenAI API key private
- Monitor your OpenAI usage/costs at platform.openai.com

## Getting Help

If you encounter issues:
1. Check this guide's troubleshooting section
2. Verify all prerequisites are installed
3. Check the main README.md for additional info
4. Ensure virtual environment is activated

## Updating the Application

```cmd
# Activate virtual environment
venv\Scripts\activate

# Pull latest changes
git pull

# Update dependencies
pip install -r requirements.txt --upgrade
```

---

**Need more help?** Check the main [README.md](README.md) for detailed API documentation and features.
