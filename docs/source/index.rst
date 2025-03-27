.. Zink documentation master file, created by Sphinx.

====================
ZINK (Zero-shot Ink)
====================

ZINK is a Python package designed for zero-shot anonymization of entities within unstructured text data. It allows you to redact or replace sensitive information based on specified entity labels.

Update
------

With version >=0.4, we are moving from simple NER models to their onnx versions. I hope you enjoy the acceleration gains. The package will download the onnx version of the
underlying model(s) when you update.

Description
-----------

In today's data-driven world, protecting sensitive information is paramount. ZINK provides a simple and effective solution for anonymizing text data by identifying and masking entities such as names, ages, phone numbers, medical conditions, and more. With ZINK, you can ensure data privacy while still maintaining the utility of your text data for analysis and processing.

ZINK leverages the power of zero-shot techniques, meaning it doesn't require prior training on specific datasets. You simply provide the text and the entity labels you want to anonymize, and ZINK handles the rest.

Features
--------

* **Zero-shot anonymization:** No training data or pre-trained models required.
* **Flexible entity labeling:** Anonymize any type of entity by specifying custom labels.
* **Redaction and replacement:** Choose between redacting entities (replacing them with ``[LABEL]_REDACTED``) or replacing them with a generic placeholder.
* **Easy integration:** Simple and intuitive API for seamless integration into your Python projects.

Installation
------------

.. code-block:: bash

    pip install zink

Usage
-----

Redacting Entities
^^^^^^^^^^^^^^^^^^

The ``redact`` function replaces identified entities with ``[LABEL]_REDACTED``.

.. code-block:: python

    import zink as pss

    text = "John works as a doctor and plays football after work and drives a toyota."
    labels = ("person", "profession", "sport", "car")
    result = pss.redact(text, labels)
    print(result.anonymized_text)

Example output:

.. code-block:: text

    person_REDACTED works as a profession_REDACTED and plays sport_REDACTED after work and drives a car_REDACTED.

Replacing Entities
^^^^^^^^^^^^^^^^^^

The ``replace`` function replaces identified entities with a random entity of the same type.

.. code-block:: python

    import zink as pss

    text = "John Doe dialled his mother at 992-234-3456 and then went out for a walk."
    labels = ("person", "phone number", "relationship")
    result = pss.replace(text, labels)
    print(result.anonymized_text)

Possible output:

.. code-block:: text

    Warren Buffet dialled his Uncle at 2347789287 and then went out for a walk.

Another example:

.. code-block:: python

    import zink as pss

    text = "Patient, 33 years old, was admitted with a chest pain"
    labels = ("age", "medical condition")
    result = pss.replace(text, labels)
    print(result.anonymized_text)

Example output:

.. code-block:: text

    Patient, 78 years old, was admitted with a Diabetes Mellitus.

Replacing Entities with your own data
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This feature is for the scenario when you want to replace entities with your own dataset. Unlike the standard replace method, this function does not use caching and therefore accepts replacements as dictionaries directly, simplifying its use for dynamic or runtime-defined pseudonyms.

.. code-block:: python

    text = "Melissa works at Google and drives a Tesla."
    labels = ("person", "company", "car")
    custom_replacements = {
        "person": "Alice",
        "company": "OpenAI",
        "car": ("Honda", "Toyota")
        }

    result = zink.replace_with_my_data(text, labels, user_replacements=custom_replacements)

    print(result.anonymized_text)

Possible Output:

.. code-block:: text

    "Alice works at OpenAI and drives a Honda."

Under the hood
--------------

`GLiNER <https://github.com/urchade/GLiNER>`_
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

GLiNER is a Named Entity Recognition (NER) model capable of identifying any entity type using a bidirectional transformer encoder (BERT-like). It provides a practical alternative to traditional NER models, which are limited to predefined entities, and Large Language Models (LLMs) that, despite their flexibility, are costly and large for resource-constrained scenarios.

`NuNer <https://huggingface.co/numind/NuNER_Zero>`_
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

NuNerZero is a compact, zero-shot Named Entity Recognition model that leverages the robust GLiNER architecture for efficient token classification. It requires lower-cased labels and processes inputs as a concatenation of entity types and text, enabling it to detect arbitrarily long entities. Trained on the NuNER v2.0 dataset, NuNerZero achieves impressive performance, outperforming larger models like GLiNER-large-v2.1 by over 3% in token-level F1-score. This model is ideal for both research and practical applications where a streamlined, high-accuracy NER solution is essential.

`Faker <https://faker.readthedocs.io/>`_
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Zink now leverages the Faker library to generate realistic, synthetic replacements for sensitive information. This feature is relatively new and continues to evolve, enhancing our data masking capabilities while preserving contextual plausibility.

How Faker Is Utilized
~~~~~~~~~~~~~~~~~~~~~

Dynamic Data Generation
    Faker is used to generate replacement values for various entity types (e.g., names, addresses, dates). For example, when a human name is detected, Faker can provide a full name or first name based on context.

Country and Location Handling
    Our tool reads a list of country names (and their synonyms) from an external file. If a location entity matches one of these names, the system selects a different country from the list to mask the sensitive geographical data.

Date Replacement
    Date-related entities (such as dates, months, and days) are delegated to a dedicated strategy. For purely numeric dates (e.g., "12/02/1975"), the tool returns a Faker-generated date. For dates with explicit alphabetic month names, custom extraction and replacement logic is applied.

Human Entity Roles
    The system differentiates between various human roles (e.g., doctor, patient, engineer) using a predefined list of human entity roles. This allows for context-aware replacement, ensuring that names are replaced appropriately according to their role in the text.

Current Status and Future Improvements
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

New Feature in Beta
    The Faker integration is one of our latest features, designed to deliver more natural and contextually relevant data replacements. While the current implementation covers many common cases, it is still under active development.

Testing
-------

To run the tests, navigate to the project directory and execute:

.. code-block:: bash

    pytest

Citation
--------

If you are using this package for your work/research, use the below citation:

.. image:: https://zenodo.org/badge/DOI/10.5281/zenodo.15035072.svg
   :target: https://doi.org/10.5281/zenodo.15035072
   :alt: DOI

Wadhwa, D. (2025). ZINK: Zero-shot anonymization in unstructured text. (v0.2.1). Zenodo. https://doi.org/10.5281/zenodo.15035072

Contributing
------------

Contributions are welcome! Please feel free to submit pull requests or open issues to suggest improvements or report bugs.

#. Fork the repository.
#. Create a new branch: ``git checkout -b feature/your-feature``
#. Make your changes.
#. Commit your changes: ``git commit -m 'Add your feature'``
#. Push to the branch: ``git push origin feature/your-feature``
#. Submit a pull request.

License
-------

This project is licensed under the Apache 2.0 License.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   api