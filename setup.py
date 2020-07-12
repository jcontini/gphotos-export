import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="gphotos-export-jcontini",
    version="0.0.3",
    author="Joe Contini",
    author_email="joe@contini.co",
    description="Export Google Photos from Takeout",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jcontini/gphotos-export",
    packages=setuptools.find_packages(),
    include_package_data=True,
    install_requires=[
        'Click',
        'sqlite_utils',
        'piexif'
    ],
    entry_points='''
        [console_scripts]
        yourscript=gphotos_export.gphotos_export.cli:cli
    ''',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)