import pytest

import zink as zn


@pytest.mark.integration
def test_pii_is_removed_during_call_and_restored_in_output():
    received = []

    @zn.shield(target_arg="prompt", labels=("person", "company"))
    def call(prompt):
        received.append(prompt)
        return f"Response generated for prompt: {prompt}"

    original = "A ticket was filed by Bob from Evil Corp."

    assert call(prompt=original) == f"Response generated for prompt: {original}"
    assert len(received) == 1
    assert "Bob" not in received[0] and "Evil Corp" not in received[0]
    assert "person_" in received[0] and "company_" in received[0]


@pytest.fixture
def detect_alice(fake_extractor):
    def predict(text, labels):
        assert tuple(labels) == ("person",)
        assert text == "Alice is here."
        return [
            {"start": 0, "end": 5, "text": "Alice", "label": "person", "score": 0.9}
        ]

    fake_extractor(predict)


@pytest.mark.parametrize("target", [1, "prompt"])
def test_shield_redacts_only_the_selected_argument(detect_alice, target):
    received = []

    def call(context, prompt):
        """Return a string containing the selected argument."""
        received.append((context, prompt))
        return prompt

    wrapped = zn.shield(target, labels=("person",))(call)
    if isinstance(target, int):
        result = wrapped("Alice stays in context", "Alice is here.")
    else:
        result = wrapped("Alice stays in context", prompt="Alice is here.")

    assert result == "Alice is here."
    [(context, prompt)] = received
    assert context == "Alice stays in context"
    assert "Alice" not in prompt and prompt.endswith("_REDACTED is here.")
    assert wrapped.__name__ == call.__name__
    assert wrapped.__doc__ == call.__doc__
    assert wrapped.__wrapped__ is call


def test_shield_requires_labels():
    with pytest.raises(ValueError, match="labels"):
        zn.shield("prompt")


def test_shield_rejects_negative_positional_index():
    with pytest.raises(ValueError, match="non-negative"):
        zn.shield(-1, labels=("person",))


@pytest.mark.parametrize("target", ["prompt", 1])
def test_shield_reports_a_missing_target(target):
    @zn.shield(target, labels=("person",))
    def call(*args, **kwargs):
        pytest.fail("The wrapped function ran without the target argument")

    with pytest.raises(ValueError, match="not found"):
        call("other")


def test_shield_rejects_a_non_string_target():
    @zn.shield("prompt", labels=("person",))
    def call(prompt):
        pytest.fail("The wrapped function ran with a non-string target")

    with pytest.raises(TypeError, match="must be a string"):
        call(prompt=42)


def test_shield_returns_non_string_results_by_identity(detect_alice):
    payload = {}

    @zn.shield(0, labels=("person",))
    def call(prompt):
        payload["received"] = prompt
        return payload

    result = call("Alice is here.")

    assert result is payload
    assert "Alice" not in result["received"]


def test_shield_preserves_exceptions_from_the_wrapped_function(detect_alice):
    error = ValueError("Original client error")

    @zn.shield(0, labels=("person",))
    def call(prompt):
        assert "Alice" not in prompt
        raise error

    with pytest.raises(ValueError) as caught:
        call("Alice is here.")

    assert caught.value is error
