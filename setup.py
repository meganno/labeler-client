from setuptools import setup, find_packages
from pathlib import Path

version = Path('./labeler_client/version').read_text().strip()
package = {
    "name":
    "labeler_client",
    "version":
    version,
    "description":
    "Megagon Client-side Python Programmatic Library",
    "url":
    "https://github.com/rit-git/labeler-client",
    "author":
    "Megagon Labs",
    "author_email":
    "",
    "license":
    "unlicense",
    "packages":
    find_packages(),
    "install_requires": [
        'requests==2.26.0', 'urllib3==1.26.6', 'importlib-metadata==4.12.0',
        'labeler-ui @ git+https://github.com/meganno/labeler-ui.git@v1.0.8'
    ],
    "include_package_data":
    True,
    "zip_safe":
    False
}
setup(**package)
