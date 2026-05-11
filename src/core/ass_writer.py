from __future__ import annotations

from pathlib import Path

import pysubs2


def write_ass(subs: pysubs2.SSAFile, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    subs.save(str(output_path), format_="ass")
