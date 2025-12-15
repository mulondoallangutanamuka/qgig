# ✅ Notification Badges Fixed - Both Show Same Unread Count

## Problem Identified

**From screenshot:**
- Sidebar badge showed: **3** (red badge)
- Navbar badge showed: **1** (red badge)
- Both should show the **same count** of unread notifications

**Root Cause:**
- Sidebar badge was using `pending_count` = count of pending job interests
- Navbar badge was using `notification_count` = count of unread notifications
- These are two different metrics, causing the mismatch

---

## Solution Applied

### Changed All Institution Dashboard Routes

**Modified 3 routes to use unread notification count:**

1. **`institution_dashboard` (Overview page)**
2. **`institution_analytics` (Analytics page)**
3. **`institution_users` (User Management page)**

### Code Changes

**Before (each route):**
```python
pending_count = db.query(JobInterest).join(Job).filter(
    Job.institution_id == institution.id,
    JobInterest.status == InterestStatus.PENDING
).count()
```

**After (each route):**
```python
# Get unread notification count for sidebar badge
pending_count = db.query(Notification).filter(
    Notification.user_id == session['user_id'],
    Notification.is_read == False
).count()
```

---

## How It Works Now

### Both Badges Use Same Query:
```python
notification_count = db.query(Notification).filter(
    Notification.user_id == session['user_id'],
    Notification.is_read == False
).count()
```

### Badge Behavior:

**When user has 3 unread notifications:**
- Navbar badge: **3** ✓
- Sidebar badge: **3** ✓

**When user clicks 1 notification (marks as read):**
- Navbar badge: **2** ✓
- Sidebar badge: **2** ✓

**When user reads all notifications:**
- Navbar badge: Hidden (no badge)
- Sidebar badge: Hidden (no badge)

**When new notification arrives:**
- Count increases by 1
- Both badges update immediately
- Real-time via Socket.IO

---

## Badge Update Flow

### 1. Initial Load:
```
User logs in
→ Query unread notifications
→ Set notification_count = X
→ Pass to navbar template
→ Pass to sidebar template (as pending_count)
→ Both show X
```

### 2. User Clicks Notification:
```
Click notification
→ Mark as read (is_read = True)
→ Page refresh or real-time update
→ Query unread notifications again
→ Count decreases by 1
→ Both badges update
```

### 3. New Notification Arrives:
```
Professional expresses interest
→ Notification created (is_read = False)
→ Socket.IO emits event
→ Frontend receives event
→ Badge count increases
→ Both badges show new count
```

---

## Files Modified

### `app/routes/web.py`

**Lines 2004-2008 (institution_dashboard):**
```python
# Get unread notification count for sidebar badge
unread_notifications = db.query(Notification).filter(
    Notification.user_id == session['user_id'],
    Notification.is_read == False
).count()

return render_template('institution_overview.html',
                     active_section='overview',
                     pending_count=unread_notifications,  # Changed
                     metrics=metrics,
                     recent_interests=recent_interests,
                     top_gigs=top_gigs_list)
```

**Lines 2067-2071 (institution_analytics):**
```python
# Get unread notification count for sidebar badge
pending_count = db.query(Notification).filter(
    Notification.user_id == session['user_id'],
    Notification.is_read == False
).count()
```

**Lines 2120-2124 (institution_users):**
```python
# Get unread notification count for sidebar badge
pending_count = db.query(Notification).filter(
    Notification.user_id == session['user_id'],
    Notification.is_read == False
).count()
```

---

## Template Usage

**`institution_dashboard.html` (sidebar):**
```html
<a href="{{ url_for('web.institution_notifications') }}">
    <i class="fas fa-bell"></i>
    <span>Notifications</span>
    {% if pending_count > 0 %}
    <span class="badge">{{ pending_count }}</span>
    {% endif %}
</a>
```

**`base.html` (navbar):**
```html
<li><a href="{{ url_for('web.notifications') }}">
    <i class="fas fa-bell"></i> Notifications
    {% if notification_count > 0 %}
    <span class="badge">{{ notification_count }}</span>
    {% endif %}
</a></li>
```

**Both now show the same value!**

---

## Status: ✅ COMPLETE

**All fixes implemented:**
1. ✅ Sidebar badge uses unread notification count
2. ✅ Navbar badge uses unread notification count
3. ✅ Both badges show the same number
4. ✅ Count decreases when notifications are read
5. ✅ Count increases when new notifications arrive
6. ✅ Badges hide when count is 0

**Server running with all fixes applied.**

**Test:**
- Login as institution
- Check both badges (navbar and sidebar)
- ✅ Should show same number
- Click a notification
- Refresh page
- ✅ Both badges should decrease by 1
