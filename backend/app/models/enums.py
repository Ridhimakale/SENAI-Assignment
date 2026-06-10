from enum import StrEnum


class ContactStatus(StrEnum):
    VIP = "VIP"
    BLOCKED = "Blocked"
    ACTIVE = "Active"
    CHURNED = "Churned"


class ThreadStatus(StrEnum):
    OPEN = "Open"
    RESOLVED = "Resolved"
    ESCALATED = "Escalated"
    IGNORED = "Ignored"


class EmailStatus(StrEnum):
    RECEIVED = "Received"
    PROCESSING = "Processing"
    REPLIED = "Replied"
    ESCALATED = "Escalated"
    IGNORED = "Ignored"


class EmailCategory(StrEnum):
    COMPLAINT = "Complaint"
    INQUIRY = "Inquiry"
    BUG_REPORT = "Bug Report"
    FEATURE_REQUEST = "Feature Request"
    COMPLIANCE = "Compliance"
    LEGAL = "Legal"
    BILLING = "Billing"
    SPAM = "Spam"
    INTERNAL = "Internal"
    OTHER = "Other"


class EmailUrgency(StrEnum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class ActionType(StrEnum):
    AUTO_REPLY = "Auto-Reply"
    ESCALATE = "Escalate"
    LEGAL_FLAG = "Legal-Flag"
    TICKET_CREATED = "Ticket-Created"
    IGNORED = "Ignored"


class ActionStatus(StrEnum):
    PROPOSED = "Proposed"
    EXECUTED = "Executed"
    BLOCKED = "Blocked"
    FAILED = "Failed"


class JobStatus(StrEnum):
    QUEUED = "Queued"
    PROCESSING = "Processing"
    COMPLETED = "Completed"
    FAILED = "Failed"
    SKIPPED = "Skipped"


class TicketStatus(StrEnum):
    OPEN = "Open"
    IN_PROGRESS = "InProgress"
    RESOLVED = "Resolved"


class ClassificationValidationStatus(StrEnum):
    VALID = "Valid"
    INVALID = "Invalid"
    REPAIRED = "Repaired"
    FAILED = "Failed"


class WebIntelligenceStatus(StrEnum):
    SUCCESS = "Success"
    FAILED = "Failed"
    SKIPPED_ROBOTS = "SkippedRobots"
