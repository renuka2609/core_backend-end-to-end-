import urllib.request
import json
import sys

try:
    print("Testing /api/schema/ endpoint...")
    response = urllib.request.urlopen('http://127.0.0.1:8000/api/schema/')
    content = response.read().decode('utf-8')
    print(f"Status: {response.status}")
    print(f"Content length: {len(content)}")
    
    data = json.loads(content)
    print(f"\nSchema keys: {list(data.keys())}")
    
    if 'paths' in data:
        print(f"\nTotal paths found: {len(data['paths'])}")
        if len(data['paths']) > 0:
            for i, path in enumerate(list(data['paths'].keys())[:5]):
                print(f"  {i+1}. {path}")
        else:
            print("  (No paths found)")
    else:
        print("  No 'paths' key in schema!")
        
    if 'info' in data:
        print(f"\nAPI Info:")
        print(f"  Title: {data['info'].get('title', 'N/A')}")
        print(f"  Version: {data['info'].get('version', 'N/A')}")
        
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
    sys.exit(1)
