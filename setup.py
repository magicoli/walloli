from setuptools import setup, find_packages

setup(
    name="walloli",
    version="0.1.1-dev",
    author="Olivier van Helden",
    author_email="olivier@van-helden.net",
    description="A cross-platform video wall player",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/magicoli/walloli",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.12',
    install_requires=[
        "PyQt5",
        "python-vlc",
    ],
)
