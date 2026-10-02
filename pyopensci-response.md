Hi @kysolvik, thanks for the feedback! I have addressed all four points:

- Added an import-time warning when GLiNER or ONNX Runtime is missing, with instructions to install `zink[cpu]` or `zink[gpu]`.
- Added a warning in the README and docs that the first run downloads approximately 2 GB and can take several minutes.
- Added a tutorial for processing a folder of text files.
- Added a [comparison with Microsoft Presidio on QIB](https://github.com/deepanwadhwa/zink/blob/main/benchmarks/QIB-COMPARISON.md), with tables covering accuracy, speed, memory, setup and replacement features.

Thanks for starting the editor search!
