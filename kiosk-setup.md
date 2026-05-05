# TV Kiosk Deployment Guide

Step-by-step instructions for deploying the Learning Commons Dashboard on the TV display machines.

---

## Prerequisites

- Windows 10/11 PC connected to each TV
- Google Chrome installed
- Python 3 installed (for the local web server)
- Internet connection (for weather, live camera, and RSS feeds)

---

## Setup Steps

### 1. Copy the dashboard files

Copy the entire `learning-commons-dashboard` folder to a permanent location on the PC:

```
C:\LearningCommons\learning-commons-dashboard\
```

### 2. Test it works

Open Command Prompt and run:

```cmd
cd C:\LearningCommons\learning-commons-dashboard
python server.py
```

Open Chrome and go to `http://localhost:8080`. Verify:
- [ ] Weather loads correctly
- [ ] Live camera loads and shows a scenic view
- [ ] Hours of operation are correct for today
- [ ] All 3 tickers are scrolling (Headlines, Stocks, Sports)
- [ ] Layout fills the screen properly

### 3. Launch in kiosk mode

The project includes a ready-made `start-dashboard.bat` file. To use it:

1. Double-click `start-dashboard.bat` — this starts the server and opens Chrome in fullscreen kiosk mode automatically
2. To verify it works on boot, place a shortcut to `start-dashboard.bat` in the Windows Startup folder (see Step 4)

The batch file runs the following automatically:
```bat
python server.py          ← starts the web server
chrome.exe --kiosk ...    ← opens the dashboard fullscreen
```

### 4. Set to auto-start on boot

1. Press `Win + R`, type `shell:startup`, press Enter
2. Copy `start-dashboard.bat` (or create a shortcut to it) into the Startup folder
3. The dashboard will now launch automatically every time the PC boots

### 5. Configure Windows power settings

1. Open **Settings → System → Power & sleep**
2. Set **Screen** to `Never` turn off
3. Set **Sleep** to `Never`
4. Disable screensaver: **Settings → Personalization → Lock screen → Screen saver settings → None**

### 6. Configure auto-login (optional)

To skip the Windows login screen on boot:

1. Press `Win + R`, type `netplwiz`, press Enter
2. Uncheck "Users must enter a user name and password"
3. Enter the account credentials
4. Restart to verify

---

## Updating the Dashboard

When hours, closures, or announcements change:

1. Open `C:\LearningCommons\learning-commons-dashboard\index.html` in any text editor (Notepad, VS Code, etc.)
2. Make your changes (see `README.md` for exactly what to edit and where)
3. Save the file
4. The dashboard auto-reloads every hour, or press `F5` in Chrome to refresh immediately

> If Chrome is in kiosk mode, press `Alt + F4` to close it, make your edits, then run `start-dashboard.bat` again.

---

## Troubleshooting

### Dashboard won't start
- Check that Python is installed: open CMD and type `python --version`
- Make sure port 8080 is not already in use: `netstat -an | findstr 8080`
- Try a different port: `python server.py 3001`

### Live camera not loading
- The server (`server.py`) must be running — the camera will not work if the dashboard is opened as a plain file
- Check internet connection
- The camera will automatically fall back to the next configured view if one stream is unavailable

### Chrome shows "restore pages" dialog
- The `start-dashboard.bat` already includes `--disable-session-crashed-bubble` to suppress this

### Screen goes black / sleeps
- Re-check Windows power settings (Step 5 above)
- Some TVs have their own sleep timeout — check the TV's menu settings

### Need to exit kiosk mode
- Press `Alt + F4` to close Chrome
- Press `Ctrl + Alt + Delete` to open Task Manager if needed
