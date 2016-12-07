#!/usr/bin/python

import argparse
import sys
import yaml


def main():
    # Parse command line arguments.
    parser = argparse.ArgumentParser(description='Convert text file to YAML.')
    parser.add_argument('key', metavar='KEY', help='key to insert/replace')
    parser.add_argument('file', metavar='FILE', help='text file to read')
    args = parser.parse_args()

    # Read YAML from stdin.
    y = yaml.load(sys.stdin)

    # Read text file.
    with open(args.file, 'r') as f:
        y[args.key] = map(lambda line: line.rstrip('\n'), f.readlines())

    # Write amended YAML to stdout.
    yaml.dump(y, sys.stdout)


if __name__ == '__main__':
    main()
