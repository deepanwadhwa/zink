import sys
import warnings
import os
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from importlib import import_module
from importlib.util import find_spec
from threading import Lock


_BACKEND_ERROR = (
    "Zink inference dependencies are unavailable. Install 'zink[cpu]' or "
    "'zink[gpu]' to use redaction and replacement."
)
_UNINITIALIZED = object()
DEFAULT_MODEL = "deepanwa/NuNerZero_onnx"
DEFAULT_MODEL_REVISION = "40349bb15d985ced384bed5c35115fd70069f4b9"


def _backend_available():
    # Check module availability without importing GLiNER, Torch, or ONNX Runtime.
    return all(
        sys.modules[name] is not None
        if name in sys.modules
        else find_spec(name) is not None
        for name in ("gliner", "onnxruntime")
    )


if not _backend_available():
    warnings.warn(
        f"{_BACKEND_ERROR} Base-package utilities remain available.",
        RuntimeWarning,
        stacklevel=2,
    )


def _mask_spans(characters, entities):
    for entity in entities:
        for index in range(entity["start"], entity["end"]):
            characters[index] = " "


def _predict_label_chunk(model, text, labels):
    first_pass = model.predict_entities(text=text, labels=labels, threshold=0.5)
    characters = list(text)
    _mask_spans(characters, first_pass)
    second_pass = model.predict_entities(
        text="".join(characters), labels=labels, threshold=0.9
    )
    return first_pass + second_pass


def _best_entities(chunk_predictions):
    best_by_span = {}
    for predictions in chunk_predictions:
        for entity in predictions:
            span = (entity["start"], entity["end"])
            previous = best_by_span.get(span)
            if previous is None or entity["score"] > previous["score"]:
                best_by_span[span] = entity
    return sorted(best_by_span.values(), key=lambda entity: entity["start"])


class EntityExtractor:
    """Detect entities using a GLiNER ONNX model loaded on first use.

    Args:
        model_name (str): Hugging Face model identifier or local model directory.
        model_revision (str, optional): Model revision. Defaults to the pinned
            revision for the built-in model and the repository default for
            other model identifiers.

    The extractor reuses its model across requests. Text, label batches, and
    masks belong to each call. The backend must allow concurrent predictions
    when callers use threaded extraction.
    """

    def __init__(self, model_name=DEFAULT_MODEL, model_revision=None):
        self.model_name = model_name
        if model_revision is None and model_name == DEFAULT_MODEL:
            model_revision = DEFAULT_MODEL_REVISION
        self.model_revision = model_revision
        self.labels = ["person", "date", "location"]
        self._model = _UNINITIALIZED
        self._model_lock = Lock()

    @property
    def model(self):
        """Return the initialized model, or None if inference packages are absent.

        Concurrent calls share one successful initialization. A failed model
        load leaves the extractor uninitialized so a later call can retry.
        """
        if self._model is _UNINITIALIZED:
            with self._model_lock:
                if self._model is _UNINITIALIZED:
                    if not _backend_available():
                        return None
                    try:
                        import_module("onnxruntime")
                        from gliner import GLiNER
                    except ImportError as exc:
                        raise ImportError(_BACKEND_ERROR) from exc

                    self._model = GLiNER.from_pretrained(
                        self.model_name,
                        revision=self.model_revision,
                        load_onnx_model=True,
                        load_tokenizer=True,
                        local_files_only=os.environ.get(
                            "HF_HUB_OFFLINE", os.environ.get("TRANSFORMERS_OFFLINE", "")
                        ).upper()
                        in {"1", "ON", "YES", "TRUE"},
                    )
        return self._model

    @model.setter
    def model(self, model):
        with self._model_lock:
            self._model = model

    def _require_model(self):
        model = self.model
        if model is None:
            raise ImportError(_BACKEND_ERROR)
        return model

    def _normalize_labels(self, labels):
        if labels is None:
            return self.labels
        return [label.lower() for label in labels]

    def predict(self, text, labels=None, max_passes=2):
        """Return detected spans in text order, masking prior matches between passes.

        Args:
            text (str): Input text. Offsets refer to its Python characters.
            labels (sequence of str, optional): Entity labels. Defaults to
                person, date, and location.
            max_passes (int): Maximum number of model passes over the text.
        """
        predict_labels = self._normalize_labels(labels)
        if not predict_labels or max_passes <= 0:
            return []

        model = self._require_model()
        entities = []
        processed_spans = set()
        characters = list(text)
        for pass_number in range(max_passes):
            current_text = "".join(characters)
            if pass_number == 0:
                candidates = model.predict_entities(current_text, predict_labels)
            else:
                candidates = model.predict_entities(
                    current_text, predict_labels, threshold=0.9
                )

            new_entities = []
            for entity in candidates:
                span = (entity["start"], entity["end"])
                if span not in processed_spans:
                    processed_spans.add(span)
                    new_entities.append(entity)
            if not new_entities:
                break
            entities.extend(new_entities)
            _mask_spans(characters, new_entities)

        return sorted(entities, key=lambda entity: entity["start"])

    def predict_thorough(self, text, labels=None):
        """Run two passes per batch of three labels, processing batches in order.

        For each span, return the highest-scoring prediction across label
        batches. The result is sorted by the span's starting offset.
        """
        predict_labels = self._normalize_labels(labels)
        if not predict_labels:
            return []

        model = self._require_model()
        return _best_entities(
            _predict_label_chunk(model, text, predict_labels[index : index + 3])
            for index in range(0, len(predict_labels), 3)
        )

    def predict2(self, text, labels=None):
        """Run two passes per batch of two labels using a shared model and threads.

        Return the highest-scoring prediction for each span in text order.
        Workers mask a private copy of this call's text for their second pass.
        """
        predict_labels = self._normalize_labels(labels)
        if not predict_labels:
            return []

        model = self._require_model()
        label_chunks = [
            predict_labels[index : index + 2]
            for index in range(0, len(predict_labels), 2)
        ]
        predict_chunk = partial(_predict_label_chunk, model, text)
        with ThreadPoolExecutor(max_workers=4) as executor:
            return _best_entities(executor.map(predict_chunk, label_chunks))


_DEFAULT_EXTRACTOR = EntityExtractor()
