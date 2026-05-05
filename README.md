# Pace University — Learning Commons Dashboard

A modern, real-time information dashboard built for the TV displays at the Pace University Learning Commons (Pleasantville campus).

---

## Features

- **Live Camera** — EarthCam live stream rotating between Lincoln Harbor/Weehawken (NYC skyline) and Times Square, NY. Automatically falls back to the next camera if one is unavailable.
- **Live Weather** — Current conditions + 7-day forecast for Pleasantville, NY via [Open-Meteo](https://open-meteo.com/) (free, no API key required)
- **Learning Commons Info** — Hours of operation (today highlighted), upcoming closures, and announcements
- **3 Scrolling Tickers** — Stocks (static display), Sports headlines (BBC Sport RSS), and either CNN News or Inspirational Quotes depending on version
- **Auto-Refresh** — Page reloads every 60 minutes to keep content fresh
- **Pace Branding** — Dark theme with Pace blue and gold accents

---

## Quick Start

> **The Python server is required.** The EarthCam live camera uses a server-side HLS proxy — the dashboard will not show a live video feed if opened directly as a file.

```bash
# 1. Navigate to the project folder
cd "Learning Commons/learning-commons-dashboard"

# 2. Start the server
python server.py

# 3. Open in browser
#    http://localhost:8080
```

Press `Ctrl+C` in the terminal to stop the server.

---

## File Structure

```
learning-commons-dashboard/
├── index.html          # The dashboard (single file, self-contained)
├── server.py           # Local web server + EarthCam HLS proxy (required)
├── start-dashboard.bat # Windows one-click launcher
├── kiosk-setup.md      # TV kiosk deployment instructions
├── README.md           # This file
├── test_cameras.py     # Dev tool: test EarthCam stream discovery
├── test_api.py         # Dev tool: test the local stream API endpoint
└── .gitignore
```

---

## Configuration

All configuration is inside the `<script>` section of `index.html` (and `index-alt.html`). No separate config files are needed.

### Hours of Operation

Find the `LC_HOURS` array and update:

```javascript
const LC_HOURS = [
  { day: "Monday",    hours: "10:00 AM – 9:00 PM" },
  { day: "Tuesday",   hours: "10:00 AM – 9:00 PM" },
  { day: "Wednesday", hours: "10:00 AM – 9:00 PM" },
  { day: "Thursday",  hours: "10:00 AM – 6:00 PM" },
  { day: "Friday",    hours: "10:00 AM – 3:00 PM" },
  { day: "Saturday",  hours: "Closed" },
  { day: "Sunday",    hours: "Closed" }
];
```

### Upcoming Closures

Find the `closures-card` section in the HTML and edit:

```html
<div class="closure-item">
  <span>Spring Break</span>
  <span class="closure-date">Mar 26 – Apr 6</span>
</div>
```

### Announcements

Find the `announcements-card` section and edit the four `announce-item` divs:

```html
<div class="announce-item">
  <span style="color:var(--accent-primary)">▸</span>
  <span>Free tutoring during open hours.</span>
</div>
```

### Weather Location

To change the weather location (e.g. for the NYC campus), update:

```javascript
const WEATHER_LAT = 41.1368;   // Pleasantville, NY
const WEATHER_LON = -73.7915;
```

And update the display label in the HTML:

```html
<div class="weather-loc-name">Pleasantville, NY</div>
<div class="weather-loc-sub">Pace University Campus</div>
```

### Camera Rotation

Cameras are configured in the `CAMERAS` array in the script:

```javascript
const CAMERAS = [
  {
    name: "Lincoln Harbor, Weehawken",
    url: "https://www.earthcam.com/usa/newjersey/weehawken/?cam=lincolnharbor",
    utc: -4
  },
  {
    name: "Times Square, New York",
    url: "https://www.earthcam.com/usa/newyork/timessquare/?cam=tsrobo",
    utc: -4
  }
];
```

- The dashboard shows `CAMERAS[0]` first and rotates every **10 minutes**
- If a camera stream fails, it automatically advances to the next camera
- To change the rotation interval, find `const ROTATION_MS = 10 * 60 * 1000` and update the value

#### Adding a New EarthCam Camera

1. Open the EarthCam page for the desired camera in Chrome
2. Open DevTools (`F12`) → **Network** tab → filter by `m3u8`
3. Reload the page — a `playlist.m3u8` request will appear
4. Right-click it → **Copy** → **Copy link address**
5. Add a direct mapping in `server.py`:

```python
CAMERA_STREAMS = {
    "https://www.earthcam.com/usa/newjersey/weehawken/?cam=lincolnharbor":
        "https://videos-3.earthcam.com/fecnetwork/22251.flv/playlist.m3u8",
    "https://www.earthcam.com/usa/newyork/timessquare/?cam=tsrobo":
        "https://videos-3.earthcam.com/fecnetwork/hdtimes10.flv/playlist.m3u8",
    # Add new camera here (use base URL without ?t=token):
    "https://www.earthcam.com/...":
        "https://videos-3.earthcam.com/fecnetwork/SLUG.flv/playlist.m3u8",
}
```

6. Add the camera to the `CAMERAS` array in `index.html`
7. Restart `server.py`

---

## Updating for a New Semester

At the start of each semester, update these items in `index.html`:

1. **Hours of operation** — Update `LC_HOURS` array if the schedule changed
2. **Upcoming closures** — Replace the closure dates in the HTML
3. **Announcements** — Update with current semester announcements

---

## Deployment (TV Kiosks)

See [`kiosk-setup.md`](kiosk-setup.md) for full instructions. Summary:

1. Run `python server.py` on the kiosk machine (or use `start-dashboard.bat` on Windows)
2. Launch Chrome in kiosk mode:
   ```
   chrome.exe --kiosk http://localhost:8080
   ```
3. Set the machine to auto-login and auto-start the server + browser on boot
4. Disable sleep and screensaver on the display

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Live camera shows "unavailable" | Ensure `server.py` is running; the HLS proxy is required for EarthCam streams |
| Camera stuck on one view | The dashboard auto-advances after ~12s timeout; Times Square is the reliable fallback |
| Camera stream URL expired | Re-discover the stream URL via Chrome DevTools Network tab → update `CAMERA_STREAMS` in `server.py` |
| Sports ticker shows placeholder text | BBC Sport RSS may be temporarily down; The Guardian or NYT Sports will be tried automatically |
| Weather not loading | Check internet connection; Open-Meteo may be temporarily unavailable |
| Layout looks cramped | Dashboard is designed for 1920×1080; test in fullscreen (`F11`) |
| Page not found | Make sure `server.py` is running (not just opening the file directly) |

---

## Tech Stack

- **HTML / CSS / JS** — Single file per version, no build step, no npm
- **Python** — `server.py` serves the files and proxies EarthCam HLS streams to avoid CORS restrictions
- **HLS.js** — Client-side HLS video playback via CDN
- **EarthCam** — Live scenic camera streams
- **Open-Meteo** — Free weather API, no key required
- **rss2json** — Converts RSS feeds (CNN, BBC Sport) to JSON
- **Plus Jakarta Sans + JetBrains Mono** — Via Google Fonts

---

## License

Internal use — Pace University Learning Commons.
