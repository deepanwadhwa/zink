import gzip
import shutil
import sys
import os
from pathlib import Path
import importlib.resources as resources

def compress_file(input_file, output_file):
    """Compress the input_file and save it as output_file using gzip."""
    with open(input_file, 'rb') as f_in, gzip.open(output_file, 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)
    print(f"Compressed '{input_file}' to '{output_file}'.")

def decompress_file(input_file, output_file):
    """Decompress the input_file and save the result as output_file."""
    with gzip.open(input_file, 'rb') as f_in, open(output_file, 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)
    print(f"Success : Decompressed '{input_file}' to '{output_file}'.")

def ensure_replacements_json():
    cache_dir = Path.home() / ".cache" / "zink"
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    json_path = cache_dir / "replacements.json"
    
    if not json_path.exists():
        with resources.open_binary("zink.data", "replacements.json.gz") as gz_file:
            with gzip.open(gz_file, "rb") as f_in:
                with open(json_path, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
        print(f"Decompressed gzip to {json_path}")
    else:
        print(f"{json_path} already exists.")
    
    return json_path


