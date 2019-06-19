from setuptools import setup

setup(
    name="entries",
    version="0.1.1",
    py_modules=["cli"],
    install_requires=["pyyaml", "mf2py", "click", "requests"],
    entry_points={"console_scripts": ["entries = cli:cli"]},
)
