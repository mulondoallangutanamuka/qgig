"""
Test all document URLs
"""
import requests

base_url = "http://127.0.0.1:5000"
urls = [
    "/static/uploads/professionals/2/certificate_2_20251214_225314_bdc453709f32.pdf",
    "/static/uploads/professionals/2/profile_picture_2_20251214_225326_5a5fc065f3d0.jpg",
    "/static/uploads/professionals/2/cv_2_20251215_083007_98a54930bc25.pdf"
]

print("=== Testing All Document URLs ===\n")

for url in urls:
    full_url = base_url + url
    try:
        response = requests.get(full_url)
        filename = url.split('/')[-1]
        print(f"File: {filename}")
        print(f"URL: {url}")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Size: {len(response.content)} bytes")
            print("✅ SUCCESS\n")
        else:
            print(f"❌ FAILED\n")
    except Exception as e:
        print(f"File: {url.split('/')[-1]}")
        print(f"❌ ERROR: {e}\n")
