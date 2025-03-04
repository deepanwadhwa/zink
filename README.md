# ZINK (Zero-shot Ink)

ZINK is a Python package designed for zero-shot anonymization of entities within unstructured text data. It allows you to redact or replace sensitive information based on specified entity labels.

## Description

In today's data-driven world, protecting sensitive information is paramount. ZINK provides a simple and effective solution for anonymizing text data by identifying and masking entities such as names, ages, phone numbers, medical conditions, and more. With ZINK, you can ensure data privacy while still maintaining the utility of your text data for analysis and processing.

ZINK leverages the power of zero-shot techniques, meaning it doesn't require prior training on specific datasets. You simply provide the text and the entity labels you want to anonymize, and ZINK handles the rest.

## Features

-   **Zero-shot anonymization:** No training data or pre-trained models required.
-   **Flexible entity labeling:** Anonymize any type of entity by specifying custom labels.
-   **Redaction and replacement:** Choose between redacting entities (replacing them with `[LABEL]_REDACTED`) or replacing them with a generic placeholder.
-   **Easy integration:** Simple and intuitive API for seamless integration into your Python projects.

## Installation

```bash
pip install zink
```
## Usage

### Redacting Entities
The redact function replaces identified entities with [LABEL]_REDACTED.

```bash
Python

import zink as pss

text = "John works as a doctor and plays football after work and drives a toyota."
labels = ("person", "profession", "sport", "car")
result = pss.redact(text, labels)
print(result.anonymized_text)
Example output:

person_REDACTED works as a profession_REDACTED and plays sport_REDACTED after work and drives a car_REDACTED.
```

### Replacing Entities
The replace function replaces identified entities with a random entity of the same type.

```bash
Python

import zink as pss

text = "John Doe dialled his mother at 992-234-3456 and then went out for a walk."
labels = ("person", "phone number", "relationship")
result = pss.replace(text, labels)
print(result.anonymized_text)
Example output:

Warren Buffet dialled his Uncle at 2347789287 and then went out for a walk.
```

Another example:

```bash
Python

import zink as pss

text = "Patient, 33 years old, was admitted with a chest pain"
labels = ("age", "medical condition")
result = pss.replace(text, labels)
print(result.anonymized_text)
Example output:

Patient, 78 years old, was admitted with a Diabetes Mellitus.
```

### Testing
To run the tests, navigate to the project directory and execute:

```bash
pytest
```

### Contributing
Contributions are welcome! Please feel free to submit pull requests or open issues to suggest improvements or report bugs.   

Fork the repository.
Create a new branch: git checkout -b feature/your-feature
Make your changes.
Commit your changes: git commit -m 'Add your feature'
Push to the branch: git push origin feature/your-feature
Submit a pull request.
License
This project is licensed under the Apache 2.0 License.