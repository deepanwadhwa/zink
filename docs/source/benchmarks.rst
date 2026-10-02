QIB comparison with Presidio
============================

This CPU comparison uses Zink's default NuNerZero ONNX model and the model
used in `Presidio's official GLiNER example <https://presidio.dataprivacystack.org/samples/python/gliner/>`_,
``urchade/gliner_multi_pii-v1``. Both receive the same single semantic label
per passage and perform detection plus placeholder replacement.

.. list-table:: Observed results
   :header-rows: 1
   :widths: 50 25 25

   * - Metric
     - Zink
     - Presidio + GLiNER
   * - F4
     - 0.8520
     - 0.7906
   * - Precision
     - 81.16%
     - 64.22%
   * - Recall
     - 85.47%
     - 80.22%
   * - All 1,750 passages: processing time
     - 782.8 s
     - 160.5 s
   * - Median per-passage latency
     - 442.8 ms
     - 92.4 ms
   * - Peak process resident memory
     - 4193 MiB
     - 2885 MiB
   * - Cached setup including imports
     - 6.74 s
     - 14.82 s

The run used an Apple M3 CPU with 16 GiB RAM, Python 3.13.13, and one full
timed pass per primary configuration. Speed numbers are single-run observations,
not guarantees across hardware or datasets. Peak RSS includes loading spikes;
it is not steady-state memory. Zink uses ONNX and two extraction passes; Presidio
uses PyTorch with its documented GLiNER settings and default chunking and threshold.

Accuracy uses the 1,734 QIB records marked useful, out of 1,750 total records.
Scores are micro-averaged using exact target boundaries, ignoring predicted label
names. Duplicate spans are counted once. Unmatched predictions count as false
positives and missed targets as false negatives. F4 = 17PR / (16P + R).
We prioritize recall because a missed identifier can expose sensitive information,
whereas an unnecessary redaction removes useful text.

The semantic labels come from the annotations, lowercased with underscores
replaced by spaces. Neither tool receives the target value or offsets. Emphasis
asterisks are removed for both tools and gold offsets are updated, because
asterisks activate Zink's exclusion syntax. The dataset revision is
``af345705a03852b8bd77c2e69c971a0361b1e71d``.

We created QIB to address the lack of diverse benchmarks for quasi-identifier
detection. It contains 1,750 examples across 35 categories, including personal
preferences and security-question answers. This run uses a separate scoring
protocol from the historical README benchmark table.

See the `comparison table
<https://github.com/deepanwadhwa/zink/blob/main/benchmarks/QIB-COMPARISON.md>`_
and `methodology and reproduction commands
<https://github.com/deepanwadhwa/zink/blob/main/benchmarks/QIB-METHODS.md>`_.
