from setuptools import find_packages, setup

setup(
    name="envbee-sdk",
    version="1.7.2",
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
    packages=find_packages(exclude=["*.pyc", "__pycache__", "*/__pycache__"]),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
