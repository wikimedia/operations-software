import argparse


def parse_args():
    parser = argparse.ArgumentParser(description='See https://wikitech.wikimedia.org/wiki/Auto_schema')
    parser.add_argument('--section', help='section name, overrides value in the code')
    parser.add_argument('--check', action='store_true', help='Check only')
    parser.add_argument(
        '--include-masters',
        action='store_true',
        help='Do\'nt ask before handling master',
        dest='include_masters'
    )
    parser.add_argument(
        '--primary-master',
        action='store_true',
        help='Run on master of section in primary dc',
        dest='primary_master'
    )
    parser.add_argument('--run', action='store_true', help='Run the schema change')
    args = parser.parse_args()
    return args
