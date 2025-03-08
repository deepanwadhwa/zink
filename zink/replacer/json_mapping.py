import json
import random
import gzip
import shutil
from pathlib import Path
import importlib.resources as resources  # available in Python 3.7+
from .base import ReplacementStrategy

def ensure_replacements_json():
    """
    Ensure that the decompressed replacements.json file exists in a writable cache.
    If it doesn't exist, decompress it from the bundled gzip file.
    Returns the path to the JSON file.
    """
    # Define a cache directory (e.g., in the user's home directory)
    cache_dir = Path.home() / ".cache" / "zink"
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    json_path = cache_dir / "replacements.json"
    
    if not json_path.exists():
        try:
            # Open the compressed file from the package resources.
            # Make sure that the 'zink.data' subpackage has an __init__.py.
            with resources.files("zink.data").joinpath("replacements.json.gzip").open("rb") as gz_file:
                with gzip.open(gz_file, "rb") as f_in:
                    with open(json_path, "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)

            #print(f"Decompressed gzip to {json_path}")
        except Exception as e:
            print(f"Error decompressing gzip file: {e}")
    
    return json_path

def load_mapping():
    """
    Load the JSON mapping, ensuring the decompressed JSON file exists.
    """
    json_path = ensure_replacements_json()
    try:
        with open(json_path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading JSON mapping: {e}")
        return {}

# Load mapping globally so it is loaded only once.
GLOBAL_MAPPING = load_mapping()

class JsonMappingReplacementStrategy(ReplacementStrategy):
    def __init__(self, label):
        # Store the label in lowercase.
        self.label = label.lower()

    def replace(self, entity):
        candidates = GLOBAL_MAPPING.get(self.label)
        if candidates and isinstance(candidates, list):
            first_random = random.choice(candidates)
            if first_random != entity['text']:
                return first_random
            second_random = random.choice(candidates)
            if second_random != entity['text']:
                return second_random
            return "[REDACTED]"
        return "[REDACTED]"
