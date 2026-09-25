Tutorial: preparing research text
=================================

This example uses a short, fictional interview note. Install ``zink[cpu]`` as
described on the :doc:`index` page first. The first import with the inference
backend installed downloads the model, so initialize it before entering an
offline environment.

1. Choose labels and redact
---------------------------

Choose labels that describe the information you want to remove. Zink predicts
spans from these labels; a label is a request, not a guarantee of detection.

.. code-block:: python

   import zink

   note = "Participant Alice works at Acme and lives in Boston."
   labels = ("person", "company", "city")
   result = zink.redact(note, categories=labels)
   print(result.anonymized_text)
   print(result.features["num_replacements"])

The output uses placeholders such as ``person_REDACTED``. Inspect
``result.replacements`` to see the detected label, source text, offsets and
confidence for each span. Review the transformed text manually before sharing
it. False negatives can leave sensitive information in place, and a false
positive can remove useful research content.

2. Keep a research term
-----------------------

If a word must remain in the text, mark it with asterisks or call :func:`zink.prep`.
The markers are removed from the result.

.. code-block:: python

   prepared = zink.prep(note, ["Acme"])
   result = zink.redact(prepared, categories=labels)
   print(result.anonymized_text)

3. Replace with controlled values
---------------------------------

For a readable synthetic note, supply replacements. Values are selected only
for labels the model detects. Unmapped labels use Zink's normal replacement
strategy. The selected value may vary when you provide a list.

.. code-block:: python

   result = zink.replace_with_my_data(
       note,
       categories=labels,
       user_replacements={
           "person": "Participant A",
           "company": "Organization X",
           "city": "City Y",
       },
   )
   print(result.anonymized_text)

Use :func:`zink.replace` for built-in synthetic values. Synthetic replacement
is still model dependent and should receive the same manual review.

4. Keep stable placeholders across notes
----------------------------------------

``numbered_entities=True`` assigns the same placeholder to the same detected
label and source text across calls.

.. code-block:: python

   first = zink.redact(note, categories=labels, numbered_entities=True)
   second = zink.redact(
       "Alice returned for a second interview.",
       categories=("person",),
       numbered_entities=True,
   )
   print(first.anonymized_text, second.anonymized_text)
   print(zink.where_mapping_file())

The mapping file lives at ``~/.zink/mapping.json`` and stores original text in
plain JSON. Restrict access to it and keep it out of published datasets. Call
:func:`zink.refresh_mapping_file` only when you intentionally want to discard
the mapping. The numbered placeholders are pseudonyms, not irreversible
anonymization.

For automation, see :func:`zink.shield` in the :doc:`api`. It restores original
text in a decorated function's string response, so that response is sensitive
again and must be handled accordingly.
