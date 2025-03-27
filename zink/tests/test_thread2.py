import zink

def punctuation_signature(text):
    """
    Returns a string containing only the punctuation characters from the text.
    This signature should remain unchanged after anonymization.
    """
    return "".join(ch for ch in text if ch in ".,;:?!")

# Sample text used in the tests.
sample_text = (
    "Alice was born on 1990-01-01 in Paris. "
    "Bob moved to New York in 2010. "
    "Charlie went to London in 2005."
)

def test_redact_preserves_structure():
    processed = zink.redact(sample_text, categories=("person", "date", "location"), placeholder="REDACTED", use_cache=True)
    orig_signature = punctuation_signature(sample_text)
    proc_signature = punctuation_signature(processed.anonymized_text)
    assert orig_signature == proc_signature, "Redact: Punctuation signature mismatch"

def test_replace_preserves_structure():
    processed = zink.replace(sample_text, categories=("person", "date", "location"), user_replacements=None, ensure_consistency=True, use_cache=True)
    orig_signature = punctuation_signature(sample_text)
    proc_signature = punctuation_signature(processed.anonymized_text)
    assert orig_signature == proc_signature, "Replace: Punctuation signature mismatch"

def test_replace_with_my_data_preserves_structure():
    user_replacements = {"person": "NAME", "date": "DATE", "location": "PLACE"}
    processed = zink.replace_with_my_data(sample_text, categories=("person", "date", "location"), user_replacements=user_replacements, ensure_consistency=True)
    orig_signature = punctuation_signature(sample_text)
    proc_signature = punctuation_signature(processed.anonymized_text)
    assert orig_signature == proc_signature, "Replace_with_my_data: Punctuation signature mismatch"

if __name__ == "__main__":
    test_redact_preserves_structure()
    test_replace_preserves_structure()
    test_replace_with_my_data_preserves_structure()
    print("All passage processor tests passed!")
