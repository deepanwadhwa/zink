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

.. _replacement-consistency-versions:

Replacement consistency across versions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In v0.7.1 and v0.7.2, ``ensure_consistency=True`` reuses the first replacement
for exact source text across labels within a call. The v0.7.2 default preserves
that policy. Source text is case sensitive.

.. versionadded:: 0.7.2

   Both replacement APIs accept the keyword-only ``consistency_scope``.
   ``"text"`` is the default; ``"label"`` opts into independent reuse for each
   normalized label and exact source string. Existing positional arguments
   retain their meaning. v0.7.1 and older versions do not accept this keyword.

For ``Jordan met Jordan.``, assume that the first mention is detected as person,
the second as location, and the replacement rules are
``{"person": "Alice", "location": "Venice"}``:

.. list-table::
   :header-rows: 1

   * - Version
     - Arguments
     - Output
   * - v0.7.1
     - ``ensure_consistency=True`` (default)
     - ``Alice met Alice.``
   * - v0.7.2
     - ``ensure_consistency=True``, scope omitted or ``"text"``
     - ``Alice met Alice.``
   * - v0.7.2
     - ``ensure_consistency=True, consistency_scope="label"``
     - ``Alice met Venice.``
   * - v0.7.1 / v0.7.2
     - ``ensure_consistency=False``
     - ``Alice met Venice.``

With consistency disabled, candidate lists and generated replacements can vary
for every occurrence, including within a label. In v0.7.2 scope is ignored in
that mode, but invalid scope values still raise ``ValueError`` before inference.
Passing the new keyword to an older version raises ``TypeError``. Check
``zink.__version__`` or pin ``zink>=0.7.2`` when using it.

Custom replacers keep the existing three-argument method protocol for default
calls and when consistency is disabled. Opting into label scope requires their
``replace_entities_ensure_consistency`` method to also accept the keyword
``consistency_scope="label"``. The built-in replacer supports both scopes.

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
passage. ``chunk_size`` is a soft target in characters: core chunks extend to
finish a word and its trailing whitespace. Periods, hyphens, and dashes within
words are preserved. Inference adds 32 to 128 characters of context on each side
of each core, extended to whole words, so multiword entities can be recognized
across boundaries. Identical windows are processed once, and duplicate spans
keep their highest score. Only detections intersecting a window's core are kept.

Context reduces boundary losses but model detection remains imperfect, and
entities longer than the available context can still be missed or fragmented.
Review sensitive output before sharing it. Extremely long whitespace-free input
can exceed the backend's input limits even though the chunker keeps it intact.

``redact`` uses chunking when ``auto_parallel=True`` and the text exceeds the
target. Both replacement APIs automatically chunk text exceeding the target,
including when ``auto_parallel=False``.

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
