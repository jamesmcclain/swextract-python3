# swextract

A Python utility for extracting files from IRIX software packages.

## Background

IRIX software is distributed as pairs of files: a `.idb` index file and one or more `.sw` archive files. The `.idb` describes every file in the package — its path, permissions, which archive it lives in, and its compressed size. The `.sw` files are sequential binary archives of LZW-compressed (`.Z`) or verbatim data, prefixed with a 13-byte file header and 2-byte per-entry overhead.

This tool parses the `.idb` and extracts each file from the appropriate `.sw` archive into a directory tree that mirrors the original IRIX filesystem layout.

## Requirements

- Python 3.6+
- `uncompress` (the `ncompress` package on Debian/Ubuntu: `sudo apt install ncompress`)

## Usage

```
python3 swextract.py <idb> <sw> <outdir>
```

| Argument | Description |
|----------|-------------|
| `idb`    | Path to the `.idb` index file |
| `sw`     | Path to one of the package's `.sw` archive files |
| `outdir` | Directory to extract files into (created if necessary) |

### Example

```
python3 swextract.py /path/to/c_fe.idb /path/to/c_fe.sw /path/to/irixroot
```

### Multiple `.sw` files

A package may ship several `.sw` archives. The `.idb` refers to them by component name — for example, `c_fe.sw.c`, `c_fe.sw64.lib`, and `c_fe.man.relnotes`. The script resolves these by stripping the last extension (`c_fe.sw.c` → `c_fe.sw`, `c_fe.man.relnotes` → `c_fe.man`) and looking for the resulting filename in the same directory as the provided `.sw` file. Place all available archives in the same directory and point the script at any one of them; it will find the rest automatically.

Files belonging to an archive that is not present are skipped with a notice.

## Output

Files are extracted into `outdir` preserving the full IRIX path (e.g. `outdir/usr/lib/cfe`, `outdir/usr/lib32/cmplrs/fec`). Directories are created as needed.

## `.sw` archive format

Documented here for reference, as it does not appear to be described elsewhere.

- **Bytes 0–12**: 13-byte file header. The first 12 bytes are an ASCII version string (e.g. `im001V620P02`); the 13th byte is `0x00`.
- **Per entry**: 2-byte entry header + path + compressed data.
  - **Byte 0**: entry type/flags (observed as `0x00`).
  - **Byte 1**: path length as a single unsigned byte.
  - **Bytes 2–(2+pathlen−1)**: file path, not null-terminated.
  - **Remaining bytes**: compressed file data, either LZW (`.Z` format, magic `1f 9d`) or verbatim (when `cmpsize` is 0 in the `.idb`).
- Entries are sequential with no padding between them.
- The `off()` field sometimes present in `.idb` files gives the absolute byte offset of an entry's 2-byte header within the archive; when absent (as in the packages this tool was developed against), offsets are computed by accumulating `2 + pathlen + cmpsize` per entry starting from 13.
