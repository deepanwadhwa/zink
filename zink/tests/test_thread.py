import re
from zink.passage_processor import redact, replace, replace_with_my_data

def punctuation_signature(text):
    """
    Returns a string containing only the punctuation characters from the text.
    This signature should remain unchanged after anonymization.
    """
    return "".join(ch for ch in text if ch in ".,;:?!")

def test_redact():
    with open("zink/tests/data/sample.txt", "r", encoding="utf-8") as file:
        original_text = file.read()
    # Process the text using redact.
    processed = redact(original_text, categories=("person", "date", "location"), placeholder="REDACTED", use_cache=False)
    # Compute punctuation signatures.
    orig_sig = punctuation_signature(original_text)
    proc_sig = punctuation_signature(processed)
    assert orig_sig == proc_sig, "Redact: Combined punctuation signature mismatch"
    print("test_redact passed")

def test_replace():
    with open("zink/tests/data/sample.txt", "r", encoding="utf-8") as file:
        original_text = file.read()
    # Process the text using replace.
    processed = replace(original_text, categories=("person", "date", "location"), user_replacements=None, ensure_consistency=True, use_cache=False)
    # Compute punctuation signatures.
    orig_sig = punctuation_signature(original_text)
    proc_sig = punctuation_signature(processed)
    assert orig_sig == proc_sig, "Replace: Combined punctuation signature mismatch"
    print("test_replace passed")

def test_replace_with_my_data():
    with open("zink/tests/data/sample.txt", "r", encoding="utf-8") as file:
        original_text = file.read()
    user_replacements = {"person": "NAME", "date": "DATE", "location": "PLACE"}
    # Process the text using replace_with_my_data.
    processed = replace_with_my_data(original_text, categories=("person", "date", "location"), user_replacements=user_replacements, ensure_consistency=True)
    # Compute punctuation signatures.
    orig_sig = punctuation_signature(original_text)
    proc_sig = punctuation_signature(processed)
    assert orig_sig == proc_sig, "Replace_with_my_data: Combined punctuation signature mismatch"
    print("test_replace_with_my_data passed")

if __name__ == "__main__":
    test_redact()
    test_replace()
    test_replace_with_my_data()
    print("All passage processor tests passed!")
