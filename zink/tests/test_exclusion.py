import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import zink as zn

class TestExclusion(unittest.TestCase):
    def test_basic_exclusion(self):
        text = "I drive a *toyota* car."
        labels = ("car",)
        q = zn.redact(text, labels)
        # "toyota" should be preserved because it's wrapped in *
        self.assertIn("toyota", q.anonymized_text)
        # The * markers should be removed in the final output
        self.assertNotIn("*toyota*", q.anonymized_text)
        self.assertEqual("I drive a toyota car.", q.anonymized_text)

    def test_multiple_exclusions(self):
        text = "I like *apple* and *banana*."
        labels = ("fruit",) # Assuming fruit is a valid label or just testing mechanism
        # Even if "apple" and "banana" are not entities, the * should be stripped
        q = zn.redact(text, labels)
        self.assertIn("apple", q.anonymized_text)
        self.assertIn("banana", q.anonymized_text)
        self.assertNotIn("*", q.anonymized_text)

    def test_prep_function(self):
        text = "I drive a rav4, i like toyota cars."
        words = ["toyota"]
        prepared_text = zn.prep(text, words)
        self.assertEqual(prepared_text, "I drive a rav4, i like *toyota* cars.")

    def test_integration_prep_redact(self):
        text = "I drive a rav4, i like toyota cars."
        # rav4 should be redacted, toyota should be kept
        prepared_text = zn.prep(text, ["toyota"])
        labels = ("car",)
        q = zn.redact(prepared_text, labels)
        
        self.assertNotIn("rav4", q.anonymized_text)
        self.assertIn("toyota", q.anonymized_text)
        self.assertNotIn("*", q.anonymized_text)

    def test_exclusion_with_punctuation(self):
        text = "I like *toyota*, it is good."
        labels = ("car",)
        q = zn.redact(text, labels)
        self.assertIn("toyota", q.anonymized_text)
        self.assertNotIn("*", q.anonymized_text)
        self.assertEqual("I like toyota, it is good.", q.anonymized_text)

    def test_no_exclusion(self):
        text = "I drive a toyota."
        labels = ("car",)
        q = zn.redact(text, labels)
        self.assertNotIn("toyota", q.anonymized_text)

if __name__ == '__main__':
    unittest.main()
