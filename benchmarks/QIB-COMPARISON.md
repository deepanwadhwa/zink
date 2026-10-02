# Zink vs. Microsoft Presidio

Compared on [QIB](https://huggingface.co/datasets/deepanwa/QIB), using each tool’s own model. Presidio uses the GLiNER model from its [official integration example](https://presidio.dataprivacystack.org/samples/python/gliner/). Both receive the same entity label for each passage.

| Comparison | Zink | Presidio + GLiNER |
| --- | --- | --- |
| Model | NuNerZero (ONNX) | gliner_multi_pii-v1 (PyTorch) |
| Exact target detection¹ | **85.5%** | 80.2% |
| Complete target coverage¹ | 87.4% | **87.7%** |
| Median time per passage, including replacement | 443 ms | **92 ms** |
| Total time for 1,750 passages | 783 s | **160 s** |
| Peak process memory | 4.1 GiB | **2.8 GiB** |
| Cached model setup | **6.7 s** | 14.8 s |
| Model download | About 1.86 GB | About 1.16 GB + spaCy model |
| CPU setup | Install `zink[cpu]` | Install analyzer with GLiNER, anonymizer and spaCy model; configure recognizer |
| Zero-shot detection with custom labels | Yes | Yes, through GLiNER integration |
| Redaction and fixed replacements | Built in | Separate anonymizer package |
| Synthetic replacements | Built-in Faker workflow | Custom operator, e.g. Faker |
| Persistent numbered placeholders | Built-in JSON mapping | Custom operator; application saves mapping |
| Masking, hashing and encryption | No built-in operators | Built-in anonymizer operators |
| Local inference after download | Yes | Yes |

Zink detected more exact target spans. Presidio was about **4.9× faster**, used less memory and had similar complete-target coverage.

¹ Accuracy uses 1,734 useful passages. Exact detection requires matching both target boundaries; coverage allows broader detected spans. QIB annotates one target per passage, so these are target-detection rates, not precision or F1. QIB is synthetic and maintained by the Zink author.

Measured in one CPU run per tool on an Apple M3 with 16 GiB RAM. Both receive the target type, never its value or offsets. Emphasis asterisks are removed consistently from both inputs. Timings include placeholder replacement; total time also includes scoring and result writing. Memory includes initialization.

[Full methodology, setup commands and per-topic results](QIB-METHODS.md) · [Benchmark runner](qib_presidio.py) · [Zink results](qib-zink/results.json) · [Presidio results](qib-presidio-gliner/results.json)
