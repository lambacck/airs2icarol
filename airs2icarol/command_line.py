import os
import sys
import argparse
import gettext

try:
    from pkg_resources import resource_filename
except ImportError:
    resource_filename = None

from .airs2icarol import convert_xml


def parse_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('source', action='store')
    parser.add_argument('dest', action='store')
    parser.add_argument('culture', action='store')

    return parser.parse_args(argv)


def main(initial_args=None):
    if initial_args is None:
        initial_args = sys.argv[1:]

    args = parse_args(initial_args)

    gettext = get_stdtranslation(languages=[args.culture])

    convert_xml(args.source, args.dest, args.culture, gettext)

    return 0


def get_localedir():
    """Retrieve the location of locales.
    If we're built as an egg, we need to find the resource within the egg.
    Otherwise, we need to look for the locales on the filesystem or in the
    system message catalog.
    """
    locale_dir = ''
    # Check the egg first
    if resource_filename is not None:
        try:
            locale_dir = resource_filename(__name__, "/i18n")
        except NotImplementedError:
            # resource_filename doesn't work with non-egg zip files
            pass
    if not hasattr(os, 'access'):
        # This happens on Google App Engine
        return os.path.join(os.path.dirname(__file__), 'i18n')
    if os.access(locale_dir, os.R_OK | os.X_OK):
        # If the resource is present in the egg, use it
        return locale_dir

    # Otherwise, search the filesystem
    locale_dir = os.path.join(os.path.dirname(__file__), 'i18n')
    if not os.access(locale_dir, os.R_OK | os.X_OK):
        # Fallback on the system catalog
        locale_dir = os.path.normpath('/usr/share/locale')

    return locale_dir


def get_stdtranslation(domain="Airs2Icarol", languages=None,
                       localedir=get_localedir()):

    t = gettext.translation(domain=domain,
                            languages=languages,
                            localedir=localedir, fallback=True)
    try:
        _ = t.ugettext
    except AttributeError:  # Python 3
        _ = t.gettext

    return _
