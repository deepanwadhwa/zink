from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class ReplacementDetail:
    """
    Details about the replacement of a sensitive entity.
    """
    label: str
    original: str
    pseudonym: str
    start: int
    end: int
    score: float  # average confidence, etc.


@dataclass
class PseudonymizationResult:
    """
    Result of the pseudonymization process.
    """
    original_text: str
    anonymized_text: str
    replacements: List[ReplacementDetail] = field(default_factory=list)
    features: Dict = field(default_factory=dict)
