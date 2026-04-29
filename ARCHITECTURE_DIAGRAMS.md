# Messaging System - Visual Architecture

## System Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    STUDENT CLUB MESSAGING SYSTEM                │
└─────────────────────────────────────────────────────────────────┘

┌─────────────┐                    ┌─────────────┐
│  Student A  │                    │  Student B  │
└──────┬──────┘                    └──────┬──────┘
       │                                   │
       │         Message Sent              │
       ├──────────────────────────────────►│
       │                                   │
       │  "You are stupid"                 │
       │                                   │
       └◄──────────────────────────────────┘
              Message Received

                    │
                    ▼
        ┌───────────────────────┐
        │  Content Check        │
        │  1. Not empty?        │
        │  2. Not blocked?      │
        │  3. Same club?        │
        └───────────┬───────────┘
                    │
        ┌───────────▼───────────┐
        │  Bad Words Filter     │
        │  ✓ Contains: "stupid" │
        └───────────┬───────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │  Add Warning          │
        │  warning_count = 1    │
        └───────────┬───────────┘
                    │
        ┌───────────▼───────────┐
        │  Check Count          │
        │  1/2 = Warn           │
        │  2/2 = Block          │
        └───────────┬───────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │  Notify User          │
        │  "1/2 warnings"       │
        └───────────────────────┘
```

## Database Relationships

```
┌────────────────┐
│    Student     │
├────────────────┤
│ id (PK)        │
│ user_id (FK)   │───┐
│ club_id (FK)   │   │
│ name           │   │
│ email          │   │
│ age            │   │
│ department     │   │
└────────────────┘   │
      ▲    ▲         │
      │    │         │
      │    └─────────┴──────────┐
      │                        User
      │                    (Django Auth)
    1:N  ┌──────────────────┐
      │  │    Message       │
      │  ├──────────────────┤
      │  │ sender_id (FK)   │──┐
      │  │ recipient_id(FK) │──┤
      │  │ content (TEXT)   │  │
      │  │ is_read (BOOL)   │  │
      │  │ contains_warning │  │
      │  │ created_at       │  │
      │  └──────────────────┘  │
      │                        │
      └────────────────────────┘

    1:N  ┌──────────────────┐
      │  │  UserWarning     │
      │  ├──────────────────┤
      │  │ student_id (FK)  │──┐
      │  │ warning_count    │  │
      │  │ reason (TEXT)    │  │
      │  │ created_at       │  │
      │  └──────────────────┘  │
      │                        │
      └────────────────────────┘

    N:N  ┌──────────────────┐
         │  BlockedUser     │
         ├──────────────────┤
         │ blocked_by_id(FK)│
         │ blocked_user_id  │
         │ reason           │
         │ created_at       │
         └──────────────────┘
```

## View Flow Chart

```
User visits /messages/conversations/
        │
        ▼
view_conversations()
        │
        ├─ Get all conversations for student
        ├─ Get latest message for each
        ├─ Check if blocked
        │
        ▼
Render: conversations.html
        │
        ├─ Show active conversations list
        ├─ Show "Start new conversation"
        │
        ▼
User clicks on a conversation
        │
        ▼
/messages/<recipient_id>/
        │
        ▼
message_thread()
        │
        ├─ Verify same club
        ├─ Check if blocked
        ├─ Get message history
        ├─ Mark unread as read
        │
        ▼
Display: message_thread.html
        │
        ├─ Show all messages (sender/recipient)
        ├─ Show message form
        ├─ Option to block user
        │
        ▼
User sends message
        │
        ▼
Form POST to same view
        │
        ├─ Extract content
        ├─ Check bad words: contains_bad_words()
        │
        ├─ If bad words found:
        │  ├─ Set flag: contains_warning=True
        │  ├─ Add warning: add_warning()
        │  ├─ Check count: should_block_user()
        │  │
        │  ├─ If warning_count >= 2:
        │  │  └─ Create BlockedUser
        │  │
        │  └─ Notify user
        │
        └─ Save message
            │
            ▼
        Reload page
```

## State Transitions for User

```
┌──────────────────┐
│  Normal User     │
│  Can Message     │
└────────┬─────────┘
         │
         │ Send message with bad words
         │
         ▼
┌──────────────────┐
│  Warned User     │
│  1/2 Warnings    │
│  Can still msg   │
└────────┬─────────┘
         │
         │ Send another bad message
         │
         ▼
┌──────────────────┐
│  Blocked User    │
│  2/2 Warnings    │
│  CANNOT MESSAGE  │
└──────────────────┘

Alternative:
┌──────────────────┐
│  Normal User     │
│  Can Message     │
└────────┬─────────┘
         │
         │ User clicks "Block User"
         │
         ▼
┌──────────────────┐
│  Blocked User    │
│  (Manual Block)  │
│  CANNOT MESSAGE  │
└──────────────────┘
```

## Message Warning Logic

```
Message Content: "You are stupid and trash"
        │
        ▼
Bad Words Check
        │
        ├─ "stupid" in BAD_WORDS? YES ───┐
        └─ "trash" in BAD_WORDS? YES ───┐
                                        │
                                        ▼
                        contains_bad_words() = True
                                        │
                                        ▼
                        mark: contains_warning = True
                                        │
                                        ▼
                        get_warning_count(student)
                        │
                        ├─ Query UserWarning table
                        ├─ Get latest record
                        └─ Return count (or 0 if none)
                                        │
                                        ▼
                        new_count = current + 1
                                        │
                                        ▼
                        add_warning(student, reason)
                        └─ Save new UserWarning record
                                        │
                                        ▼
                        should_block_user(new_count)?
                        │
                        ├─ If new_count >= 2: TRUE
                        └─ If new_count < 2: FALSE
                                        │
                        ┌───────────────┴───────────────┐
                        │                               │
                    FALSE                           TRUE
                        │                               │
                        ▼                               ▼
                  Show warning        Create BlockedUser
                  1/2 warnings                │
                                        Block user
                                        Show: BLOCKED!
