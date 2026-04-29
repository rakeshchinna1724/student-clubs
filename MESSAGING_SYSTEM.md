# Student Club Messaging System - Implementation Guide

## Overview
A complete direct messaging system for students in the same club with built-in content moderation, warning system, and user blocking functionality.

## Features Implemented

### 1. **Direct Messaging Between Students**
- Students can send and receive direct messages with other members of their club
- Messages are stored in the database with timestamps
- Automatic marking of unread messages as read
- Clean, intuitive messaging interface

### 2. **Content Moderation System**
- **Bad Words Filter**: Messages containing inappropriate language are flagged
- **Warning System**: 
  - 1st warning: User gets a warning message (notified they have 1/2 warnings)
  - 2nd warning: User is automatically BLOCKED by the recipient
  - Users can view their warnings in a dedicated "My Warnings" page

- **Blocked User System**:
  - Users can manually block other users
  - Once blocked, the blocked user cannot send messages
  - Users can see if conversations are blocked
  - Users can unblock blocked users at any time

### 3. **Conversation Management**
- View list of all active conversations
- See latest message preview for each conversation
- See timestamp of last message
- Identify conversations that are blocked

### 4. **Message Features**
- Message content visibility (shows sender/recipient)
- Messages marked with appropriate indicator if they contain warning-triggering content
- Clean message threading with chronological order
- Auto-scroll to latest message

## Database Models

### Message Model
```python
- sender (ForeignKey to Student)
- recipient (ForeignKey to Student)
- content (TextField)
- is_read (Boolean)
- created_at (DateTime)
- contains_warning (Boolean) - flags if message had bad words
```

### UserWarning Model
```python
- student (ForeignKey to Student)
- warning_count (Integer) - tracks cumulative warnings
- reason (TextField) - reason for warning
- created_at (DateTime)
```

### BlockedUser Model
```python
- blocked_by (ForeignKey to Student)
- blocked_user (ForeignKey to Student)
- reason (TextField)
- created_at (DateTime)
- unique_together: (blocked_by, blocked_user)
```

## Views & URLs

### Available Routes:

1. **View Conversations**
   - URL: `/messages/conversations/`
   - View: `view_conversations`
   - Shows all active conversations

2. **Message Thread**
   - URL: `/messages/<recipient_id>/`
   - View: `message_thread`
   - Shows full chat history with a user

3. **Send Message (API)**
   - URL: `/messages/<recipient_id>/send/`
   - View: `send_message`
   - Handles message submission with validation

4. **Get Available Users (API)**
   - URL: `/messages/available-users/`
   - View: `get_available_users`
   - Returns JSON list of available users to message

5. **Block User**
   - URL: `/users/<user_id>/block/`
   - View: `block_user`
   - Blocks a user from messaging

6. **Unblock User**
   - URL: `/users/<user_id>/unblock/`
   - View: `unblock_user`
   - Removes block from a user

7. **View User Warnings**
   - URL: `/warnings/`
   - View: `view_user_warnings`
   - Shows all warnings received by current user

## Bad Words Filter

The system comes with a predefined list of inappropriate words in `utils.py`:

### Bad Words List Includes:
- abuse, aggressive, bully, damn, hate, idiot, jerk, kill
- stupid, suck, trash, useless, worthless
- harassment, racist, sexist, discriminate, threat, violence
- profanity, explicit, vulgar, obscene, inappropriate

### How to Customize:
Edit `mainpage/utils.py` and update the `BAD_WORDS` list:

```python
BAD_WORDS = [
    'word1', 'word2', 'word3',
    # Add more words as needed
]
```

## Utility Functions (utils.py)

### Key Functions:

1. **contains_bad_words(text)** - Checks if text contains bad words
2. **add_warning(student, reason)** - Adds a warning to a student, returns warning count
3. **should_block_user(warning_count)** - Returns True if user should be blocked (warning_count >= 2)
4. **is_user_blocked(sender, recipient)** - Checks if either user is blocked
5. **can_message(sender, recipient)** - Returns tuple (can_send: bool, message: str)

## User Workflow

