from setuptools import setup

setup(
    name="envbee-sdk",
    version="1.2.0",
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
    ],
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
