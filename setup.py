#!/usr/bin/env python

'''pollenc setup.py'''
from setuptools import setup

setup(
    name="pollenc",
    version="0.9.0",
    install_requires=[
    ],
    scripts=['bin/pollenc'],
    author="Amaret, Inc",
    author_email="develop@amaret.com",
    description=("A command-line client to the Pollen Cloud Compiler."),
    license="GPLv2",
    keywords="python pollen micro-controller toolchain compiler",
    url="https://github.com/amaret/pollenc",
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Topic :: Software Development :: Compilers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7'
    ],
)

