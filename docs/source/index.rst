Zink documentation
==================

Zink finds text spans that match the entity labels you provide. It can redact
those spans or replace them with other values. It uses a local named entity
recognition model.

Quick start
-----------

1. Install Zink
~~~~~~~~~~~~~~~

Zink requires Python 3.11 or newer. For CPU use, run:

.. code-block:: console

   pip install "zink[cpu]"

For a compatible CUDA environment, run ``pip install "zink[gpu]"`` instead.
The model downloads when you first import Zink with an inference backend
installed. Later runs use the cached model.

2. Redact text
~~~~~~~~~~~~~~

.. code-block:: python

   import zink

   result = zink.redact(
       "Alice works at Acme.",
       categories=("person", "company"),
   )
   print(result.anonymized_text)

``categories`` lists the entity types to find. Detected spans are replaced
with placeholders such as ``person_REDACTED``. Model predictions vary with
the text and labels, so check the output before sharing it.

Next steps
----------

* :doc:`tutorial` shows redaction, custom replacements and consistent
  placeholders across texts.
* :doc:`api` lists the functions, parameters and result fields.
* :doc:`related-tools` compares Zink with other text redaction packages.

.. toctree::
   :hidden:
   :maxdepth: 2

   tutorial
   api
   related-tools
