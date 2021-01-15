import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="wander",
    version="0.0.1",
    author="Dominic Tarro",
    author_email="dominic.tarro@gmail.com",
    description="Asynchronous API wrapper for Wandbox (https://wandbox.org/api)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dominictarro/wander",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.9',
)