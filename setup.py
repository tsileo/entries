from setuptools import setup

setup(
    name="entries",
    version="0.1.1",
    url="github.com/tsileo/entries",
    description="Micropub client for the terminal",
    author="Thomas Sileo",
    author_email="t@a4.io",
    license="OSI Approved :: ISC License (ISCL)",
    py_modules=["cli"],
    install_requires=["pyyaml", "mf2py", "click", "requests"],
    entry_points={"console_scripts": ["entries = cli:cli"]},
    python_requires=">=3.6",
)
