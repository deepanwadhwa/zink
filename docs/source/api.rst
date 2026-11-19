API reference
=============

The functions below are the public ``zink`` interface. ``categories`` specifies
entity labels; when omitted, the model uses ``person``, ``date`` and
``location``. Inference labels are converted to lowercase. An empty sequence
requests no labels.

Redaction and replacement
-------------------------

.. autofunction:: zink.redact

.. autofunction:: zink.replace

.. autofunction:: zink.replace_with_my_data

.. code-block:: python

   import zink

   note = "Alice attended the meeting."
   labels = ("person",)
   redacted = zink.redact(note, categories=labels, placeholder="[NAME]")
   synthetic = zink.replace(note, categories=labels)
   controlled = zink.replace_with_my_data(
       note, categories=labels, user_replacements={"person": "Participant A"},
   )
   print(redacted.anonymized_text, synthetic.anonymized_text, controlled.anonymized_text)

All three functions return a result with ``anonymized_text`` and metadata.
The optional pipeline components can be supplied as ``extractor``,
``merger``, and ``replacer``. See :class:`zink.pipeline.Pseudonymizer`
for their callable interfaces.

Protected text and mapping
--------------------------

.. autofunction:: zink.prep

.. autofunction:: zink.where_mapping_file

.. autofunction:: zink.refresh_mapping_file

.. code-block:: python

   import zink

   note = "Alice arrived early. Bob arrived later."
   prepared = zink.prep(note, ["Alice", "Alice arrived"])
   print(zink.redact(prepared, categories=("person",)).anonymized_text)
   print(zink.where_mapping_file())
   # Run this only when you intend to discard all stored placeholders:
   # zink.refresh_mapping_file()

Decorator
---------

.. autofunction:: zink.shield

.. code-block:: python

   import zink

   @zink.shield(target_arg=0, labels=("person",))
   def echo(note):
       return f"Received: {note}"

   print(echo("Alice is here."))

The wrapped function receives the redacted argument. Its string result
restores any recognized placeholders and can contain the original text.

Result objects
--------------

.. autoclass:: zink.result.PseudonymizationResult
   :members:

.. autoclass:: zink.result.ReplacementDetail
   :members:

The ``replacements`` field of a redaction result contains
``ReplacementDetail`` objects. Replacement results currently contain the
extractor's entity dictionaries instead; inspect ``anonymized_text`` for the
transformed text.

Pipeline components
-------------------

.. autoclass:: zink.pipeline.Pseudonymizer

.. autoclass:: zink.extractor.EntityExtractor

Passage processing
------------------

The low-level passage helpers return detections with offsets in the original
passage. Choose chunk boundaries carefully since splitting an entity can
prevent the model from recognizing it.

.. autofunction:: zink.passage_processors.chunk_text

.. autofunction:: zink.passage_processors.extract_entities_for_chunk

.. autofunction:: zink.passage_processors.extract_entities_in_parallel

.. code-block:: python

   from zink import passage_processors

   text = "Alice is here. Bob is away."
   print(passage_processors.chunk_text(text, chunk_size=15))
   print(passage_processors.extract_entities_for_chunk(
       "Bob is away.", offset=15, categories=("person",),
   ))
   print(passage_processors.extract_entities_in_parallel(
       text, chunk_size=15, categories=("person",),
   ))

HTTP API
--------

Install the CPU backend and optional server dependencies, then start the
server on your local machine.

.. code-block:: console

   pip install "zink[cpu,server]"
   uvicorn zink.server:app --host 127.0.0.1 --port 8000

``GET /health`` reports the server status and package version.
``POST /redact`` accepts ``text`` and optional ``labels``. The response
contains the original text, redacted text, and details of each redaction.
It still contains original sensitive text.

.. code-block:: console

   curl http://127.0.0.1:8000/health
   curl --json '{"text":"Alice is here.","labels":["person"]}' http://127.0.0.1:8000/redact
