# Messaging System - Quick Reference Guide

## For Students

### How to Start Messaging

1. **Click "💬 Messages"** in the top navigation bar
2. You'll see:
   - **Active Conversations** - chats you've already started
   - **Start a New Conversation** - list of club members you can message

### Sending Your First Message

1. From Messages page, select a club member
2. Type your message in the text area
3. Click "Send"
4. Message appears immediately in the conversation

### Rules for Messaging

✅ **DO:**
- Be respectful and kind
- Use appropriate language
- Communicate clearly
- Report problems to club admins

❌ **DON'T:**
- Use profanity or bad language
- Send harassment or abuse
- Send hate speech or discrimination
- Bully or threaten other members

### What Happens If You Break Rules?

**1st Offense (Bad Message):**
- You get a ⚠️ Warning
- You can still message (1/2 warnings)
- See your warnings at `/warnings/`

**2nd Offense (Another Bad Message):**
- You're automatically BLOCKED by that user
- That user can't receive messages from you anymore
- You're marked as flagged (2/2 warnings)

### Managing Conversations

**Block a User:**
1. Open conversation with that person
2. Click "Block User" button (top right)
3. You won't see their messages

**Unblock a User:**
1. Go to Messages page
2. Find the blocked user
3. Click "Unblock User"

### Checking Your Warnings

1. Go to Messages page
2. Click "My Warnings" button
3. See all warnings received
4. Understand what triggered each warning

### Can't Send a Message?

Possible reasons:
- ❌ You're blocked by that user
- ❌ You've been blocked for bad behavior (2 warnings)
- ❌ That person blocked you
- ❌ Different clubs can't message each other (same club only)

**Solution:** Contact club admin if you believe it's a mistake

---

## For Club Admins

### Monitoring Messages (Django Admin)

1. Go to `/admin/` (admin login required)
2. Click "Messages" to see all messages
3. Click "User warnings" to monitor behavior
4. Click "Blocked users" to see relationship issues

### Managing Bad Behavior

**From Admin Panel:**
1. Find the problematic user in "User warnings"
2. See their warning count
3. Can manually add warnings if needed
4. Can create blocks if necessary

### Troubleshooting for Admins

**Issue: Student says they can't message someone**
- Check "Blocked users" - see if there's a block
- Check "Messages" - verify messages exist
- Check "User warnings" - see if user is flagged

**Issue: Inappropriate messages**
1. Go to Messages in admin
2. Find the message
3. Review content
4. Check if warning was issued
5. Can delete message if needed
6. Consider adding manual warning

**Issue: False positives in word filter**
- Admin can modify `BAD_WORDS` list in `utils.py`
- Remove overly broad filter terms
- Contact developer to adjust filtering

### Customizing Bad Words Filter

**To add or remove words:**
1. Open: `mainpage/utils.py`
2. Find: `BAD_WORDS` list
3. Add or remove words as needed
4. Restart Django server

Example:
```python
BAD_WORDS = [
    'abuse', 'aggressive', 'bully',  # existing
    'myword',  # add new word
    # 'unwantedword',  # remove by commenting out
]
```

---

## Quick Statistics

### About the Warning System
- **2 Warnings = Automatic Block** - No human intervention needed
- **Warnings expire?** No - warnings are permanent records
- **Can unblock own blocks?** Yes - users can unblock users they blocked
- **Can users unblock themselves?** No - if someone blocked them for bad behavior, they stay blocked

### About Messaging Restrictions
- Students can only message **same club members**
- Admins cannot message (only students)
- Messages are **permanent** (unless deleted by admin)
- Messages marked if they had inappropriate content

---

## Common Questions

**Q: Can I delete my messages?**
A: No - students can't delete. Only admins can. Message history is permanent.

**Q: Can I see who blocked me?**
A: No - you see "blocked" but not who did it. You'll be notified if you try to message them.

**Q: What if I get 2 warnings by mistake?**
A: Contact your club admin - they can remove the warning in admin panel.

**Q: Can I message people from other clubs?**
A: No - you can only message people in your own club.

**Q: What words trigger a warning?**
A: See `BAD_WORDS` list in MESSAGING_SYSTEM.md - includes profanity, harassment terms, hate speech, etc.

**Q: Can admins message students?**
A: Currently no - only students can message each other.

---

## Accessing Messaging

**URL Routes:**
- Messages Hub: `/messages/conversations/`
- Chat with User: `/messages/<user_id>/`
- My Warnings: `/warnings/`

**Navigation:**
- Look for "💬 Messages" in top menu (students only)
- Click to access your conversations
