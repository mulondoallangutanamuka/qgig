"""Debug why buttons aren't appearing"""
import requests
from bs4 import BeautifulSoup

BASE_URL = "http://127.0.0.1:5000"
session = requests.Session()

# Login
session.post(f"{BASE_URL}/login", data={
    'email': 'nairobi.hospital@gmail.com',
    'password': 'password123'
})

# Get notifications
response = session.get(f"{BASE_URL}/notifications")
soup = BeautifulSoup(response.content, 'html.parser')

# Find the notification item
notif_item = soup.find('div', class_='notification-item')

if notif_item:
    print("Notification HTML:")
    print("="*80)
    print(notif_item.prettify())
    print("="*80)
    
    # Check for specific elements
    print("\nChecking for elements:")
    print(f"Title: {notif_item.find('h4').get_text() if notif_item.find('h4') else 'Not found'}")
    
    # Look for any buttons
    all_buttons = notif_item.find_all('button')
    print(f"\nTotal buttons found: {len(all_buttons)}")
    for i, btn in enumerate(all_buttons, 1):
        print(f"  Button {i}: {btn.get_text(strip=True)}")
        print(f"    onclick: {btn.get('onclick', 'None')}")
    
    # Check for the condition elements
    timestamp = notif_item.find('small')
    if timestamp:
        print(f"\nTimestamp found: {timestamp.get_text(strip=True)}")
else:
    print("No notification item found!")