### Sending a Message:
1. Go to "Messages" in the navigation
2. View active conversations or start a new one
3. Type your message and click "Send"
4. If message contains bad words:
   - Message is sent with a warning flag
   - User receives warning notification
   - If it's the 2nd warning, user is blocked

### Receiving Messages:
1. Go to "Messages" in navigation
2. Click on a conversation to open
3. Messages are auto-marked as read when viewing
4. Can see message history and send replies

### Managing Blocks:
1. Open a conversation
2. Click "Block User" button (top right)
3. Conversation becomes blocked
4. To unblock: Open "My Conversations", find blocked user, click "Unblock"

### Viewing Warnings:
1. Click "My Warnings" (from Message page or anywhere)
2. See all warnings received
3. See reason for each warning
4. See warning count (1/2 or 2/2)

## Admin Dashboard

All messaging data can be managed from Django Admin (`/admin/`):
- View all messages
- Monitor user warnings
- See blocked user relationships
- Delete inappropriate messages
- Manually add warnings to users

## Security Features

1. **Same Club Restriction**: Users can only message members of their own club
2. **Blocking System**: Prevents unwanted communication
3. **Warning System**: Discourages inappropriate behavior
4. **Content Filtering**: Automatically detects inappropriate content
5. **Admin Oversight**: All messages visible to admins

## Testing the System

### Test Scenario 1: Send a Normal Message
1. Login as Student A
2. Go to Messages
3. Select Student B
4. Type a normal message
5. Verify message appears for both

### Test Scenario 2: Test Bad Words Filter
1. Login as Student C
2. Go to Messages
3. Select Student D
4. Type a message with a bad word (e.g., "You are stupid")
5. Verify warning notification appears
6. Send another message with bad words
7. Verify user is blocked

### Test Scenario 3: Test Blocking
1. Login as Student E
2. Open conversation with Student F
3. Click "Block User"
4. Login as Student F
5. Try to send message to Student E
6. Verify message is blocked

## Templates Created

1. **conversations.html** - Main messaging hub showing all conversations
2. **message_thread.html** - Individual chat interface with a user
3. **user_warnings.html** - Display user warnings and blocking info

## Navigation Integration

Updated `base.html` navigation to include:
- 💬 Messages link (appears for all students)
- Link to view warnings on message pages

## Future Enhancements

Possible improvements:
1. Real-time messaging using WebSockets
2. Message search functionality
3. Group conversations/channels
4. Message reactions/emojis
5. File/image sharing in messages
6. Message encryption
7. Auto-expiring messages
8. Message forwarding
9. Message read receipts
10. Typing indicators

## Troubleshooting

### Messages not appearing?
- Ensure both users are in the same club
- Check if either user is blocked
- Clear browser cache

### Bad word filter too strict?
- Edit `BAD_WORDS` list in `utils.py`
- Remove overly broad terms
- Use more specific filtering

### Users still appearing in list when blocked?
- Check BlockedUser model in admin
- Ensure the block was created correctly
- Refresh the page

## Files Modified/Created

### New Files:
- `mainpage/utils.py` - Utility functions for messaging
- `mainpage/templates/mainpage/conversations.html`
- `mainpage/templates/mainpage/message_thread.html`
- `mainpage/templates/mainpage/user_warnings.html`
- `mainpage/migrations/0007_message_userwarning_blockeduser.py`

### Modified Files:
- `mainpage/models.py` - Added Message, UserWarning, BlockedUser models
- `mainpage/forms.py` - Added MessageForm
- `mainpage/views.py` - Added messaging views
- `studentclub/urls.py` - Added messaging URLs
- `mainpage/admin.py` - Registered messaging models
- `mainpage/templates/mainpage/base.html` - Added Messages navigation link

## Deployment Notes

When deploying to production:
1. Update `BAD_WORDS` list to match your community guidelines
2. Consider enabling message logging for compliance
3. Set up admin notifications for frequent warnings
4. Implement rate limiting on message API
5. Consider backup strategy for message data
6. Enable Django's security middleware
7. Use HTTPS for all connections
