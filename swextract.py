#!/usr/bin/env python3

import argparse
import os
import re
import subprocess

def parse_args():
    parser = argparse.ArgumentParser(
        description="Extract files from an IRIX software package (.sw/.idb).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("idb", help="Absolute path to the .idb index file")
    parser.add_argument("sw",  help="Absolute path to the .sw archive file")
    parser.add_argument("out", help="Output directory for extracted files")
    return parser.parse_args()

def extract_paren(line, key):
    m = re.search(rf'{re.escape(key)}\((\d+)\)', line)
    return int(m.group(1)) if m else None

def main():
    args = parse_args()
    swdir = os.path.dirname(args.sw)

    # Running byte offset per sw base file; each sw file has a 13-byte header.
    swoffset = {}

    with open(args.idb, 'r', errors='replace') as f:
        for line in f:
            line = line.rstrip('\r\n')
            parts = line.split()
            if not parts:
                continue

            kind = parts[0]

            if kind == 'd':
                if len(parts) >= 5:
                    os.makedirs(os.path.join(args.out, parts[4]), exist_ok=True)
                continue

            if kind != 'f' or len(parts) < 7:
                continue

            fullpath = parts[4]
            swname   = parts[6]
            swbase   = swname.rsplit('.', 1)[0]
            swpath   = os.path.join(swdir, swbase)
            strlen   = len(fullpath)
            cmpsize  = extract_paren(line, 'cmpsize')
            size     = extract_paren(line, 'size')

            if cmpsize is None or size is None:
                continue

            if swbase not in swoffset:
                swoffset[swbase] = 13
            offset = swoffset[swbase]

            parent = os.path.dirname(fullpath)
            if parent:
                os.makedirs(os.path.join(args.out, parent), exist_ok=True)

            if not os.path.isfile(swpath):
                print(f"Skipping {fullpath} ({swbase} not found)")
                swoffset[swbase] = offset + 2 + strlen + (size if cmpsize == 0 else cmpsize)
                continue

            skip = offset + 2 + strlen

            if cmpsize == 0:
                print(f"Extracting {fullpath} (uncompressed, size={size})")
                with open(swpath, 'rb') as sw:
                    sw.seek(skip)
                    data = sw.read(size)
                with open(os.path.join(args.out, fullpath), 'wb') as out:
                    out.write(data)
                swoffset[swbase] = offset + 2 + strlen + size
            else:
                print(f"Extracting {fullpath} (cmpsize={cmpsize})")
                outfile_z = os.path.join(args.out, fullpath) + '.Z'
                with open(swpath, 'rb') as sw:
                    sw.seek(skip)
                    data = sw.read(cmpsize)
                with open(outfile_z, 'wb') as out:
                    out.write(data)
                subprocess.run(['uncompress', outfile_z], stderr=subprocess.DEVNULL)
                swoffset[swbase] = offset + 2 + strlen + cmpsize

if __name__ == '__main__':
    main()
