#! /usr/bin/env python
""" j2cli main file """
import importlib.metadata

__author__  = "Manolis Stamatogiannakis"
__email__   = "mstamat@gmail.com"
__version__ =  importlib.metadata.version('jj2cli')

from jj2cli.cli import render

if __name__ == '__main__':
    render()
