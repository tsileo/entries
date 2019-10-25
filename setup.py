from pathlib import Path
from setuptools import setup

README = Path(__file__).parent.joinpath("README.md").resolve()

setup(
    name="entries",
    version="0.1.2",
    url="https://github.com/tsileo/entries",
    description="Micropub client for the terminal",
    long_description=README.read_text(),
    long_description_content_type="text/markdown",
    author="Thomas Sileo",
    author_email="t@a4.io",
    license="OSI Approved :: ISC License (ISCL)",
    py_modules=["cli"],
    install_requires=["pyyaml", "mf2py", "click", "requests"],
    entry_points={"console_scripts": ["entries = cli:cli"]},
    python_requires=">=3.6",
)
