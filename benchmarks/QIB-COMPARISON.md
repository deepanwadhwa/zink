# Zink vs. Microsoft Presidio

Compared on [QIB](https://huggingface.co/datasets/deepanwa/QIB), using each tool’s own model. Presidio uses the GLiNER model from its [official integration example](https://presidio.dataprivacystack.org/samples/python/gliner/). Both receive the same entity label for each passage.

| Comparison | Zink | Presidio + GLiNER |
| --- | --- | --- |
| Detection model / CPU backend | NuNerZero / ONNX Runtime | `urchade/gliner_multi_pii-v1` / PyTorch |
| **F4 score¹** | **0.8520** | 0.7906 |
| Precision¹ | **81.16%** | 64.22% |
| Recall¹ | **85.47%** | 80.22% |
| Median time per passage, including replacement | 443 ms | **92 ms** |
| Total time for 1,750 passages | 783 s | **160 s** |
| Peak process memory | 4.1 GiB | **2.8 GiB** |
| Startup with model already downloaded | **6.7 s** | 14.8 s |
| Model download | About 1.86 GB | About 1.16 GB + spaCy model |


Zink needs one installation command: `pip install "zink[cpu]"`. Its default model and replacement workflows are already configured. The tested Presidio GLiNER workflow requires installing the analyzer, anonymizer and spaCy model, then configuring the recognizer and label mapping.

Zink achieved higher F4, precision and recall. Presidio was about **4.9× faster** and used less memory.

For anonymization, a missed identifier can expose sensitive information; an unnecessary redaction removes useful text. We prioritize recall because leaving identifying information behind is the more consequential error. F4 reflects that priority by weighting recall 16 times as heavily as precision in its harmonic mean, while still accounting for unnecessary detections.

¹ Micro-averaged scores across 1,734 useful QIB passages. A true positive matches both annotated target boundaries; unmatched predictions count as false positives and missed targets as false negatives. F4 = 17PR / (16P + R). QIB is synthetic and maintained by the Zink author.

Measured in one CPU run per tool on an Apple M3 with 16 GiB RAM. Both receive the target type, never its value or offsets. Emphasis asterisks are removed consistently from both inputs. Timings include placeholder replacement; total time also includes scoring and result writing. Memory includes initialization.

[Full methodology, setup commands and per-topic results](QIB-METHODS.md) · [Benchmark runner](qib_presidio.py) · [Zink results](qib-zink/results.json) · [Presidio results](qib-presidio-gliner/results.json)
