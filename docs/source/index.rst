.. Zink documentation master file, created by Sphinx.

==================================================
Zink: Zero-shot Ink
==================================================

**Zink** is a powerful Python library for **zero-shot entity anonymization**. It allows you to redact or replace sensitive information in unstructured text without the need for training data or pre-defined models.

.. image:: https://zenodo.org/badge/DOI/10.5281/zenodo.15035072.svg
   :target: https://doi.org/10.5281/zenodo.15035072
   :alt: DOI

-------------------

Introduction
============

Protecting sensitive data is critical. Zink simplifies this process by leveraging advanced zero-shot Named Entity Recognition (NER) models (GLiNER/NuNer) to identify and mask entities like names, locations, dates, and more on the fly.

**Key Features:**

*   **Zero-Shot**: No training required. Works out of the box with custom labels.
*   **Flexible**: Redact with placeholders or replace with realistic synthetic data (Faker).
*   **Privacy-First**: Run completely locally.
*   **Easy to Use**: Simple, intuitive API.

Installation
============

Zink requires Python 3.8+. To install, choose the version that matches your hardware:

**For CPU Users:**

.. code-block:: bash

    pip install "zink[cpu]"

**For GPU Users (CUDA):**

.. code-block:: bash

    pip install "zink[gpu]"

Quick Start
===========

Get started with redaction in just a few lines of code:

.. code-block:: python

    import zink as zn

    text = "John works at Google and drives a Toyota."
    labels = ("person", "company", "car")

    # Redact entities
    result = zn.redact(text, labels)
    print(result.anonymized_text)

**Output:**

.. code-block:: text

    person_REDACTED works at company_REDACTED and drives a car_REDACTED.

Usage Guide
===========

Redacting Entities
------------------

Use ``zn.redact`` to mask entities with a generic placeholder.

.. code-block:: python

    import zink as zn

    text = "Contact Alice at 555-0123."
    labels = ("person", "phone number")
    
    result = zn.redact(text, labels)
    print(result.anonymized_text)
    # Output: Contact person_REDACTED at phone number_REDACTED.

Replacing with Synthetic Data
-----------------------------

Use ``zn.replace`` to substitute entities with realistic fake data using Faker.

.. code-block:: python

    import zink as zn

    text = "Dr. Smith diagnosed the patient with Flu on Monday."
    labels = ("person", "medical condition", "date")
    
    result = zn.replace(text, labels)
    print(result.anonymized_text)
    # Possible Output: Dr. Johnson diagnosed the patient with Cold on Tuesday.

Excluding Words
---------------

Protect specific words from redaction by wrapping them in asterisks (``*``) or using ``zn.prep``.

**Using Asterisks:**

.. code-block:: python

    text = "I drive a *Toyota*."
    result = zn.redact(text, ("car",))
    print(result.anonymized_text)
    # Output: I drive a Toyota.

**Using ``zn.prep``:**

.. code-block:: python

    text = "I like Apple and Banana."
    # Protect 'Apple' from being redacted as a fruit/company
    prepared = zn.prep(text, ["Apple"]) 
    
    result = zn.redact(prepared, ("fruit", "company"))
    print(result.anonymized_text)
    # Output: I like Apple and fruit_REDACTED.

Custom Replacements
-------------------

Use ``zn.replace_with_my_data`` to supply your own dictionary of replacements.

.. code-block:: python

    custom_data = {
        "person": ["Alice", "Bob"],
        "city": ["New York", "London"]
    }
    
    text = "Charlie lives in Paris."
    result = zn.replace_with_my_data(text, ("person", "city"), user_replacements=custom_data)
    print(result.anonymized_text)
    # Output: Alice lives in New York.

How It Works
============

*   **GLiNER & NuNer**: Zink uses these state-of-the-art zero-shot NER models to identify entities based on semantic similarity to your labels.
*   **Faker**: For replacements, Zink integrates with the Faker library to generate context-aware synthetic data (e.g., replacing a name with another name, a date with a valid date).

API Reference
=============

For detailed class and function documentation, see the :doc:`api`.

.. toctree::
   :maxdepth: 2
   :hidden:

   api

Project Info
============

**License**: Apache 2.0

**Citation**:

.. code-block:: text

    Wadhwa, D. (2025). ZINK: Zero-shot anonymization in unstructured text. (v0.2.1). Zenodo. https://doi.org/10.5281/zenodo.15035072

**Contributing**:
Contributions are welcome! Please submit a Pull Request on GitHub.