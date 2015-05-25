#!/usr/bin/env python
# -*- coding: utf-8 -*-


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read().replace('.. :changelog:', '')

requirements = [
    'lxml>=3.3.0'
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='airs2icarol',
    version='0.3.2',
    description="A tool to convert AIRS XML export files into translation import files for iCarol",
    long_description=readme + '\n\n' + history,
    author="Chris Lambacher",
    author_email='chris@kateandchris.net',
    url='https://github.com/lambacck/airs2icarol',
    packages=[
        'airs2icarol',
    ],
    package_dir={'airs2icarol':
                 'airs2icarol'},
    include_package_data=True,
    install_requires=requirements,
    license="Apache 2.0",
    zip_safe=False,
    keywords='airs2icarol',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        # 'Programming Language :: Python :: 3',
        # 'Programming Language :: Python :: 3.3',
        # 'Programming Language :: Python :: 3.4',
    ],
    test_suite='tests',
    tests_require=test_requirements,
    entry_points={
        'console_scripts': [
            'airs2icarol = airs2icarol.command_line:main'
        ]
    }
)
