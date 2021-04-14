#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
@author: HJK 
@file: setup.py 
@time: 2019-01-26

打包配置文件

"""
import os
import sys
import setuptools

# 'setup.py publish' shortcut.
if sys.argv[-1] == "publish":
    os.system("rm -rf dist")
    os.system("python setup.py sdist bdist_wheel")
    os.system("twine upload dist/*")
    sys.exit()

setuptools.setup(
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    test_suite="tests",
    entry_points={"console_scripts": ["music-dl = music_dl.__main__:main"]},
    install_requires=["requests", "click", "pycryptodome", "prettytable"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Internet",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Multimedia",
        "Topic :: Multimedia :: Sound/Audio",
        "Topic :: Utilities",
    ],
)
