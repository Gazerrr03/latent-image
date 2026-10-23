#!/usr/bin/env python3
"""Fetch only the official Godot export templates needed for this project."""

from __future__ import annotations

import argparse
import binascii
import struct
import urllib.request
import zlib
from pathlib import Path


GODOT_VERSION = "4.7.2"
ARCHIVE_URL = (
    f"https://downloads.godotengine.org/?version={GODOT_VERSION}&flavor=stable"
    "&slug=export_templates.tpz&platform=templates"
)
USER_AGENT = "LatentImage-export-packaging/1.0"
TAIL_SIZE = 65_536

TARGETS = {
    "macos-universal": ("templates/macos.zip",),
    "windows-x86_64": (
        "templates/windows_debug_x86_64.exe",
        "templates/windows_release_x86_64.exe",
    ),
}


def request_range(start: int, end: int | None = None) -> tuple[bytes, str]:
    value = f"bytes={start}-{end}" if end is not None else f"bytes=-{TAIL_SIZE}"
    request = urllib.request.Request(
        ARCHIVE_URL,
        headers={"Range": value, "User-Agent": USER_AGENT},
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        return response.read(), response.headers.get("Content-Range", "")


def selected_entries() -> tuple[int, dict[str, tuple[int, int, int, int, int]]]:
    tail, content_range = request_range(0)
    try:
        tail_start, tail_end, archive_size = map(
            int,
            content_range.removeprefix("bytes ").replace("/", "-").split("-"),
        )
    except ValueError as exc:
        raise RuntimeError(f"Unexpected Content-Range for template archive: {content_range}") from exc
    if len(tail) != tail_end - tail_start + 1 or tail_end + 1 != archive_size:
        raise RuntimeError("Could not read the end of the official template archive.")

    eocd_offset = tail.rfind(b"PK\x05\x06")
    if eocd_offset < 0:
        raise RuntimeError("The official template archive has no ZIP footer.")
    _, _, _, _, entry_count, central_size, central_offset, _ = struct.unpack_from(
        "<IHHHHIIH", tail, eocd_offset
    )
    if entry_count == 0xFFFF or central_size == 0xFFFFFFFF or central_offset == 0xFFFFFFFF:
        raise RuntimeError("ZIP64 export template archives are not supported by this helper.")

    if central_offset >= tail_start:
        central = tail[central_offset - tail_start : central_offset - tail_start + central_size]
    else:
        central, central_range = request_range(central_offset, central_offset + central_size - 1)
        if not central_range.startswith(f"bytes {central_offset}-"):
            raise RuntimeError("Could not read the export template index.")
    if len(central) != central_size:
        raise RuntimeError("The export template index is incomplete.")

    wanted = {"templates/version.txt"}
    for files in TARGETS.values():
        wanted.update(files)
    entries: dict[str, tuple[int, int, int, int, int]] = {}
    position = 0
    for _ in range(entry_count):
        if struct.unpack_from("<I", central, position)[0] != 0x02014B50:
            raise RuntimeError("The official template archive index is malformed.")
        fields = struct.unpack_from("<IHHHHHHIIIHHHHHII", central, position)
        (_, _, _, _, method, _, _, crc32, compressed_size, uncompressed_size,
         name_size, extra_size, comment_size, _, _, _, local_offset) = fields
        name = central[position + 46 : position + 46 + name_size].decode("utf-8")
        if name in wanted:
            entries[name] = (local_offset, compressed_size, uncompressed_size, method, crc32)
        position += 46 + name_size + extra_size + comment_size

    if entries.keys() != wanted:
        missing = ", ".join(sorted(wanted - entries.keys()))
        raise RuntimeError(f"Required template entries are missing: {missing}")
    return archive_size, entries


def fetch_entry(name: str, info: tuple[int, int, int, int, int], archive_size: int) -> bytes:
    local_offset, compressed_size, expected_size, method, expected_crc = info
    local_header, _ = request_range(local_offset, local_offset + 29)
    if len(local_header) != 30 or local_header[:4] != b"PK\x03\x04":
        raise RuntimeError(f"Bad ZIP local header for {name}.")
    _, _, _, local_method, _, _, _, _, _, name_size, extra_size = struct.unpack(
        "<IHHHHHIIIHH", local_header
    )
    if local_method != method:
        raise RuntimeError(f"ZIP compression method mismatch for {name}.")

    data_start = local_offset + 30 + name_size + extra_size
    data_end = data_start + compressed_size - 1
    compressed, data_range = request_range(data_start, data_end)
    if len(compressed) != compressed_size:
        raise RuntimeError(f"Incomplete download for {name}.")
    if not data_range.startswith(f"bytes {data_start}-") or not data_range.endswith(f"/{archive_size}"):
        raise RuntimeError(f"Unexpected Content-Range for {name}: {data_range}")

    if method == 0:
        result = compressed
    elif method == 8:
        result = zlib.decompress(compressed, -15)
    else:
        raise RuntimeError(f"Unsupported ZIP compression method {method} for {name}.")
    if len(result) != expected_size:
        raise RuntimeError(f"Uncompressed size mismatch for {name}.")
    if binascii.crc32(result) & 0xFFFFFFFF != expected_crc:
        raise RuntimeError(f"Checksum mismatch for {name}.")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--platform", choices=TARGETS, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    archive_size, entries = selected_entries()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    names = ("templates/version.txt", *TARGETS[args.platform])
    for name in names:
        data = fetch_entry(name, entries[name], archive_size)
        output = args.output_dir / name.rsplit("/", 1)[-1]
        output.write_bytes(data)
        print(f"Installed {output} ({len(data):,} bytes)")


if __name__ == "__main__":
    main()
