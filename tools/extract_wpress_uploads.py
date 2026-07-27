#!/usr/bin/env python3
import argparse
import os
from pathlib import Path


HEADER_SIZE = 4377
NAME_SIZE = 255
SIZE_OFFSET = 255
SIZE_END = 269
MTIME_OFFSET = 269
MTIME_END = 281
PATH_OFFSET = 281
UPLOAD_PREFIX = "wp-content/uploads/"
UPLOAD_DIR_PREFIX = "uploads/"


def read_c_string(data):
    return data.split(b"\0", 1)[0].decode("utf-8", "replace")


def iter_wpress_entries(archive_path):
    position = 0
    archive_size = archive_path.stat().st_size

    with archive_path.open("rb") as archive:
        while position + HEADER_SIZE <= archive_size:
            archive.seek(position)
            header = archive.read(HEADER_SIZE)
            if len(header) < HEADER_SIZE:
                break

            name = read_c_string(header[:NAME_SIZE])
            size_text = read_c_string(header[SIZE_OFFSET:SIZE_END])
            mtime_text = read_c_string(header[MTIME_OFFSET:MTIME_END])
            directory = read_c_string(header[PATH_OFFSET:])

            if not name or not size_text.isdigit():
                break

            size = int(size_text)
            data_offset = position + HEADER_SIZE
            yield {
                "name": name,
                "directory": directory,
                "archive_path": f"{directory.rstrip('/')}/{name}" if directory and directory != "." else name,
                "size": size,
                "mtime": int(mtime_text) if mtime_text.isdigit() else None,
                "data_offset": data_offset,
            }
            position = data_offset + size


def safe_upload_destination(output_dir, archive_path):
    if archive_path.startswith(UPLOAD_PREFIX):
        relative_name = archive_path.removeprefix(UPLOAD_PREFIX)
    elif archive_path.startswith(UPLOAD_DIR_PREFIX):
        relative_name = archive_path.removeprefix(UPLOAD_DIR_PREFIX)
    else:
        return None

    relative_path = Path(relative_name)

    if relative_path.is_absolute() or ".." in relative_path.parts:
        return None

    return output_dir / relative_path


def extract_uploads(archive_path, output_dir, dry_run=False):
    count = 0
    total_bytes = 0

    output_dir.mkdir(parents=True, exist_ok=True)

    with archive_path.open("rb") as archive:
        for entry in iter_wpress_entries(archive_path):
            destination = safe_upload_destination(output_dir, entry["archive_path"])
            if destination is None:
                continue

            count += 1
            total_bytes += entry["size"]

            if dry_run:
                continue

            destination.parent.mkdir(parents=True, exist_ok=True)
            archive.seek(entry["data_offset"])
            with destination.open("wb") as output:
                remaining = entry["size"]
                while remaining:
                    chunk = archive.read(min(1024 * 1024, remaining))
                    if not chunk:
                        raise EOFError(f"Archive ended while extracting {entry['archive_path']}")
                    output.write(chunk)
                    remaining -= len(chunk)

            if entry["mtime"] is not None:
                try:
                    os.utime(destination, (entry["mtime"], entry["mtime"]))
                except OSError:
                    pass

    return count, total_bytes


def main():
    parser = argparse.ArgumentParser(description="Extract uploads from an All-in-One WP Migration .wpress archive.")
    parser.add_argument("archive", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    count, total_bytes = extract_uploads(args.archive, args.output_dir, args.dry_run)
    mode = "Would extract" if args.dry_run else "Extracted"
    print(f"{mode} {count} upload files ({total_bytes / 1024 / 1024:.1f} MB) to {args.output_dir}")


if __name__ == "__main__":
    main()
