# Messaging System - Technical Deep Dive

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Student Club Messaging                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐         ┌──────────────┐                  │
│  │  Student A  │◄────►   │  Student B   │                  │
│  └─────────────┘         └──────────────┘                  │
│         │                         │                         │
│         └─────────┬───────────────┘                        │
│                   │                                        │
│         ┌─────────▼──────────┐                            │
│         │  Message Model     │                            │
│         │  - sender          │                            │
│         │  - recipient       │                            │
│         │  - content         │                            │
│         │  - contains_warning│                            │
│         │  - is_read         │                            │
│         └────────┬───────────┘                            │
│                  │                                        │
│     ┌────────────┼────────────┐                          │
│     │            │            │                          │
│  ┌──▼──┐   ┌─────▼────┐   ┌──▼────────┐                │
│  │ BAD │   │ WARNING  │   │  BLOCKED  │                │
│  │WORDS│   │ SYSTEM   │   │   USER    │                │
│  │FILTER   │          │   │ SYSTEM    │                │
│  └──────┘   └──────────┘   └───────────┘                │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## Data Flow Diagram

### Sending a Message

```
User Types Message
        │
        ▼
Form Validation (not empty)
        │
        ▼
Check Block Status
    │         │
   YES       NO (can continue)
    │         │
    ▼         ▼
Error    Bad Words Check
         │         │
        YES       NO
         │         │
         ▼         ▼
    Add Warning   Save Message
      │           │
      ├─▶Flag Message
      │
    Warning Count?
      │         │
    1/2       2/2
      │         │
      ▼         ▼
    Notify  Block User
    (warn)    (block)
```

## Database Schema

### Message Table
```
┌─────────────────────┐
│      Message        │
├─────────────────────┤
│ id (PK)             │
│ sender_id (FK)      │──→ Student
│ recipient_id (FK)   │──→ Student
│ content (TEXT)      │
│ is_read (BOOL)      │
│ contains_warning    │
│ (BOOL)              │
│ created_at (DATETIME)
└─────────────────────┘
```

### UserWarning Table
```
┌──────────────────────┐
│    UserWarning       │
├──────────────────────┤
│ id (PK)              │
│ student_id (FK)      │──→ Student
│ warning_count (INT)  │ (1 or 2)
│ reason (TEXT)        │
│ created_at (DATETIME)│
└──────────────────────┘
```

### BlockedUser Table
```
┌──────────────────────┐
│    BlockedUser       │
├──────────────────────┤
│ id (PK)              │
│ blocked_by_id (FK)   │──→ Student
│ blocked_user_id (FK) │──→ Student
│ reason (TEXT)        │
│ created_at (DATETIME)│
│ UNIQUE: (blocked_by, │
│          blocked_user)
└──────────────────────┘
```

## Code Examples

### Example 1: Sending a Message

**User Action:** Student sends "You are stupid" to another student

**Code Flow:**
```python
# 1. View receives the form data
def message_thread(request, recipient_id):
    # ... 
    
    # 2. Extract message content
    content = "You are stupid"
    
    # 3. Check for bad words
    has_bad_words = contains_bad_words(content)
    # Returns: True (because "stupid" is in BAD_WORDS list)
    
    # 4. Create message
    message = Message.objects.create(
        sender=sender,
        recipient=recipient,
        content=content,
        contains_warning=True  # Flagged!
    )
    
    # 5. Process warning
    if has_bad_words:
        warning_count = add_warning(sender, "Sent message with inappropriate content")
        # Returns: 1 (first warning)
        
        # 6. Check if should block
        if should_block_user(warning_count):  # False (1 < 2)
            # Show warning message to user
            message = f'Warning {warning_count}/2. One more and you will be blocked.'
        else:
            # Block user
            BlockedUser.objects.create(
                blocked_by=recipient,
                blocked_user=sender
            )
            message = 'You have been BLOCKED.'
```

### Example 2: Checking if User Can Message

**Code:**
```python
def can_message(sender, recipient):
    # Check if recipient blocked sender
    if BlockedUser.objects.filter(
        blocked_by=recipient, 
        blocked_user=sender
    ).exists():
        return False, "You have been blocked by this user."
    
    # Check if sender blocked recipient
    if BlockedUser.objects.filter(
        blocked_by=sender, 
        blocked_user=recipient
    ).exists():
        return False, "You have blocked this user."
    
    return True, "Can send message"

# Usage
can_send, msg = can_message(student_a, student_b)
if not can_send:
    print(msg)  # "You have been blocked by this user."
```

### Example 3: Getting Bad Words

**Code:**
```python
def contains_bad_words(text):
    text_lower = text.lower()
    for word in BAD_WORDS:
        if word in text_lower:
            return True
    return False

# Examples:
contains_bad_words("Hello friend")  # False
contains_bad_words("You stupid person")  # True (contains "stupid")
contains_bad_words("This is racist")  # True (contains "racist")
contains_bad_words("HATE speech")  # True (case-insensitive, contains "hate")
```

## Warning System Logic

### Warning Counter Logic

