"""Sample Unix process resident memory during an existing benchmark run."""
import argparse
import json
from pathlib import Path
import subprocess
import time


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("pid", type=int)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    started = time.monotonic()
    with args.output.open("x") as output:
        while True:
            result = subprocess.run(["ps", "-o", "rss=", "-p", str(args.pid)],
                                    capture_output=True, text=True)
            if result.returncode or not result.stdout.strip():
                break
            output.write(json.dumps({"seconds_since_sampling_started": time.monotonic() - started,
                                     "resident_mib": int(result.stdout.strip()) / 1024}) + "\n")
            output.flush()
            time.sleep(1)


if __name__ == "__main__":
    main()
