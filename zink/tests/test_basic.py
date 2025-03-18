import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
import zink as psst

def test01():
    text = "John works as a doctor and plays football after work and drives a toyota."
    labels = ("person","profession","sport","car")
    q = psst.redact(text, labels)
    assert "John" not in q.anonymized_text and "doctor" not in q.anonymized_text and "football" not in q.anonymized_text and "toyota" not in q.anonymized_text
    
def test02():
    text = "Samantha is sitting on a french chair"
    labels = ("person","furniture")
    q = psst.redact(text, labels)
    print(q.anonymized_text)
    assert "person_REDACTED" in q.anonymized_text and "furniture_REDACTED" in q.anonymized_text

def test03():
    text = "Patient, 33 years old, was admitted with a chest pain"
    labels = ("age","medical condition")
    q = psst.replace(text, labels)
    assert "33 years old" not in q.anonymized_text and "chest pain" not in q.anonymized_text

def test04():
    text = "John Doe dialled his mother at 992-234-3456 and then went out for a walk."
    labels = ("person","phone number","relationship")
    q = psst.replace(text, labels)
    assert "John Doe" not in q.anonymized_text and "992-234-3456" not in q.anonymized_text and "mother" not in q.anonymized_text

def test05():
    text = "Melissa is a software engineer at Google and she drives a Tesla. She is 29 years old."
    labels = ("person", "profession", "company", "car", "age")
    my_data = {
        "person": "Alice",
        "profession": "Data Scientist",
        "company": "Amazon",
        "car": "Honda",
        "age": "35"
    }

    q = psst.replace_with_my_data(text, labels, user_replacements=my_data)

    # Check original sensitive data is not present
    for original in ["Melissa", "software engineer", "Google", "Tesla", "29 years old"]:
        assert original not in q.anonymized_text, f"'{original}' was not replaced!"

    # Optionally check that replacements are correctly inserted
    for replacement in my_data.values():
        if isinstance(replacement, (list, tuple)):
            assert any(rep in q.anonymized_text for rep in replacement), "Replacement not found in anonymized text."
        else:
            assert replacement in q.anonymized_text, f"Replacement '{replacement}' missing."

    print("test05 passed successfully.")

def test06():
    # Test a purely numeric date – no explicit month name,
    # so DateReplacementStrategy should simply return a faker.date()
    text = "The meeting is scheduled on 10/22/2020 at the main office."
    labels = ("date",)
    q = psst.replace(text, labels)
    # Ensure that the original numeric date is removed and replaced by a new date format (e.g., with hyphens)
    assert "10/22/2020" not in q.anonymized_text and "-" in q.anonymized_text, "Numeric date not replaced properly"


def test07():
    # Test a sentence with two human names in a medical context.
    # The human_entity_roles logic should replace both names.
    text = "Dr. John Doe operated on patient Peter Baxter."
    labels = ("person",)
    q = psst.replace(text, labels)
    # Check that both names have been replaced (i.e. original names do not appear)
    assert "John Doe" not in q.anonymized_text and "Peter Baxter" not in q.anonymized_text, \
           "One or both human names were not replaced"


def test08():
    # Test a location where the text is a country (using countries_data via file).
    text = "The conference was held in Japan."
    labels = ("location",)
    q = psst.replace(text, labels)
    # Ensure "Japan" is not present; it should be replaced by another country
    assert "japan" not in q.anonymized_text.lower(), "Country name 'Japan' was not replaced"


def test09():
    # Test combined labels: person and location.
    text = "Alice, the engineer, from United States of America, called her friend."
    labels = ("person", "location")
    q = psst.replace(text, labels)
    # Check that "Alice" is replaced and that the country (or its synonyms) is replaced
    assert "alice" not in q.anonymized_text.lower() and "united states" not in q.anonymized_text.lower(), \
           "Either the person or location was not replaced properly"


def test10():
    # Test a multi-label scenario including a date, to exercise delegation to DateReplacementStrategy.
    text = "Dr. Michael, a cardiologist from Canada, was born on 07/04/1970."
    labels = ("person", "profession", "location", "date")
    q = psst.replace(text, labels)
    # Check that sensitive elements are removed from the anonymized text.
    for original in ["Dr. Michael", "cardiologist", "Canada", "07/04/1970"]:
        assert original.lower() not in q.anonymized_text.lower(), f"'{original}' was not replaced!"

def test11():
    text = "John, who is from Japan moved to the USA last month. u"
    labels = ("name", "location")
    q = psst.replace(text, labels)
    # Check that the original name and locations do not appear.
    assert "john" not in q.anonymized_text.lower(), "Original name 'John' found"
    assert "japan" not in q.anonymized_text.lower(), "Original location 'Japan' found"
    assert "usa" not in q.anonymized_text.lower(), "Original location 'USA' found"
    print("test12 passed:", q.anonymized_text)

def test12():
    text = "John riggins, who is from Japan moved to the USA last month. u"
    labels = ("name", "location")
    q = psst.replace(text, labels)
    # Ensure that both first and last names are replaced.
    assert "john" not in q.anonymized_text.lower(), "Original name 'John' found"
    assert "riggins" not in q.anonymized_text.lower(), "Original surname 'riggins' found"
    # Ensure that the locations are replaced.
    assert "japan" not in q.anonymized_text.lower(), "Original location 'Japan' found"
    assert "usa" not in q.anonymized_text.lower(), "Original location 'USA' found"
    print("test13 passed:", q.anonymized_text)
