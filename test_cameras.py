#!/usr/bin/env python3
import urllib.request
import urllib.error
import re

cameras = [
    'https://www.earthcam.com/usa/newyork/timessquare/?cam=tsrobo',
    'https://www.earthcam.com/usa/california/sanfrancisco/?cam=goldengate',
    'https://www.earthcam.com/world/italy/venice/?cam=venice',
    'https://www.earthcam.com/europe/france/paris/?cam=eiffel',
]

for cam_url in cameras:
    print(f"\nTesting: {cam_url.split('?')[0]}")
    try:
        req = urllib.request.Request(cam_url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://www.earthcam.com/'
        })
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8')
            match = re.search(r'var json_base\s*=\s*({.*?});', html, re.DOTALL)
            if match:
                json_str = match.group(1)
                stream_match = re.search(r'"stream":"([^"]*)', json_str)
                if stream_match:
                    print(f"  ✓ Found stream URL")
                else:
                    print(f"  ✗ No stream URL in json_base")
            else:
                print(f"  ✗ No json_base found")
    except urllib.error.HTTPError as e:
        print(f"  ✗ HTTP Error {e.code}: {e.reason}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
