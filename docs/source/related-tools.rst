Related tools
=============

Zink uses GLiNER with a NuNerZero ONNX model to find entities. It then applies
redaction or replacement. The table lists other packages that handle parts of
this workflow.

.. list-table:: Package comparison
   :header-rows: 1
   :widths: 20 40 40

   * - Package
     - Features
     - Zink comparison
   * - `PyRedactKit <https://github.com/brootware/PyRedactKit>`_
     - Command line redaction for built-in structured types and custom regular
       expressions. Supports unredaction.
     - Zink accepts entity labels at inference time to find spans in text.
   * - `Microsoft Presidio <https://microsoft.github.io/presidio/>`_
     - Detection and anonymization framework with recognizers, NLP
       integrations and replacement operators.
     - Zink provides a single API around its default zero-shot model.
       Presidio supports additional recognizers and operators.
   * - `scrubadub <https://scrubadub.readthedocs.io/en/stable/>`_
     - Text cleaning with configurable detectors and postprocessors.
     - Zink passes the requested entity labels to its model during redaction.
   * - `GLiNER <https://github.com/urchade/GLiNER>`_
     - Named entity recognition with user-specified labels.
     - Zink uses GLiNER for extraction and adds redaction, synthetic
       replacements and placeholder mapping.

The package has no benchmark against the tools in this table. Test detection
on samples from your data before using its output in a research workflow.
