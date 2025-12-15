# Testing Instructions

## Prerequisites

Before running the E2E test, you need to create test users:

### 1. Start the Server
```bash
python main.py
```

### 2. Create Test Users

#### Option A: Via API (Recommended)
```bash
# Create Institution User
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "institution@test.com",
    "password": "test123",
    "role": "institution"
  }'

# Create Professional User
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "professional@test.com",
    "password": "test123",
    "role": "professional"
  }'
```

#### Option B: Via Web UI
1. Navigate to `http://localhost:5000/signup`
2. Register institution user: `institution@test.com` / `test123` / Role: Institution
3. Register professional user: `professional@test.com` / `test123` / Role: Professional

### 3. Create Profiles

Both users need to create their profiles before the test can run:

**Institution:**
1. Login as `institution@test.com`
2. Go to Profile page
3. Fill in institution details and save

**Professional:**
1. Login as `professional@test.com`
2. Go to Profile page
3. Fill in professional details (including full_name) and save

### 4. Run E2E Test
```bash
python test_complete_workflow.py
```

## Manual Testing Checklist

If you prefer manual testing, follow this workflow:

### As Institution:
1. ✅ Login
2. ✅ Navigate to "My Gigs" (should be in navigation menu)
3. ✅ Post a new gig
4. ✅ View the gig - should see Close (✔) and Delete (✗) buttons
5. ✅ Wait for professional to express interest
6. ✅ Check notifications - should see interest notification
7. ✅ Click Accept or Decline button on notification
8. ✅ Professional should receive notification
9. ✅ Try closing a gig (✔ button)
10. ✅ Try deleting a gig (✗ button)
11. ✅ Test notification deletion (single, selected, all)

### As Professional:
1. ✅ Login
2. ✅ Browse gigs
3. ✅ Click "Interested" button on a gig
4. ✅ Button should change to "Interest Sent" (green)
5. ✅ Refresh page - button should still show "Interest Sent"
6. ✅ Click "Interest Sent" again to withdraw
7. ✅ Confirm withdrawal
8. ✅ Button should revert to "Interested"
9. ✅ Institution should receive withdrawal notification
10. ✅ Check notifications for accept/decline responses
11. ✅ Test notification deletion

## Expected Results

### Interest Flow:
1. Professional clicks "Interested" → Button becomes "Interest Sent" (green)
2. Institution receives real-time notification
3. Institution clicks Accept → Professional receives "Interest Accepted" notification
4. Institution clicks Decline → Professional receives "Interest Declined" notification

### Withdrawal Flow:
1. Professional clicks "Interest Sent" → Confirmation dialog
2. Professional confirms → Button reverts to "Interested"
3. Institution receives notification: "The professional has withdrawn their interest in this gig."

### Gig Management:
1. Close button (✔) → Gig status changes to COMPLETED, no longer accepts interest
2. Delete button (✗) → Gig is permanently deleted after confirmation

### Notifications:
1. Each notification has a trash icon for individual deletion
2. Checkboxes allow selecting multiple notifications
3. "Delete Selected" button appears when checkboxes are checked
4. "Delete All" button in header deletes all notifications

## Troubleshooting

### "Invalid token" errors:
- Make sure you're logged in
- Check that JWT token is being sent in Authorization header

### "Profile not found" errors:
- Both users must create their profiles first
- Professional must have `full_name` field filled

### Socket.IO not connecting:
- Check browser console for connection errors
- Ensure server is running with Socket.IO enabled
- Check that session is active

### Notifications not appearing:
- Check browser console for Socket.IO events
- Verify user is in correct room (check server logs)
- Ensure notifications are being created in database

## Success Criteria

All features working correctly when:
- ✅ Interest button state persists across refreshes
- ✅ Withdraw interest works and sends notification
- ✅ Accept/Decline buttons work for institutions
- ✅ Real-time notifications appear instantly
- ✅ Close and Delete gig controls work
- ✅ Notification deletion works (single, selected, all)
- ✅ No backend crashes or 500 errors
- ✅ Proper authorization (users can only manage their own data)