```

## Permission Matrix

```
┌──────────────────┬──────────┬──────────┬──────────┐
│ Can Message?     │ Normal   │ Warned   │ Blocked  │
├──────────────────┼──────────┼──────────┼──────────┤
│ Same Club Member │ ✅ YES   │ ✅ YES   │ ❌ NO    │
│ Different Club   │ ❌ NO    │ ❌ NO    │ ❌ NO    │
│ Blocked By Them  │ ❌ NO    │ ❌ NO    │ ❌ NO    │
│ Blocked Them     │ ❌ NO    │ ❌ NO    │ ❌ NO    │
└──────────────────┴──────────┴──────────┴──────────┘
```

## URL Routing Flow

```
User Action                    URL Route                  View Function
──────────────────────────────────────────────────────────────────────

Click "Messages"        →    /messages/conversations/    →  view_conversations()
                                                              Display all convos

Click on user           →    /messages/<id>/             →  message_thread()
                                                              Show chat, form

Type & Send             →    POST /messages/<id>/        →  message_thread()
                                                              Process & save

Click "Block User"      →    POST /users/<id>/block/     →  block_user()
                                                              Create block

Click "Unblock"         →    POST /users/<id>/unblock/   →  unblock_user()
                                                              Delete block

Click "My Warnings"     →    /warnings/                  →  view_user_warnings()
                                                              Show warnings

Get users list          →    /messages/available-users/  →  get_available_users()
                                                              Return JSON

Send (AJAX)             →    POST /messages/<id>/send/   →  send_message()
                                                              Return JSON
```

## Admin Dashboard View

```
Django Admin (/admin/)
        │
        ├─ Messages
        │  ├─ View all messages
        │  ├─ Filter by sender/recipient
        │  ├─ Search by content
        │  └─ Delete inappropriate messages
        │
        ├─ User Warnings
        │  ├─ View all warnings
        │  ├─ Filter by student
        │  ├─ See warning count
        │  ├─ View reason for each
        │  └─ Add manual warnings
        │
        └─ Blocked Users
           ├─ View all blocks
           ├─ Filter by blocker/blocked
           ├─ See block reason
           └─ Remove blocks
```

## Component Interaction

```
┌──────────────────────────────────────────────────────────┐
│               Message Submission Flow                    │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────────┐                                   │
│  │   User Input     │                                   │
│  │  Message Form    │                                   │
│  └────────┬─────────┘                                   │
│           │                                             │
│           ▼                                             │
│  ┌──────────────────────────────────┐                  │
│  │    Views (message_thread)        │                  │
│  │  1. Extract content              │                  │
│  │  2. Call contains_bad_words()    │                  │
│  │  3. Check permissions            │                  │
│  └────────┬─────────────────────────┘                  │
│           │                                             │
│           ▼                                             │
│  ┌──────────────────────────────────┐                  │
│  │    Utilities (utils.py)          │                  │
│  │  1. contains_bad_words()         │                  │
│  │  2. add_warning()                │                  │
│  │  3. should_block_user()          │                  │
│  │  4. can_message()                │                  │
│  └────────┬─────────────────────────┘                  │
│           │                                             │
│           ▼                                             │
│  ┌──────────────────────────────────┐                  │
│  │   Models (models.py)             │                  │
│  │  1. Message.save()               │                  │
│  │  2. UserWarning.save()           │                  │
│  │  3. BlockedUser.save()           │                  │
│  └────────┬─────────────────────────┘                  │
│           │                                             │
│           ▼                                             │
│  ┌──────────────────────────────────┐                  │
│  │   Database                       │                  │
│  │  Message, UserWarning,           │                  │
│  │  BlockedUser Tables              │                  │
│  └──────────────────────────────────┘                  │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

## Feature Coverage

```
┌─────────────────────────────────────────────────────────┐
│           MESSAGING SYSTEM FEATURES                     │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ✅ Direct Messaging                                   │
│     └─ Same club members only                         │
│                                                         │
│  ✅ Message Storage                                    │
│     └─ Persistent database storage                    │
│                                                         │
│  ✅ Read Status                                        │
│     └─ Mark as read on view                           │
│                                                         │
│  ✅ Content Moderation                                 │
│     ├─ Bad words detection                            │
│     ├─ Automatic flagging                             │
│     └─ Customizable word list                         │
│                                                         │
│  ✅ Warning System                                     │
│     ├─ 1st violation = Warning                        │
│     ├─ 2nd violation = Block                          │
│     └─ Permanent records                              │
│                                                         │
│  ✅ User Blocking                                      │
│     ├─ Manual blocking                                │
│     ├─ Automatic blocking after 2 warnings           │
│     └─ Unblocking available                           │
│                                                         │
│  ✅ Admin Control                                      │
│     ├─ View all messages                              │
│     ├─ Monitor warnings                               │
│     ├─ Manage blocks                                  │
│     └─ Customize filter                               │
│                                                         │
│  ✅ User Interface                                     │
│     ├─ Conversations list                             │
│     ├─ Message thread view                            │
│     ├─ Warning display                                │
│     └─ Navigation integration                         │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

This visual guide shows how all components of the messaging system work together to provide a safe, moderated communication platform for students in clubs.
