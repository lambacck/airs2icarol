import sys
import argparse

from .airs2icarol import convert_xml, get_stdtranslation


def parse_args(argv):
    parser = argparse.ArgumentParser(prog='airs2icarol', description='Convert an AIRS XML file into an iCarol CSV translation file.')
    parser.add_argument('source', action='store', help='Source AIRS XML file or zip file containing an AIRS XML File')
    parser.add_argument('dest', action='store', help='Destination iCarol Translation File')
    parser.add_argument('culture', action='store', help='Culture code for destination translation file')

    return parser.parse_args(argv)


def main(initial_args=None):
    if initial_args is None:
        initial_args = sys.argv[1:]

    args = parse_args(initial_args)

    gettext = get_stdtranslation(languages=[args.culture])

    convert_xml(args.source, args.dest, args.culture, gettext)

    return 0
