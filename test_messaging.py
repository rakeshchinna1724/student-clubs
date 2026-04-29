from mainpage.utils import contains_bad_words, censor_bad_words

# Test normal message
print("Test 1 - Normal message:")
result = contains_bad_words("Hello, how are you?")
print(f"  'Hello, how are you?' contains bad words: {result}")
assert result == False, "Should be False"

# Test message with bad word
print("\nTest 2 - Message with bad word:")
result = contains_bad_words("You are stupid")
print(f"  'You are stupid' contains bad words: {result}")
assert result == True, "Should be True"

# Test case insensitivity
print("\nTest 3 - Case insensitivity:")
result = contains_bad_words("HATE speech")
print(f"  'HATE speech' contains bad words: {result}")
assert result == True, "Should be True"

# Test censoring
print("\nTest 4 - Word censoring:")
censored = censor_bad_words("You are stupid and trash")
print(f"  Original: 'You are stupid and trash'")
print(f"  Censored: '{censored}'")

print("\n✓ All bad word filter tests passed!")
