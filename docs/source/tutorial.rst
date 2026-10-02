Tutorial: preparing research text
=================================

This example uses a short, fictional interview note. Install ``zink[cpu]`` as
described on the :doc:`index` page first. The first import with the inference
backend installed downloads the model, so initialize it before entering an
offline environment.

1. Choose labels and redact
---------------------------

Choose labels that describe the information you want to remove. Zink predicts
spans from these labels and may miss relevant text.

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

To replace detected spans with your own values, pass ``user_replacements``.
Unmapped labels use Zink's default replacement strategy. When you provide a
list, Zink selects one value from it.

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
the mapping. The numbered placeholders can be linked back to the original
text through this file.

For automation, see :func:`zink.shield` in the :doc:`api`. It restores original
text in a decorated function's string response, so that response is sensitive
again and must be handled accordingly.

5. Process a folder of text files
---------------------------------

Save fictional notes as UTF-8 ``.txt`` files in ``notes/``. This sequential
workflow reads one file at a time and writes transformed text to a separate
folder. It never overwrites an input file and refuses to overwrite an existing
output. Keep output private until you have reviewed every file.

.. code-block:: python

   from pathlib import Path
   import zink

   source = Path("notes")
   destination = Path("redacted_notes")
   destination.mkdir(exist_ok=True)
   labels = ("person", "company", "location", "date")

   for path in sorted(source.glob("*.txt")):
       text = path.read_text(encoding="utf-8")
       result = zink.redact(text, categories=labels, use_cache=False)
       with (destination / path.name).open("x", encoding="utf-8") as output:
           output.write(result.anonymized_text)
       print(path.name, result.features["num_replacements"])

For example, ``notes/interview_01.txt`` might contain::

   Alice works at Acme in Boston. The interview was on June 12, 2025.

The transformed file contains placeholders for detected spans. Predictions
vary; a successful script exit does not establish that all sensitive text was
removed. ``use_cache=False`` avoids retaining extraction results for each file
in the pipeline cache. The result object still contains the original text and
detected values, so this example writes only ``anonymized_text``.

Files longer than the model's context may lose detections. For long documents,
split on paragraph boundaries and review the resulting sections. Avoid splitting
names or other entities across sections. The example uses sequential calls;
do not share Zink's default extractor across concurrent file-processing threads.
To keep stable placeholders across files, add ``numbered_entities=True`` and
protect the mapping file as described above.
