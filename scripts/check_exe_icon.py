"""Confere se o ícone do Orguine foi embutido no .exe do Windows.

Uso:  python scripts/check_exe_icon.py dist/Orguine-windows-amd64.exe orguine/resources/orguine_icon.ico
Requer: pip install pefile
"""

from __future__ import annotations

import struct
import sys
from pathlib import Path

import pefile


def ico_images(path: Path) -> list[bytes]:
    data = path.read_bytes()
    _, _, count = struct.unpack_from("<HHH", data, 0)
    images = []
    for i in range(count):
        size, offset = struct.unpack_from("<II", data, 6 + i * 16 + 8)
        images.append(data[offset:offset + size])
    return images


def exe_icons(path: Path) -> list[bytes]:
    pe = pefile.PE(str(path), fast_load=True)
    pe.parse_data_directories([pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_RESOURCE"]])
    out = []
    for entry in getattr(pe, "DIRECTORY_ENTRY_RESOURCE", None).entries:
        if entry.id == pefile.RESOURCE_TYPE["RT_ICON"]:
            for res in entry.directory.entries:
                for lang in res.directory.entries:
                    d = lang.data.struct
                    out.append(pe.get_data(d.OffsetToData, d.Size))
    return out


def main() -> int:
    exe, ico = Path(sys.argv[1]), Path(sys.argv[2])
    want = ico_images(ico)
    have = exe_icons(exe)
    missing = [i for i, img in enumerate(want) if img not in have]
    print(f"{exe.name}: {len(have)} imagens de ícone embutidas; {ico.name}: {len(want)} imagens")
    if missing:
        print(f"ERRO: {len(missing)} imagens do ícone não foram encontradas no executável")
        return 1
    print("OK: o ícone do Orguine está embutido no executável")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
