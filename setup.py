#!/usr/bin/python

import os
import shlex
import subprocess
import sys

from setuptools import find_packages, setup

import InvoiceGenerator

from pathlib import Path
from pkg_resources import RequirementParseError

def parse_requirements(req_path="requirements.txt"):
    """
    Return a list of requirement strings, ignoring comments and indexes.
    """
    req_file = Path(__file__).with_name(req_path)
    if not req_file.exists():
        return []

    requirements = []
    for line in req_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("--"):
            continue
        try:
            # Validate the requirement string
            from pkg_resources import Requirement
            Requirement.parse(line)
        except RequirementParseError:
            raise SystemExit(f"Bad requirement in {req_path!r}: {line!r}")
        requirements.append(line)
    return requirements


version = InvoiceGenerator.__versionstr__

# release a version, publish to GitHub and PyPI
if sys.argv[-1] == "publish":

    def command(cmd):
        subprocess.check_call(shlex.split(cmd))

    command("git tag v" + version)
    command("git push --tags origin master:master")
    command("python setup.py sdist upload")
    sys.exit()


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


description = ""

for file_ in ("README", "CHANGES", "CONTRIBUTORS"):
    description += read("%s.rst" % file_) + "\n\n"


setup(
    name="InvoiceGenerator",
    version=version,
    author="Adam Strauch",
    author_email="cx@initd.cz",
    description="Library to generate PDF invoice.",
    license="BSD",
    keywords="invoice invoices generator",
    url="https://github.com/creckx/InvoiceGenerator",
    packages=find_packages(exclude=["ez_setup", "examples", "tests"]),
    long_description=description,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.5",
        "Topic :: Utilities",
        "License :: OSI Approved :: BSD License",
    ],
    install_requires=parse_requirements(),   # ← populated from requirements.txt
    tests_require=[
        "PyPDF2",
        "xmlunittest",
        "future",
        "six",
    ],
    extras_require={
        "dev": [
            "flake8",
            "flake8-blind-except",
            "flake8-comprehensions",
            "flake8-import-order",
            "flake8-tidy-imports",
        ],
        "docs": "sphinx",
    },
    include_package_data=True,
    test_suite="tests",
)
