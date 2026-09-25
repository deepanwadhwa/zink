Related tools and package overlap
=================================

Zink's niche is a Python text workflow that combines user supplied, zero-shot
entity labels with redaction, synthetic replacement and optional persistent
placeholder mapping. It uses GLiNER with a NuNerZero ONNX model for extraction;
it does not introduce a new named entity recognition model.

.. list-table:: Related packages
   :header-rows: 1
   :widths: 18 36 46

   * - Package
     - Main approach
     - Relationship to Zink
   * - `PyRedactKit <https://github.com/brootware/PyRedactKit>`_
     - CLI redaction of several built-in structured types, with custom regular
       expressions and an unredact workflow.
     - Strong fit for known patterns and files. Zink accepts semantic labels
       at inference time for text entities that need not have a regular expression.
   * - `Microsoft Presidio <https://microsoft.github.io/presidio/>`_
     - Extensible detection and anonymization framework with recognizers,
       NLP integrations and multiple operators.
     - Broader, configurable platform. Zink offers a shorter path for trying
       arbitrary labels using its bundled zero-shot model; Presidio can also
       integrate ML recognizers, including GLiNER.
   * - `scrubadub <https://scrubadub.readthedocs.io/en/stable/>`_
     - Text cleaning with detectors, postprocessors and optional integrations.
     - Useful for supported detector types and localization. Zink exposes
       label driven model inference directly in its redaction API.
   * - `GLiNER <https://github.com/urchade/GLiNER>`_
     - Generalist named entity recognition for user specified labels.
     - Zink builds on GLiNER to apply redaction or synthetic replacement and
       manage placeholder mappings; GLiNER is the underlying extraction tool.

These are differences in interface and workflow, not evidence that Zink is
universally faster or more accurate. No comparable benchmark of these packages
is included here. For known formats, deterministic recognizers may be preferable;
for sensitive research text, validate recall on a representative, authorized
sample before relying on any tool.
