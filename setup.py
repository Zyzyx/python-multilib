#!/usr/bin/python
from setuptools import setup, find_packages
import distutils.command.sdist
import os

distutils.command.sdist.sdist.default_format = {"posix": "bztar"}

# recursively scan for python modules to be included
package_root_dirs = ["multilib"]
packages = set()
for package_root_dir in package_root_dirs:
    for root, dirs, files in os.walk(package_root_dir):
        if "__init__.py" in files:
            packages.add(root.replace("/", "."))
packages = sorted(packages)

setup(
    name = "python-multilib",
    version = "1.1",
    author = "Jay Greguske",
    author_email = "jgregusk@redhat.com",
    description = ("module for determining if a package is multilib"),
    license = "GPLv2",
    url = "https://github.com/Zyzyx/python-multilib.git",
    packages = packages,
    install_requires = ['six'],
    package_data = {'': ['README.md', 'LICENSE']},
    data_files = [('/etc', ['etc/multilib.conf'])],
    test_suite      = "tests",
)
