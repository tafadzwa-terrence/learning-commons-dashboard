#!/usr/bin/env python3
"""
Learning Commons Dashboard — Local Web Server with EarthCam HLS Proxy

Usage:
    python server.py
    python server.py 3001
"""

import http.server
import socketserver
import sys
import os
import json
import re
import urllib.parse
import urllib.request
import urllib.error
from urllib.parse import urljoin

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

# Keep only known-good direct mappings here.
# Times Square is the one you already confirmed works.
CAMERA_STREAMS = {
    "https://www.earthcam.com/usa/newyork/timessquare/?cam=tsrobo":
        "https://videos-3.earthcam.com/fecnetwork/hdtimes10.flv/playlist.m3u8",
    "https://www.earthcam.com/usa/newjersey/weehawken/?cam=lincolnharbor":
        "https://videos-3.earthcam.com/fecnetwork/22251.flv/playlist.m3u8",
}

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.earthcam.com/",
    "Origin": "https://www.earthcam.com",
}

def make_proxy_url(target_url: str) -> str:
    return f"/api/hls-proxy?url={urllib.parse.quote(target_url, safe='')}"

def fetch_text(url: str, timeout: int = 15) -> str:
    req = urllib.request.Request(url, headers=DEFAULT_HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="ignore")

def try_head_or_get(url: str, timeout: int = 10) -> bool:
    try:
        req = urllib.request.Request(url, headers=DEFAULT_HEADERS, method="HEAD")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return 200 <= resp.status < 400
    except Exception:
        try:
            req = urllib.request.Request(url, headers=DEFAULT_HEADERS)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return 200 <= resp.status < 400
        except Exception:
            return False

def normalize_cam_url(cam_url: str) -> str:
    parsed = urllib.parse.urlparse(cam_url)
    clean = parsed._replace(fragment="")
    return urllib.parse.urlunparse(clean)

def candidate_playlist_urls_from_html(html: str, page_url: str) -> list[str]:
    candidates = []

    # 1. Parse EarthCam's embedded JSON config blob (json_base, json_data, etc.)
    #    These blobs contain the cam_id and stream URL directly.
    for var_name in ("json_base", "json_data", "cam_data"):
        m = re.search(
            rf'var\s+{var_name}\s*=\s*(\{{.*?\}});',
            html, re.DOTALL | re.IGNORECASE
        )
        if m:
            try:
                obj = json.loads(m.group(1))
                # Extract stream URL from known keys
                for key in ("stream", "hls", "streamUrl", "stream_url", "hlsUrl"):
                    val = str(obj.get(key, ""))
                    if val and ("m3u8" in val or "fecnetwork" in val):
                        if val.startswith("//"):
                            val = "https:" + val
                        elif not val.startswith("http"):
                            val = urljoin(page_url, val)
                        if "fecnetwork" in val and not val.endswith(".m3u8"):
                            val = val.rstrip("/") + "/playlist.m3u8"
                        candidates.append(val)
                # Build fecnetwork URL from cam_id
                cam_id = str(obj.get("cam_id", "") or obj.get("camId", "") or "")
                if cam_id and re.match(r'^[a-zA-Z0-9_-]{2,}$', cam_id):
                    for n in [3, 1, 2, 4]:
                        candidates.append(
                            f"https://videos-{n}.earthcam.com/fecnetwork/{cam_id}.flv/playlist.m3u8"
                        )
            except Exception:
                pass

    # 2. Stream/HLS URL patterns inside JSON key-value pairs across the whole HTML
    for pattern in [
        r'"stream"\s*:\s*"((?:https?:|//)[^"<>]*?(?:\.m3u8|fecnetwork)[^"<>]*)"',
        r'"hls"\s*:\s*"((?:https?:|//)[^"<>]*\.m3u8[^"<>]*)"',
        r'"streamUrl"\s*:\s*"((?:https?:|//)[^"<>]*\.m3u8[^"<>]*)"',
    ]:
        for match in re.findall(pattern, html, re.IGNORECASE):
            url = match if match.startswith("http") else "https:" + match
            if "fecnetwork" in url and not url.endswith(".m3u8"):
                url = url.rstrip("/") + "/playlist.m3u8"
            candidates.append(url)

    # 3. Direct .m3u8 URLs anywhere in the HTML
    for match in re.findall(r'(?:https?:)?//[^\s"\'<>]+\.m3u8[^\s"\'<>]*', html, re.IGNORECASE):
        url = match if match.startswith("http") else "https:" + match
        candidates.append(url)
    for match in re.findall(r'/[^\s"\'<>]+\.m3u8[^\s"\'<>]*', html, re.IGNORECASE):
        candidates.append(urljoin(page_url, match))

    # 4. fecnetwork slug extraction → try playlist URL on all video servers
    slugs: set[str] = set()
    for pattern in [
        r'videos-\d+\.earthcam\.com/fecnetwork/([a-zA-Z0-9_-]+)\.flv',
        r'fecnetwork/([a-zA-Z0-9_-]+)\.flv',
        r'"cam_id"\s*:\s*"([a-zA-Z0-9_-]{2,})"',
        r"'cam_id'\s*:\s*'([a-zA-Z0-9_-]{2,})'",
    ]:
        slugs.update(re.findall(pattern, html, re.IGNORECASE))
    for slug in slugs:
        slug = slug.strip()
        if slug:
            for n in [3, 1, 2, 4]:
                candidates.append(f"https://videos-{n}.earthcam.com/fecnetwork/{slug}.flv/playlist.m3u8")

    # De-duplicate while preserving order
    seen: set[str] = set()
    uniq: list[str] = []
    for item in candidates:
        if item not in seen:
            seen.add(item)
            uniq.append(item)
    return uniq

