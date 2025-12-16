import os
from pathlib import Path

def get_default_mapping_path():
    """Returns the default path for the persistent entity mapping file."""
    home = Path.home()
    zink_dir = home / ".zink"
    zink_dir.mkdir(parents=True, exist_ok=True)
    return str(zink_dir / "mapping.json")
