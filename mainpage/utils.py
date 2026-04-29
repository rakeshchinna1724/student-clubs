# Utility functions for message moderation and filtering
from django.db.models import Q

# List of bad words to filter
BAD_WORDS = [
    'abuse', 'aggressive', 'bully', 'damn', 'hate', 'idiot', 'jerk', 'kill',
    'stupid', 'suck', 'trash', 'useless', 'worthless', 'badword', 'offensive',
    'harassment', 'racist', 'sexist', 'discriminate', 'threat', 'violence',
    'profanity', 'explicit', 'vulgar', 'obscene', 'inappropriate'
]


def contains_bad_words(text):
    """
    Check if text contains bad words.
    Returns True if bad words found, False otherwise.
    """
    text_lower = text.lower()
    for word in BAD_WORDS:
        if word in text_lower:
            return True
    return False


def censor_bad_words(text):
    """
    Censor bad words in text by replacing with asterisks.
    """
    text_censored = text
    for word in BAD_WORDS:
        censored = '*' * len(word)
        # Case-insensitive replacement
        import re
        pattern = re.compile(re.escape(word), re.IGNORECASE)
        text_censored = pattern.sub(censored, text_censored)
    return text_censored


def get_warning_count(student):
    """
    Get the current warning count for a student.
    """
    from .models import UserWarning
    latest_warning = student.warnings.order_by('-created_at').first()
    if latest_warning:
        return latest_warning.warning_count
    return 0


def add_warning(student, reason):
    """
    Add a warning to a student. Blocks after 2 warnings.
    Returns warning count.
    """
    from .models import UserWarning, BlockedUser
    
    current_count = get_warning_count(student)
    new_count = current_count + 1
    
    UserWarning.objects.create(
        student=student,
        warning_count=new_count,
        reason=reason
    )
    
    return new_count


def should_block_user(warning_count):
    """
    Determine if user should be blocked based on warning count.
    Block after 2 warnings.
    """
    return warning_count >= 2


def is_user_blocked(sender, recipient):
    """
    Check if sender is blocked by recipient or vice versa.
    """
    from .models import BlockedUser
    
    # Check if recipient blocked sender or sender blocked recipient
    return BlockedUser.objects.filter(
        Q(blocked_by=recipient, blocked_user=sender) | Q(blocked_by=sender, blocked_user=recipient)
    ).exists()


def can_message(sender, recipient):
    """
    Check if sender can send message to recipient.
    Returns tuple (can_send: bool, message: str)
    """
    from .models import BlockedUser
    
    # Check if either user blocked the other
    if BlockedUser.objects.filter(blocked_by=recipient, blocked_user=sender).exists():
        return False, "You have been blocked by this user."
    
    if BlockedUser.objects.filter(blocked_by=sender, blocked_user=recipient).exists():
        return False, "You have blocked this user."
    
    return True, "Can send message"