def resolve_stream_url(cam_url: str) -> tuple[str | None, str]:
    cam_url = normalize_cam_url(cam_url)

    # 1) Direct exact mapping
    if cam_url in CAMERA_STREAMS:
        return CAMERA_STREAMS[cam_url], "direct-map"

    # 2) Base URL mapping without query string
    base_url = cam_url.split("?")[0]
    if base_url in CAMERA_STREAMS:
        return CAMERA_STREAMS[base_url], "base-map"

    # 3) Try scraping the EarthCam page for embedded stream candidates
    try:
        html = fetch_text(cam_url)
    except Exception as e:
        return None, f"page-fetch-failed: {e}"

    candidates = candidate_playlist_urls_from_html(html, cam_url)

    for candidate in candidates:
        if try_head_or_get(candidate):
            return candidate, "page-discovered"

    return None, "no-working-candidate-found"

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")

    def do_GET(self):
        if self.path.startswith("/api/earthcam-stream"):
            self.handle_earthcam_stream()
            return

        if self.path.startswith("/api/hls-proxy"):
            self.handle_hls_proxy()
            return

        super().do_GET()

    def handle_earthcam_stream(self):
        try:
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)
            cam_url = params.get("url", [None])[0]

            if not cam_url:
                self.send_error(400, "Missing 'url' parameter")
                return

            stream_url, source = resolve_stream_url(cam_url)

            if not stream_url:
                self.send_error(404, "No working stream URL found for this camera")
                return

            proxied_url = make_proxy_url(stream_url)
            response_json = json.dumps({
                "stream_url": proxied_url,
                "raw_stream_url": stream_url,
                "source": source
            })

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors_headers()
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.end_headers()
            self.wfile.write(response_json.encode("utf-8"))

            print(f"✓ Camera request: {cam_url}")
            print(f"  Resolved via : {source}")
            print(f"  Raw stream   : {stream_url}")
            print(f"  Proxy URL    : {proxied_url}", flush=True)

        except Exception as e:
            print(f"ERROR in /api/earthcam-stream: {e}", flush=True)
            self.send_error(500, f"Error: {e}")

    def handle_hls_proxy(self):
        try:
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)
            target = params.get("url", [None])[0]

            if not target:
                self.send_error(400, "Missing 'url' parameter")
                return

            req = urllib.request.Request(target, headers=DEFAULT_HEADERS)

            with urllib.request.urlopen(req, timeout=20) as resp:
                content = resp.read()
                content_type = resp.headers.get("Content-Type", "application/octet-stream")

            if ".m3u8" in target or "mpegurl" in content_type.lower():
                text = content.decode("utf-8", errors="ignore")
                rewritten_lines = []

                for line in text.splitlines():
                    stripped = line.strip()

                    if not stripped or stripped.startswith("#"):
                        rewritten_lines.append(line)
                        continue

                    absolute_url = urljoin(target, stripped)
                    rewritten_lines.append(make_proxy_url(absolute_url))

                content = "\n".join(rewritten_lines).encode("utf-8")
                content_type = "application/vnd.apple.mpegurl"

            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self._send_cors_headers()
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(content)

        except urllib.error.HTTPError as e:
            print(f"HTTP ERROR in /api/hls-proxy: {e.code} for {self.path}", flush=True)
            self.send_error(500, f"Proxy error: HTTP Error {e.code}: {e.reason}")
        except Exception as e:
            print(f"ERROR in /api/hls-proxy: {e}", flush=True)
            self.send_error(500, f"Proxy error: {e}")

    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def log_message(self, format, *args):
        pass

if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print("╔══════════════════════════════════════════════╗")
        print("║  Learning Commons Dashboard                  ║")
        print(f"║  Running at: http://localhost:{PORT}         ║")
        print("║  Press Ctrl+C to stop                        ║")
        print("╚══════════════════════════════════════════════╝")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")
            httpd.server_close()