#!/usr/bin/python
from setuptools import setup, find_packages
import distutils.command.sdist

distutils.command.sdist.sdist.default_format = {"posix": "bztar"}

setup(
    name = "python-multilib",
    version = "1.1",
    author = "Jay Greguske",
    author_email = "jgregusk@redhat.com",
    description = ("module for determining if a package is multilib"),
    license = "GPLv2",
    url = "https://github.com/Zyzyx/python-multilib.git",
    packages = find_packages(),
    package_data = {'': ['README.md', 'LICENSE']},
    data_files = [('/etc', ['etc/multilib.conf'])],
    scripts = ['multilib/multilib_test_data'],
    test_suite      = "tests",
)
