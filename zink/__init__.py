from .zink import *
import os
from .utils import data_utils

if "replacements.json" not in os.listdir("zink/data"):
    print("Decompressing replacements.json.gz ...")
    data_utils.decompress_file("zink/data/replacements.json.gzip", "zink/data/replacements.json")