from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in foodna/__init__.py
from foodna import __version__ as version

setup(
	name="foodna",
	version=version,
	description="Custom Doctype to update item ref code and item price",
	author="smb",
	author_email="usamanaveed9263@gmail.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
