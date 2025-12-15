# Backup of Old Notification System

This file contains references to the old notification system before complete rebuild.

## Files to be deleted/rebuilt:
1. `app/models/notification.py` - Database model
2. `app/templates/notifications.html` - Template
3. Notification routes in `app/routes/web.py`
4. Notification API endpoints in `app/routes/api.py`

## Database table:
- `notifications` table will be dropped and recreated

## Backup timestamp:
December 14, 2025 at 1:03pm UTC+03:00

## Reason for rebuild:
Complete rebuild requested by user to ensure Accept/Reject buttons work correctly for all notifications.
