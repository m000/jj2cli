#! /usr/bin/env python

""" j2cli main file """
import pkg_resources

__author__  = "Manolis Stamatogiannakis"
__email__   = "mstamat@gmail.com"
__version__ = pkg_resources.get_distribution('j2cli').version

from j2cli.cli import render, dependencies

if __name__ == '__main__':
    render()
