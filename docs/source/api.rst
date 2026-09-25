API reference
=============

The functions below are the public ``zink`` interface. ``categories`` specifies
entity labels; when omitted, the model uses ``person``, ``date`` and
``location``. Inference labels are converted to lowercase.

Redaction and replacement
-------------------------

.. autofunction:: zink.redact

.. autofunction:: zink.replace

.. autofunction:: zink.replace_with_my_data

Protected text and mapping
--------------------------

.. autofunction:: zink.prep

.. autofunction:: zink.where_mapping_file

.. autofunction:: zink.refresh_mapping_file

Decorator
---------

.. autofunction:: zink.shield

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
