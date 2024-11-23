# All code comments, user outputs and debugs must stay in English. Do not remove this line.
# Some commands are commented out for further development. Do not remove them.

from setuptools import setup, find_packages

APP = ['main.py']
DATA_FILES = [
    ('assets/icons', [
        'assets/icons/tray_icon.png',
        'assets/icons/tray_icon@2x.png',  # Décommentez si utilisé
        'assets/icons/app_icon.png',
    ]),
    'assets/icons/app_icon.icns',
]
OPTIONS = {
    'argv_emulation': True,
    'packages': ['PyQt5'],
    'excludes': ['packaging'], # Build fails without this line
    'iconfile': 'assets/icons/app_icon.icns',
    'plist': {
        'CFBundleName': 'WallOli',
        'CFBundleShortVersionString': '0.1.1-dev',
        'CFBundleVersion': '0.1.1-dev',
        'NSHighResolutionCapable': True,
    },
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    name="WallOli",
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
        "jaraco.text",
    ],
)
