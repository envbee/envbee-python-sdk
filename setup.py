from setuptools import find_packages, setup

import sys

sys.path[0:0] = ["envbee_sdk"]

from version import __version__  # type: ignore # noqa: E402

setup(
    name="envbee-sdk",
    version=__version__,
    author="envbee",
    author_email="info@envbee.dev",
    description="envbee SDK for Python",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/envbee/envbee-python-sdk",
    install_requires=[
        "diskcache",
        "platformdirs",
        "requests",
        "cryptography",
    ],
    include_package_data=True,
    packages=find_packages(exclude=["*.pyc", "__pycache__", "*/__pycache__", "tests"]),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
)
