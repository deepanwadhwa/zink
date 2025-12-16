import os
import json
import tempfile
import pytest
from unittest.mock import patch
import zink as zn

@pytest.fixture
def mock_mapping_file():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        mapping_file = tmp.name
    
    # Patch the path in all places where it is imported
    with patch('zink.zink.get_default_mapping_path', return_value=mapping_file), \
         patch('zink.pipeline.get_default_mapping_path', return_value=mapping_file), \
         patch('zink.utils.paths.get_default_mapping_path', return_value=mapping_file):
        yield mapping_file
        
    if os.path.exists(mapping_file):
        os.remove(mapping_file)

def test_persistent_mapping_consistency(mock_mapping_file):
    """
    Verifies that using implicit mapping ensures consistent redaction across calls.
    """
    mapping_file = mock_mapping_file
    
    text1 = "My name is Alice and I work at Google."
    
    # First call: should generate new IDs and save to mapping file
    result1 = zn.redact(text1, categories=["person", "company"], numbered_entities=True)
    anonymized1 = result1.anonymized_text
    
    assert "person_" in anonymized1
    assert "company_" in anonymized1
    
    # Verify mapping file exists and has content
    assert os.path.exists(mapping_file)
    with open(mapping_file, 'r') as f:
        mapping = json.load(f)
        assert "person" in mapping
        assert "Alice" in mapping["person"]
        assert "company" in mapping
        assert "Google" in mapping["company"]
        
    # Second call: same text, should produce IDENTICAL output
    result2 = zn.redact(text1, categories=["person", "company"], numbered_entities=True)
    anonymized2 = result2.anonymized_text
    
    assert anonymized1 == anonymized2
    
    # Third call: new text with SAME entities, should use SAME IDs
    text2 = "Alice is a great engineer at Google."
    result3 = zn.redact(text2, categories=["person", "company"], numbered_entities=True)
    anonymized3 = result3.anonymized_text
    
    # Extract the IDs used in result1
    alice_id = mapping["person"]["Alice"]
    google_id = mapping["company"]["Google"]
    
    assert f"person_{alice_id}_REDACTED" in anonymized3
    assert f"company_{google_id}_REDACTED" in anonymized3

def test_persistent_mapping_new_entities(mock_mapping_file):
    """
    Verifies that new entities are added to the existing mapping file.
    """
    mapping_file = mock_mapping_file
    
    # 1. Redact Alice
    zn.redact("Alice is here.", categories=["person"], numbered_entities=True)
    
    with open(mapping_file, 'r') as f:
        mapping = json.load(f)
        assert "Alice" in mapping["person"]
        assert "Bob" not in mapping.get("person", {})
        
    # 2. Redact Bob (new entity)
    zn.redact("Bob is here.", categories=["person"], numbered_entities=True)
    
    with open(mapping_file, 'r') as f:
        mapping = json.load(f)
        assert "Alice" in mapping["person"]
        assert "Bob" in mapping["person"]

def test_shield_with_implicit_mapping(mock_mapping_file):
    """
    Verifies that @zn.shield works with implicit mapping.
    """
    mapping_file = mock_mapping_file
        
    @zn.shield(target_arg='prompt', labels=('person',))
    def echo(prompt):
        return prompt
        
    # 1. Call with Alice
    out1 = echo(prompt="Alice is calling.")
    
    assert out1 == "Alice is calling."
    
    with open(mapping_file, 'r') as f:
        mapping = json.load(f)
        assert "Alice" in mapping["person"]
        alice_id = mapping["person"]["Alice"]
        
    # 2. Call with Alice again
    out2 = echo(prompt="Alice again.")
    assert out2 == "Alice again."
    
    # Verify mapping didn't change (ID should be same)
    with open(mapping_file, 'r') as f:
        mapping = json.load(f)
        assert mapping["person"]["Alice"] == alice_id

def test_refresh_mapping_file(mock_mapping_file):
    """
    Verifies that refresh_mapping_file deletes the mapping file.
    """
    mapping_file = mock_mapping_file
    
    # Create file by redacting something
    zn.redact("Alice is here.", categories=["person"], numbered_entities=True)
    assert os.path.exists(mapping_file)
    
    # Refresh
    zn.refresh_mapping_file()
    assert not os.path.exists(mapping_file)

def test_where_mapping_file(mock_mapping_file):
    """
    Verifies where_mapping_file returns the correct path.
    """
    assert zn.where_mapping_file() == mock_mapping_file