```
User sends message with bad words
        │
        ▼
Get current warning count from database
        │
        ▼
Check latest UserWarning record
    │
    ├─ If exists: use warning_count
    └─ If not exists: use 0
        │
        ▼
New warning count = current + 1
        │
        ▼
Save new UserWarning record with new count
        │
        ├─ Record 1: warning_count = 1
        ├─ Record 2: warning_count = 2
        └─ Record 3: warning_count = 3 (if ever repeated)
        │
        ▼
Check: should_block_user(warning_count)
    │
    ├─ If 1 → No block (warn user)
    └─ If 2 → Block (automatic)
```

## Block System Logic

### Blocking Flow

```
User A wants to block User B
        │
        ▼
Create BlockedUser record:
    blocked_by = User A
    blocked_user = User B
        │
        ▼
Now when User B tries to message User A:
        │
        ├─ Check: BlockedUser.objects.filter(
        │        blocked_by=A, blocked_user=B)
        │        
        └─ Returns: True (blocked!)
            │
            ▼
    Can't send message error
```

### Checking Block Status

```python
# Check if either direction is blocked
blocked_by_recipient = BlockedUser.objects.filter(
    blocked_by=recipient,
    blocked_user=sender
).exists()

blocked_by_sender = BlockedUser.objects.filter(
    blocked_by=sender,
    blocked_user=recipient
).exists()

is_blocked = blocked_by_recipient or blocked_by_sender
```

## Message Display Logic

### Conversations List

```python
# Get all unique conversation partners
sent_to = Message.objects.filter(sender=student)\
    .values_list('recipient_id', flat=True)\
    .distinct()

received_from = Message.objects.filter(recipient=student)\
    .values_list('sender_id', flat=True)\
    .distinct()

# Combine into one set
conversation_ids = set(sent_to) | set(received_from)

# Get Student objects
conversations = Student.objects.filter(id__in=conversation_ids)

# For each, get latest message
for student in conversations:
    latest = Message.objects.filter(
        Q(sender=current_user, recipient=student) |
        Q(sender=student, recipient=current_user)
    ).order_by('-created_at').first()
```

## Performance Considerations

### Query Optimization

**Without Optimization (N+1 problem):**
```python
# Bad: queries database once per message!
conversations = Student.objects.filter(...)
for student in conversations:
    message = Message.objects.filter(...).first()  # ← N queries!
```

**With select_related/prefetch_related:**
```python
# Good: optimized queries
conversations = Student.objects.select_related('club', 'user').filter(...)
messages = Message.objects.filter(...).select_related('sender', 'recipient')
```

### Database Indexes

Consider adding indexes for frequently queried fields:
```python
class Message(models.Model):
    # ... fields ...
    class Meta:
        indexes = [
            models.Index(fields=['sender', 'recipient']),
            models.Index(fields=['recipient', 'is_read']),
        ]
```

## Testing Examples

### Test Case 1: Bad Word Detection

```python
from mainpage.utils import contains_bad_words

# Test cases
assert contains_bad_words("hello") == False
assert contains_bad_words("stupid person") == True
assert contains_bad_words("HATE") == True  # case-insensitive
assert contains_bad_words("abuse") == True
```

### Test Case 2: Warning Count

```python
from mainpage.utils import add_warning

student = Student.objects.get(id=1)
count1 = add_warning(student, "First bad message")
assert count1 == 1

count2 = add_warning(student, "Second bad message")
assert count2 == 2
```

### Test Case 3: Blocking

```python
from mainpage.models import BlockedUser

# Create block
BlockedUser.objects.create(
    blocked_by=user_a,
    blocked_user=user_b
)

# Check if blocked
assert BlockedUser.objects.filter(
    blocked_by=user_a,
    blocked_user=user_b
).exists() == True
```

## Configuration Options

### In settings.py (Future Enhancement)

```python
# Add to settings.py for customization
MESSAGING = {
    'WARNING_LIMIT': 2,  # Block after 2 warnings
    'ENABLE_BAD_WORD_FILTER': True,
    'ENABLE_PROFANITY_DETECTION': True,
    'MESSAGE_RETENTION_DAYS': None,  # Keep forever
    'MAX_MESSAGE_LENGTH': 5000,
    'RATE_LIMIT_MESSAGES_PER_MINUTE': 10,
}
```

## Common Issues & Solutions

### Issue: Message sent but not appearing

**Cause:** Is read flag issue or recipient didn't refresh

**Solution:** 
- Check if message exists in database
- Reload page
- Check Message model in admin

### Issue: User not blocked but can't message

**Cause:** Same club restriction

**Solution:**
- Check both users are in same club
- Can't message across clubs

### Issue: Warning not recorded

**Cause:** Bad word filter not triggered

**Solution:**
- Check the exact bad word spelling
- Check if word is in BAD_WORDS list
- Test contains_bad_words() function directly

## Migration Notes

When deploying new versions:

```bash
# 1. Create migrations
python manage.py makemigrations

# 2. Check migration
python manage.py sqlmigrate mainpage 0007

# 3. Apply migration
python manage.py migrate

# 4. Test
python manage.py test
```

## Monitoring & Analytics (Future)

Could add:
- Message count per user
- Warning frequency
- Block statistics
- Message volume by time
- Popular conversation patterns
