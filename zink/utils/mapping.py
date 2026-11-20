"""Private, atomic persistence for numbered entity mappings."""

import json
import os
from pathlib import Path
import tempfile


def save_mapping(path, mapping):
    """Replace a mapping atomically, using mode 0600 on POSIX.

    A private temporary file in the same directory prevents partial JSON and
    avoids a window with permissive creation permissions. Replacing the old
    file also tightens permissions of previously created mappings. Windows
    access remains subject to the containing directory's access controls.
    """
    path = Path(path)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            prefix=".mapping-",
            dir=path.parent,
            delete=False,
        ) as stream:
            temporary = Path(stream.name)
            if os.name == "posix":
                os.fchmod(stream.fileno(), 0o600)
            json.dump(mapping, stream, indent=2)
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
