"""
Test newly uploaded document URLs
"""
import requests

base_url = "http://127.0.0.1:5000"
urls = [
    "/static/uploads/professionals/4/profile_picture_4_20251215_085432_4046e5c64295.jpg",
    "/static/uploads/professionals/4/cv_4_20251215_085443_b0b806878528.pdf",
    "/static/uploads/professionals/4/certificate_4_20251215_085449_950a6e4c3e06.pdf"
]

print("=== Testing Newly Uploaded Documents ===\n")

for url in urls:
    full_url = base_url + url
    try:
        response = requests.get(full_url)
        filename = url.split('/')[-1]
        print(f"File: {filename}")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Size: {len(response.content)} bytes")
            print("✅ SUCCESS\n")
        else:
            print(f"❌ FAILED\n")
    except Exception as e:
        print(f"File: {url.split('/')[-1]}")
        print(f"❌ ERROR: {e}\n")
