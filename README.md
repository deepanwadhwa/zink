[![PyPI version](https://badge.fury.io/py/zink.svg)](https://badge.fury.io/py/zink)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Run Python Tests](https://github.com/deepanwadhwa/zink/actions/workflows/python-tests.yaml/badge.svg)](https://github.com/deepanwadhwa/zink/actions/workflows/python-tests.yaml)
[![PyPI Downloads](https://static.pepy.tech/badge/zink)](https://pepy.tech/projects/zink)

<div align="center">
  <h1>ZINK (Zero-shot Ink)</h1>
</div>
ZINK is a Python package designed for zero-shot anonymization of entities within unstructured text data. It allows you to redact or replace sensitive information based on specified entity labels.

### Abstract

The proliferation of Large Language Models (LLMs) heightens challenges in protecting Personal Identifiable Information (PII), particularly Quasi-Identifiers (QIs), in unstructured text. QIs enable re-identification when combined and pose significant privacy risks, highlighted by their use in security verification. Current approaches face limitations: large LLMs offer flexibility for detecting diverse QIs but are often hindered by high computational costs, while traditional supervised NER models require domain-specific labeled data and fail to generalize to heterogeneous, unseen QI types. Furthermore, evaluating QI identification methods is hampered by the lack of diverse benchmarks. To address this need for evaluation resources, we present the Quasi-Identifier Benchmark (QIB), a new corpus with 1750 examples across 35 diverse QI categories (e.g., personal preferences, security answers) designed to assess model robustness against QI heterogeneity. To facilitate the application of flexible identification methods on such diverse data, we also introduce ZINK (Zero-shot INK), a Python package providing a unified framework for applying existing zero-shot NER models to QI identification and anonymization, simplifying model integration and offering configurable redaction and replacement.

Evaluation using ZINK on QIB shows strong performance, achieving an F4-score of 0.9206. This result outperforms both supervised models like BERT (0.6109) and paid large language models like GPT-4-Nano (0.9007), while remaining competitive with top-tier models like GPT-4 (0.9726). QIB and ZINK provide valuable resources enabling standardized evaluation and development of flexible, practical solutions for quasi-identifier anonymization in text.

## Installation

Install the package using `uv` or `pip`.

**CPU Support (Recommended for most users):**
```bash
uv add "zink[cpu]"
# or
pip install "zink[cpu]"
```

**GPU Support:**
```bash
pip install "zink[gpu]"
```

## Quick Start

Get started with ZINK in just a few lines of code. The `redact` function replaces identified entities with `[LABEL]_REDACTED`.

```python
import zink as zn

text = "John works as a doctor and plays football after work and drives a toyota."
labels = ("person", "profession", "sport", "car")

result = zn.redact(text, labels)
print(result.anonymized_text)
```

**Output:**
```text
person_REDACTED works as a profession_REDACTED and plays sport_REDACTED after work and drives a car_REDACTED.
```

## Key Features

### 1. Replacing Entities
Instead of simple redaction, you can replace entities with realistic synthetic data using the `replace` function. ZINK uses the Faker library to generate context-aware replacements.

```python
import zink as zn

text = "John Doe dialled his mother at 992-234-3456 and then went out for a walk."
labels = ("person", "phone number", "relationship")

result = zn.replace(text, labels)
print(result.anonymized_text)
```

**Possible Output:**
```text
Warren Buffet dialled his Uncle at 2347789287 and then went out for a walk.
```

### 2. Custom Replacements (Bring Your Own Data)
You can provide your own dictionary of replacements for specific labels. This is useful for consistent mapping or using domain-specific datasets.

```python
import zink as zn

text = "Melissa works at Google and drives a Tesla."
labels = ("person", "company", "car")
custom_replacements = {
    "person": "Alice",
    "company": "OpenAI",
    "car": ("Honda", "Toyota")
}

result = zn.replace_with_my_data(text, labels, user_replacements=custom_replacements)
print(result.anonymized_text)
```

**Possible Output:**
```text
Alice works at OpenAI and drives a Honda.
```

### 3. Shielding LLM and API Calls
Protect sensitive data in your RAG pipelines or API calls using the `@zink.shield` decorator. It automatically anonymizes inputs before they reach the function and re-identifies the output, creating a secure "shield" around your logic.

```python
import zink as zn

# This mock function simulates calling an external API (like OpenAI or Gemini)
@zn.shield(target_arg='prompt', labels=('person', 'company'))
def call_sensitive_api(prompt: str):
    # The prompt received here is already anonymized.
    # e.g., "Report for person_REDACTED from company_REDACTED."
    return f"Analysis for {prompt} is complete."

# The original, sensitive text
sensitive_data = "Report for John Doe from Acme Inc."

# Call the function normally. The decorator handles anonymization and re-identification.
final_result = call_sensitive_api(prompt=sensitive_data)

print(final_result)
```

**Output:**
```text
Analysis for John Doe from Acme Inc. is complete.
```

### 4. Persistent Entity Mapping
To ensure consistent redaction across multiple sessions or calls, you can use the `numbered_entities=True` flag. This will automatically use a persistent mapping file stored in your home directory (`~/.zink/mapping.json`).

```python
import zink as zn

# First call: Generates IDs and saves them to default mapping file
text1 = "My name is Alice."
result1 = zn.redact(text1, labels=["person"], numbered_entities=True)
print(result1.anonymized_text) 
# Output: person_1234_REDACTED ...

# Second call: Reuses the SAME ID for 'Alice'
text2 = "Alice is here again."
result2 = zn.redact(text2, labels=["person"], numbered_entities=True)
print(result2.anonymized_text)
# Output: person_1234_REDACTED ...

# Check where the mapping file is stored
print(zn.where_mapping_file())

# Clear the mapping file to start fresh
zn.refresh_mapping_file()
```

## Docker Support

You can run `zink` easily using Docker. The image comes with the model pre-installed and exposes a REST API.

### 1. Build the Image
Run this command in the root of the repository:
```bash
docker build -t zink .
```

### 2. Run the Container
Start the API server on port 8000:
```bash
docker run --rm -p 8000:8000 zink
```

> **Tip:** If port 8000 is already in use (e.g., you see a "Bind for 0.0.0.0:8000 failed" error), map it to a different port like 8001:
> ```bash
> docker run --rm -p 8001:8000 zink
> ```

### 3. Use the API
Once the container is running, you can send requests to the `/redact` endpoint.

**Example Request:**
```bash
curl -X POST "http://localhost:8000/redact" \
     -H "Content-Type: application/json" \
     -d '{"text": "John Doe lives in New York.", "labels": ["person", "location"]}'
```
*(Note: If you used port 8001, replace `localhost:8000` with `localhost:8001`)*

**Example Response:**
```json
{
  "original_text": "John Doe lives in New York.",
  "anonymized_text": "<PERSON> lives in <LOCATION>.",
  "replacements": [
    {
      "label": "person",
      "original": "John Doe",
      "pseudonym": "<PERSON>",
      "start": 0,
      "end": 8,
      "score": 0.99
    },
    {
      "label": "location",
      "original": "New York",
      "pseudonym": "<LOCATION>",
      "start": 18,
      "end": 26,
      "score": 0.99
    }
  ]
}
```

### Run Tests
To verify the installation, you can run the test suite inside the container:
```bash
docker run --rm zink pytest zink/tests
```

## How It Works

### [GLiNER](https://github.com/urchade/GLiNER)
GLiNER is a Named Entity Recognition (NER) model capable of identifying any entity type using a bidirectional transformer encoder (BERT-like). It provides a practical alternative to traditional NER models, which are limited to predefined entities, and Large Language Models (LLMs) that, despite their flexibility, are costly and large for resource-constrained scenarios.

### [NuNer](https://huggingface.co/numind/NuNER_Zero)
NuNerZero is a compact, zero-shot Named Entity Recognition model that leverages the robust GLiNER architecture for efficient token classification. It requires lower-cased labels and processes inputs as a concatenation of entity types and text, enabling it to detect arbitrarily long entities.

### [Faker](https://faker.readthedocs.io/) & Training Data
Zink leverages both the Faker library and the extensive training data from the GLiNER model to generate realistic, synthetic replacements for sensitive information.
- **GLiNER Training Data**: Access to thousands of label categories from the model's training set for diverse and accurate replacements.
- **Dynamic Data Generation**: Faker generates context-aware values (e.g., names, addresses).
- **Location Handling**: Swaps countries/cities with valid alternatives.
- **Date Replacement**: Handles various date formats intelligently.
- **Roles**: Differentiates between roles (e.g., doctor vs. patient) for appropriate naming.

## Benchmarks

Here is a comparison of ZINK against other models on Quasi Identifier Benchmark ([QIB])(https://huggingface.co/datasets/deepanwa/QIB)

| Model                  | Overall Recall | Overall Precision | Overall F4_SCORE | True Positives (TP) | False Negatives (FN) | Total Redaction Markers |
| :--------------------- | :------------- | :---------------- | :--------------- | :------------------ | :------------------- | :---------------------- |
| **gpt_41_nano** | 0.8971         | 0.962             | 0.9007           | 1570                | 180                  | 1632                    |
| **gpt_41** | 0.9726         | 0.9737            | 0.9726           | 1702                | 48                   | 1748                    |
| **zink_single** | 0.9            | 0.8858            | 0.8992           | 1575                | 175                  | 1778                    |
| **zink_topic** | 0.9126         | 0.6502            | 0.8914           | 1597                | 153                  | 2456                    |
| **zink_human (run 1)** | 0.9371         | 0.6597            | 0.9145           | 1640                | 110                  | 2486                    |
| **zink_human (run 2)** | 0.9446         | 0.6544            | 0.9206           | 1653                | 97                   | 2526                    |
| **tars_topic** | 0.5983         | 0.762             | 0.6059           | 1047                | 703                  | 1374                    |
| **bert** | 0.628          | 0.4255            | 0.6109           | 1099                | 651                  | 2583                    |

## Development

### Testing
To run the tests, navigate to the project directory and execute:
```bash
pytest
```

### Contributing
Contributions are welcome! Please feel free to submit pull requests or open issues to suggest improvements or report bugs.

1. Fork the repository.
2. Create a new branch: `git checkout -b feature/your-feature`
3. Make your changes.
4. Commit your changes: `git commit -m 'Add your feature'`
5. Push to the branch: `git push origin feature/your-feature`
6. Submit a pull request.

### Citation
If you are using this package for your work/research, use the below citation:
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.15035072.svg)](https://doi.org/10.5281/zenodo.15035072)

Wadhwa, D. (2025). ZINK: Zero-shot anonymization in unstructured text. (v0.2.1). Zenodo. https://doi.org/10.5281/zenodo.15035072

### License
This project is licensed under the Apache 2.0 License.