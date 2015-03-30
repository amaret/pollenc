#!/usr/bin/env python

'''
pollen command line client setup.py

installs a python package called "pollen" and
generates a script in the user's path called "pollen"
'''

from setuptools import setup

setup(
    name="pollen",
    version="0.9.10",
    install_requires=[
        'autobahn[asyncio]',
        'trollius'
    ],
    entry_points={
        'console_scripts': [
            'pollen=pollen.main:main',
        ],
    },
    packages=['pollen'],
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

