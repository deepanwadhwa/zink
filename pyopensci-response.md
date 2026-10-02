Draft maintainer response — post after the changes are published

Hi @kysolvik, thank you for the checks and for starting the editor search. I have prepared changes addressing the suggestions:

- Zink now warns at import if GLiNER or ONNX Runtime is unavailable, with CPU/GPU installation instructions. The base package remains importable, and inference still raises an actionable ImportError. I also removed global warning suppression that would otherwise hide this warning.
- The README and installation docs explain that the first import downloads approximately 2 GB of model files and can take several minutes, with cache and offline guidance.
- The tutorial now includes sequential processing of a folder of UTF-8 text files, writing to a separate output folder without overwriting files, and guidance on review, long documents and mapping files.
- I added a reproducible QIB comparison against Presidio's documented GLiNER example (`urchade/gliner_multi_pii-v1`), retaining the spaCy/rule configuration as a supplementary baseline, with a pinned dataset revision, per-record prediction offsets, full and shared-label target-detection results, CPU timing, peak memory, setup notes and a feature table. Both primary configurations receive each record's annotated semantic label, not its target value or offsets, so this is an annotation-assisted label-driven workflow comparison. The common preprocessing removes QIB emphasis asterisks, which otherwise activate Zink's exclusion feature. QIB annotates one target per passage, so extra predictions are reported without calling them false positives or using them to claim ordinary precision/F4. The primary comparison keeps each tool's own model and documented extraction defaults, gives them identical label information, and includes placeholder replacement in both timings.
- Ruff now runs in CI, initially checking undefined names. Migrating the public API to type hints and adopting a type checker remains follow-up work.

I completed the onboarding survey before submitting, as indicated in the submission. I noticed that its checkbox in the checks is still open; please let me know if the response did not arrive. I will update the archived release/DOI for JOSS at the appropriate point after review.

I also used OpenAI Codex in October 2026 to help implement these changes, write the tutorial and benchmark runner, and run validation. I reviewed the changes and results.

The primary QIB run found 85.5% exact target detection for Zink and 80.2% for Presidio GLiNER; complete target coverage was 87.4% and 87.7%, respectively. Full-corpus detection plus replacement took 782.8 s and 160.5 s, with peak RSS about 4,193 MiB and 2,885 MiB. These are single CPU runs, not universal rankings. The full comparison documents setup, downloads, models, thresholds, prompt information and annotation limitations.

Validation: the existing model-backed tests passed during this work; benchmark and dependency tests, Ruff and the final Sphinx build were checked separately. The existing long-text test exposes GLiNER truncation warnings now that global warning suppression is removed.
