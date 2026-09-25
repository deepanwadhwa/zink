Zink documentation
==================

Zink detects text spans matching user supplied entity labels with a local
zero-shot named entity recognition model, then redacts or replaces those spans.
It is intended for preparing unstructured research text for analysis. Detection
is probabilistic: inspect the output before sharing sensitive data.

.. toctree::
   :maxdepth: 2

   tutorial
   api
   related-tools

Installation
------------

Zink requires Python 3.11 or newer. Choose one inference backend::

   pip install "zink[cpu]"

For a compatible CUDA environment, use ``pip install "zink[gpu]"`` instead.
The first use downloads the default NuNerZero ONNX model; subsequent inference
runs locally with the cached model. Installation and initial model download
therefore require network access.

Quick start
-----------

.. code-block:: python

   import zink

   result = zink.redact(
       "Alice works at Acme.",
       categories=("person", "company"),
   )
   print(result.anonymized_text)
   print(result.replacements)

Model predictions can vary with the text and labels. See the :doc:`tutorial`
for a research workflow and the :doc:`api` for exact parameters and results.
