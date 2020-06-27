import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="gphotos-export-jcontini",
    version="0.0.2",
    author="Joe Contini",
    author_email="joe@contini.co",
    description="Export Google Photos from Takeout",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jcontini/gphotos-export",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)