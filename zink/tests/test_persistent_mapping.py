import os
import json
import tempfile
import pytest
import zink as zn

def test_persistent_mapping_consistency():
    """
    Verifies that using a mapping file ensures consistent redaction across calls.
    """
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        mapping_file = tmp.name
    
    try:
        text1 = "My name is Alice and I work at Google."
        
        # First call: should generate new IDs and save to mapping file
        result1 = zn.redact(text1, categories=["person", "company"], numbered_entities=True, mapping_file=mapping_file)
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
        result2 = zn.redact(text1, categories=["person", "company"], numbered_entities=True, mapping_file=mapping_file)
        anonymized2 = result2.anonymized_text
        
        assert anonymized1 == anonymized2
        
        # Third call: new text with SAME entities, should use SAME IDs
        text2 = "Alice is a great engineer at Google."
        result3 = zn.redact(text2, categories=["person", "company"], numbered_entities=True, mapping_file=mapping_file)
        anonymized3 = result3.anonymized_text
        
        # Extract the IDs used in result1
        alice_id = mapping["person"]["Alice"]
        google_id = mapping["company"]["Google"]
        
        assert f"person_{alice_id}_REDACTED" in anonymized3
        assert f"company_{google_id}_REDACTED" in anonymized3

    finally:
        if os.path.exists(mapping_file):
            os.remove(mapping_file)

def test_persistent_mapping_new_entities():
    """
    Verifies that new entities are added to the existing mapping file.
    """
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        mapping_file = tmp.name
    
    try:
        # 1. Redact Alice
        zn.redact("Alice is here.", categories=["person"], numbered_entities=True, mapping_file=mapping_file)
        
        with open(mapping_file, 'r') as f:
            mapping = json.load(f)
            assert "Alice" in mapping["person"]
            assert "Bob" not in mapping.get("person", {})
            
        # 2. Redact Bob (new entity)
        zn.redact("Bob is here.", categories=["person"], numbered_entities=True, mapping_file=mapping_file)
        
        with open(mapping_file, 'r') as f:
            mapping = json.load(f)
            assert "Alice" in mapping["person"]
            assert "Bob" in mapping["person"]
            
    finally:
        if os.path.exists(mapping_file):
            os.remove(mapping_file)

def test_shield_with_mapping_file():
    """
    Verifies that @zn.shield works with mapping_file.
    """
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        mapping_file = tmp.name
        
    try:
        @zn.shield(target_arg='prompt', labels=('person',), mapping_file=mapping_file)
        def echo(prompt):
            return prompt
            
        # 1. Call with Alice
        out1 = echo(prompt="Alice is calling.")
        # The output of shield is RE-IDENTIFIED, so it should be the original text.
        # But we want to verify that the INTERMEDIATE step used the mapping file.
        # We can check the mapping file content.
        
        assert out1 == "Alice is calling."
        
        with open(mapping_file, 'r') as f:
            mapping = json.load(f)
            assert "Alice" in mapping["person"]
            alice_id = mapping["person"]["Alice"]
            
        # 2. Call with Alice again - should reuse ID (internal check)
        # Since we can't easily inspect the internal call without mocking, 
        # we rely on the fact that if it works, it didn't crash.
        # And if we use a DIFFERENT mapping file, we'd get a different ID, but here we want consistency.
        
        out2 = echo(prompt="Alice again.")
        assert out2 == "Alice again."
        
        # Verify mapping didn't change (ID should be same)
        with open(mapping_file, 'r') as f:
            mapping = json.load(f)
            assert mapping["person"]["Alice"] == alice_id

    finally:
        if os.path.exists(mapping_file):
            os.remove(mapping_file)
