#!/usr/bin/env python
"""Build everything."""

import os
import glob
import sys

import grammar


def must_build(source, target):
    """Determine if building is necessary.

    :return: True if a build is needed, False otherwise.

    """
    if os.path.exists(target):
        return os.path.getmtime(source) >= os.path.getmtime(target)
    return True


def main():
    """Perform the build, if necessary."""
    if len(sys.argv) > 1:
        build_dir = sys.argv[1]
    else:
        build_dir = os.getcwd()

    os.chdir(build_dir)

    for source in glob.glob('*.JSON-tmLanguage'):
        target = grammar.xml_filename(source)
        if must_build(source, target):
            print('Building %s' % target)
            grammar.build(source)
        else:
            print('%s is up to date.' % target)


if __name__ == "__main__":
    main()
