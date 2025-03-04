Welcome to anonify!

# anonify

**anonify** is a Python library for anonymizing sensitive information in unstructured text. It can identify various entity types—like names, phone numbers, medical conditions, or even custom labels—and then **redact** or **replace** them with consistent, privacy-preserving placeholders.

## Key Features

- **Automatic Entity Detection**  
  Uses a pre-trained or rule-based Named Entity Recognition (NER) model to detect sensitive entities.

- **Redaction & Replacement**  
  - `redact(text, labels)` replaces matched entities with placeholders (e.g., `person_REDACTED`).  
  - `replace(text, labels)` swaps matched entities with realistic pseudonyms.

- **Consistency Control**  
  When using `replace`, each recognized entity can be mapped to a single pseudonym across the text, preserving coherence.

- **Customizability**  
  - Extend or override default label sets (e.g., `person`, `location`, `furniture`, etc.).  
  - Pass in your own user-defined replacements.  

- **LRU Cache (Optional)**  
  Speeds up repeated calls with the same input text and label sets.

## Installation

```bash
pip install anonify
