from os.path import splitext
from os.path import basename
from glob import glob

from setuptools import find_packages
from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="pyWirelessMbus",
    version="0.2.1",
    author="Karl Wolffgang",
    author_email="karlwolffgang@googlemail.com",
    description="A tool to receive and send Wireless-M-Bus messages.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/karlTGA/pyWirelessMbus",
    packages=find_packages("src"),
    package_dir={"": "src"},
    py_modules=[splitext(basename(path))[0] for path in glob("src/*.py")],
    include_package_data=True,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: MIT License",
        "Intended Audience :: Developers",
        "Operating System :: Unix",
        "Operating System :: POSIX",
    ],
    install_requires=["pyserial", "pyserial-asyncio"],
    python_requires=">=3.7.0",
)

