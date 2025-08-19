from enum import Enum


class NotificationStatus(str, Enum):
    """Represents the lifecycle of a notification."""

    PENDING = "pending"          # Created, not yet processed
    QUEUED = "queued"            # Added to the job queue for async processing
    PROCESSING = "processing"    # Currently being sent (in progress)
    SENT = "sent"                # Successfully delivered to all recipients
    PARTIAL = "partial"          # Delivered to some, failed for others
    FAILED = "failed"            # Attempted but all failed
    RETRYING = "retrying"        # Scheduled for a retry attempt
    CANCELLED = "cancelled"      # Explicitly cancelled before sending
    SCHEDULED = "scheduled"      # Delayed to a specific future time