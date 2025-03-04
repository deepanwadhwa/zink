import gzip
import shutil
import sys

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

