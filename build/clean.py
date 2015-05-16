#!/usr/bin/env python
"""Clean the build artifacts."""

import os
import glob
import sys

import grammar


def main():
    """Perform the cleaning work."""
    if len(sys.argv) > 1:
        build_dir = sys.argv[1]
    else:
        build_dir = os.getcwd()

    os.chdir(build_dir)

    for f in glob.glob('*.JSON-tmLanguage'):
        xml = grammar.xml_filename(f)
        if os.path.exists(xml):
            print('Deleting ' + xml)
            os.remove(xml)


if __name__ == "__main__":
    main()
