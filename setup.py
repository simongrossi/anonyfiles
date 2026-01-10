from setuptools import setup, find_packages

setup(
    name="anonyfiles",
    version="0.1.0",
    description="A suite of tools to anonymize and deanonymize files.",
    author="Simon Grossi",
    packages=find_packages(),
    # This file allows the project to be installed in editable mode with `pip install -e .`
)