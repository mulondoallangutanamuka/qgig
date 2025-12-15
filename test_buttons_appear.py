"""Test that Accept/Reject buttons appear on notifications page"""
import requests
from bs4 import BeautifulSoup

BASE_URL = "http://127.0.0.1:5000"

# Create session
session = requests.Session()

# Login as institution
print("Logging in as institution...")
response = session.post(
    f"{BASE_URL}/login",
    data={
        'email': 'nairobi.hospital@gmail.com',
        'password': 'password123'
    },
    allow_redirects=True
)

if response.status_code == 200:
    print("✓ Login successful")
    
    # Get notifications page
    print("\nFetching notifications page...")
    response = session.get(f"{BASE_URL}/notifications")
    
    if response.status_code == 200:
        print("✓ Notifications page loaded")
        
        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Check for Accept button
        accept_buttons = soup.find_all('button', string=lambda text: text and 'Accept' in text)
        reject_buttons = soup.find_all('button', string=lambda text: text and 'Reject' in text)
        
        print(f"\n{'='*60}")
        print("BUTTON VISIBILITY TEST")
        print(f"{'='*60}")
        
        if accept_buttons:
            print(f"✅ ACCEPT BUTTON FOUND! ({len(accept_buttons)} button(s))")
            for btn in accept_buttons:
                print(f"   - {btn.get_text(strip=True)}")
        else:
            print("❌ ACCEPT BUTTON NOT FOUND")
        
        if reject_buttons:
            print(f"✅ REJECT BUTTON FOUND! ({len(reject_buttons)} button(s))")
            for btn in reject_buttons:
                print(f"   - {btn.get_text(strip=True)}")
        else:
            print("❌ REJECT BUTTON NOT FOUND")
        
        # Check for the JavaScript functions
        page_text = response.text
        has_accept_function = 'acceptInterest' in page_text
        has_reject_function = 'rejectInterest' in page_text
        
        print(f"\n{'='*60}")
        print("JAVASCRIPT FUNCTIONS TEST")
        print(f"{'='*60}")
        print(f"acceptInterest function: {'✅ FOUND' if has_accept_function else '❌ NOT FOUND'}")
        print(f"rejectInterest function: {'✅ FOUND' if has_reject_function else '❌ NOT FOUND'}")
        
        # Check for notification items
        notification_items = soup.find_all('div', class_='notification-item')
        print(f"\n{'='*60}")
        print("NOTIFICATIONS TEST")
        print(f"{'='*60}")
        print(f"Notification items found: {len(notification_items)}")
        
        if notification_items:
            for i, item in enumerate(notification_items, 1):
                title = item.find('h4')
                if title:
                    print(f"\nNotification {i}: {title.get_text(strip=True)}")
                    
                    # Check for buttons in this notification
                    item_accept = item.find('button', string=lambda text: text and 'Accept' in text)
                    item_reject = item.find('button', string=lambda text: text and 'Reject' in text)
                    
                    if item_accept:
                        print("  ✅ Has Accept button")
                    if item_reject:
                        print("  ✅ Has Reject button")
                    
                    if not item_accept and not item_reject:
                        # Check for badges
                        badges = item.find_all('span')
                        for badge in badges:
                            badge_text = badge.get_text(strip=True)
                            if 'Accepted' in badge_text or 'Rejected' in badge_text:
                                print(f"  ℹ️  Status badge: {badge_text}")
        
        print(f"\n{'='*60}")
        print("FINAL RESULT")
        print(f"{'='*60}")
        
        if accept_buttons and reject_buttons:
            print("✅ SUCCESS! Accept and Reject buttons are VISIBLE!")
            print("\nYou can now:")
            print("1. Go to http://127.0.0.1:5000/notifications")
            print("2. Click the green 'Accept' button")
            print("3. Or click the red 'Reject' button")
            print("4. Confirm the action in the dialog")
            exit(0)
        else:
            print("❌ FAILED! Buttons are still not visible")
            print("\nDebugging info:")
            print(f"  - Accept buttons found: {len(accept_buttons)}")
            print(f"  - Reject buttons found: {len(reject_buttons)}")
            print(f"  - Notification items: {len(notification_items)}")
            exit(1)
    else:
        print(f"❌ Failed to load notifications page: {response.status_code}")
        exit(1)
else:
    print(f"❌ Login failed: {response.status_code}")
    exit(1)
