"""
Database indexes for performance optimization
This file documents the indexes that should be created for optimal query performance
"""

# Indexes are defined in the models using index=True parameter
# Additional composite indexes for common queries:

# User table indexes:
# - email (unique, already indexed)
# - role (for filtering by role)
# - is_active (for filtering active users)

# Job table indexes:
# - status (for filtering by job status)
# - institution_id (for institution's jobs)
# - assigned_professional_id (for professional's assigned jobs)
# - created_at (for sorting by date)
# - is_urgent (for filtering urgent jobs)

# Payment table indexes:
# - gig_id (for job payments)
# - institution_id (for institution payments)
# - professional_id (for professional payments)
# - status (for filtering by payment status)
# - pesapal_order_tracking_id (unique, for webhook lookups)

# Rating table indexes:
# - rated_id (for user ratings)
# - rater_id (for ratings given)
# - gig_id (for job ratings)
# - Composite unique index on (gig_id, rater_id)

# Document table indexes:
# - user_id (for user documents)
# - status (for pending documents)
# - reviewed_by (for admin review tracking)

# GigInterest table indexes:
# - job_id (for interested professionals)
# - professional_id (for professional interests)
# - created_at (for sorting by interest date)
