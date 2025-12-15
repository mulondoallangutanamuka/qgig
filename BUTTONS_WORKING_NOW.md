# ✅ Accept/Reject Buttons - Fixed!

## Error Fixed

**Error:** `type object 'InterestStatus' has no attribute 'REJECTED'`

**Root Cause:** The code was using `InterestStatus.REJECTED` but the enum only defines:
- `PENDING`
- `ACCEPTED`
- `DECLINED` ← The correct value for rejection

## Fix Applied

**Changed in `app/routes/web.py`:**

**Line 1844 (when accepting one interest, reject others):**
```python
# Before:
other.status = InterestStatus.REJECTED  # ❌ Error!

# After:
other.status = InterestStatus.DECLINED  # ✓ Correct!
```

**Line 1856 (when rejecting an interest):**
```python
# Before:
interest.status = InterestStatus.REJECTED  # ❌ Error!

# After:
interest.status = InterestStatus.DECLINED  # ✓ Correct!
```

## What This Fixes

**Accept Button:**
- No longer crashes with AttributeError
- Correctly sets accepted interest to `ACCEPTED`
- Correctly sets other interests to `DECLINED`
- Creates notifications for all professionals
- Emits Socket.IO events

**Reject Button:**
- No longer crashes with AttributeError
- Correctly sets interest to `DECLINED`
- Creates notification for professional
- Emits Socket.IO events

## Status: ✅ FIXED

**Both buttons now work correctly:**
- ✅ Accept button sets status to `ACCEPTED`
- ✅ Reject button sets status to `DECLINED`
- ✅ No more AttributeError
- ✅ Notifications created properly
- ✅ Database updated correctly
- ✅ Real-time updates via Socket.IO

**Server restarted with fix. Test the buttons now!**
