# -*- coding: utf-8 -*-
"""
Created on Sun Jan 27 09:43:16 2013

@author: Daniel
"""
#from pykat import __version__ as version
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
    
import os
import subprocess

# Fetch version from git tags, and write to version.py.
# Also, when git is not available (PyPi package), use stored version.py.
version_py = os.path.join(os.path.dirname(__file__), 'pykat', '_version.py')

try:
    version_git = subprocess.check_output(["git", "describe","--long"]).decode('utf8').rstrip()
    version_git = ".".join(version_git.split('-')[:2])
except:
    with open(version_py, 'r') as fh:
        version_git = open(version_py).read().strip().split('=')[-1].replace('"','')
    
version_msg = "# Do not edit this file, pipeline versioning is governed by git tags"

with open(version_py, 'w') as fh:
    fh.write(version_msg + os.linesep + ("__version__=\"%s\"" % version_git))

print("!!!! Printing version to:", version_py)

REQUIREMENTS = [i.strip() for i in open("requirements.txt").readlines()]

setup(
    name='PyKat',
    version=version_git,
    author='Daniel Brown',
    author_email='finesse@star.sr.bham.ac.uk',
    packages=[x[0].replace("/",".") for x in os.walk("pykat") if "__" not in x[0]],
    url='http://pypi.python.org/pypi/PyKat/',
    license='GPL v2',
    description='Python interface and tools for FINESSE',
    long_description=open('README.md').read(),
    install_requires=REQUIREMENTS,
    package_data={'': ['optics/greedypoints/*.txt',
                       'ifo/aligo/files/*.kat',
                       'ifo/adv/files/*.kat',
                       'ifo/voyager/files/*.kat',
                       'style/*.mplstyle']},
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'pykat = pykat.__main__:cli'
            ],
        },
)
