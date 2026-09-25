from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class ReplacementDetail:
    """One redacted span.

    Attributes:
        label (str): Predicted entity type.
        original (str): Source text detected at this span.
        pseudonym (str): Placeholder inserted into the output.
        start (int): Start offset in the text after exclusion markers are removed.
        end (int): Exclusive end offset in that text.
        score (float): Model confidence reported for the span.
    """
    label: str
    original: str
    pseudonym: str
    start: int
    end: int
    score: float  # average confidence, etc.


@dataclass
class PseudonymizationResult:
    """Text transformation and extraction metadata.

    Attributes:
        original_text (str): Input text, including exclusion markers if present.
        anonymized_text (str): Redacted or replaced output.
        replacements (list): ``ReplacementDetail`` objects for ``redact``;
            entity dictionaries for ``replace`` and ``replace_with_my_data``.
        features (dict): Counts and other metadata. Currently includes
            ``num_replacements``.
    """
    original_text: str
    anonymized_text: str
    replacements: List[ReplacementDetail] = field(default_factory=list)
    features: Dict = field(default_factory=dict)
