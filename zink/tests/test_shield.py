import zink as zn

# This list will act as a "spy" to record the exact prompt our mock function receives.
prompt_history = []

@zn.shield(target_arg='prompt', labels=('person', 'company'))
def mock_llm_call_with_spy(prompt: str):
    """
    A mock LLM function that records the prompt it receives to our spy list.
    The 'prompt' argument here will be the anonymized version from the decorator.
    """
    print(f"DEBUG: Mock LLM received prompt: '{prompt}'") # For visualization
    prompt_history.append(prompt)
    return f"Response generated for prompt: {prompt}"


def test_pii_is_removed_during_call_and_restored_in_output():
    """
    Verifies that the @zn.shield decorator:
    1. Removes PII before calling the wrapped function.
    2. Restores the PII in the final returned string.
    """
    # 1. Arrange
    prompt_history.clear() # Ensure the spy list is empty before the test
    sensitive_input = "A ticket was filed by Bob from Evil Corp."
    pii_to_check = ["Bob", "Evil Corp"]
    expected_final_output = f"Response generated for prompt: {sensitive_input}"

    # 2. Act
    # Call the decorated function. This triggers the full anonymize -> call -> re-identify cycle.
    final_result = mock_llm_call_with_spy(prompt=sensitive_input)

    # 3. Assert
    # Phase 1: Verify Anonymization (Check what the mock LLM saw)
    assert len(prompt_history) == 1
    prompt_seen_by_llm = prompt_history[0]

    for pii in pii_to_check:
        assert pii not in prompt_seen_by_llm
    
    assert "person" in prompt_seen_by_llm
    assert "company" in prompt_seen_by_llm

    # Phase 2: Verify Re-identification (Check the final output)
    assert final_result == expected_final_output