========
Usage
========

To use AIRS XML 2 iCarol Translation in a project::

    import airs2icarol

    # get translations for selected language
    transaltions = airs2icarol.get_stdtranslation(langauges = ['fr'])
    
    airs2icarol.convert_xml('source.xml', 'dest.csv', 'fr', translations)


:code:`source.xml` and :code:`dest.csv` can optionally end in :code:`.zip` they will then be
treated as zip files containing a single file. The filename inside :code:`source.zip`
is ignored, and the filename in :code:`dest.zip` will be :code:`dest.csv`. The output CSV
file will be encoded in UTF-8 prefixed with a UTF-8 BOM (Byte Order Mark).

==================
Command Line Usage
==================

When airs2icarol is installed, an :code:`airs2icarol` command line application is
also installed. This can be run as follows::

    airs2icarol source.xml dest.csv fr

Where :code:`source.xml` and :code:`dest.csv` can optionally end in :code:`.zip` they will then be
treated as zip files containing a single file. The filename inside :code:`source.zip`
is ignored, and the filename in :code:`dest.zip` will be :code:`dest.csv`. The output CSV
file will be encoded in UTF-8 prefixed with a UTF-8 BOM (Byte Order Mark).
:code:`fr` is the target translation culture code.
