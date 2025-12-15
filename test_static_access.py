"""
Test if static files are accessible
"""
import requests

# Test URLs
base_url = "http://127.0.0.1:5000"
test_urls = [
    "/static/uploads/professionals/2/certificate_2_20251214_225314_bdc453709f32.pdf",
    "/static/uploads/professionals/2/profile_picture_2_20251214_225326_5a5fc065f3d0.jpg",
    "/static/css/main.css",  # Test if any static file works
]

print("=== Testing Static File Access ===\n")

for url in test_urls:
    full_url = base_url + url
    try:
        response = requests.get(full_url)
        print(f"URL: {url}")
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        if response.status_code == 200:
            print(f"Size: {len(response.content)} bytes")
            print("✅ SUCCESS\n")
        else:
            print(f"❌ FAILED")
            print(f"Response: {response.text[:200]}\n")
    except Exception as e:
        print(f"URL: {url}")
        print(f"❌ ERROR: {e}\n")
