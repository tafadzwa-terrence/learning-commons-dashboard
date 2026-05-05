#!/usr/bin/env python3
import urllib.request
import urllib.parse
import json

cams = [
    ('Times Square', 'https://www.earthcam.com/usa/newyork/timessquare/?cam=tsrobo'),
    ('Golden Gate', 'https://www.earthcam.com/usa/california/sanfrancisco/?cam=goldengate'),
    ('Venice', 'https://www.earthcam.com/world/italy/venice/?cam=venice'),
]

for name, url in cams:
    api_url = f'http://localhost:3000/api/earthcam-stream?url={urllib.parse.quote(url, safe="")}'
    try:
        response = urllib.request.urlopen(api_url, timeout=10)
        content = response.read().decode('utf-8')
        data = json.loads(content)
        if 'stream_url' in data and data['stream_url']:
            stream = data['stream_url'][:80]
            print(f"✓ {name}: {stream}...")
        else:
            print(f"✗ {name}: No stream_url in response")
    except Exception as e:
        print(f"✗ {name}: {e}")
