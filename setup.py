#!/usr/bin/env python3

import setuptools

with open("README.rst", "r", encoding="utf-8") as f:
	long_description = f.read()

setuptools.setup(
	name="rezparser",
	version="1.0.0",
	description="A pure Python library for parsing Macintosh Rez source files",
	long_description=long_description,
	url="https://github.com/dgelessus/python-rezparser",
	author="dgelessus",
	license="MIT",
	classifiers=[
		"Development Status :: 4 - Beta",
		"Intended Audience :: Developers",
		"Topic :: Software Development :: Libraries :: Python Modules",
		"Topic :: Utilities",
		"License :: OSI Approved :: MIT License",
		"Operating System :: OS Independent",
		"Programming Language :: Python",
		"Programming Language :: Python :: 3",
		"Programming Language :: Python :: 3 :: Only",
		"Programming Language :: Python :: 3.6",
	],
	keywords="rez resource macintosh mac macos",
	python_requires=">=3.6",
	packages=["rezparser"],
	install_requires=["ply"],
)
