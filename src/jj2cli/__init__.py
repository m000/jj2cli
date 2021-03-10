#! /usr/bin/env python

""" j2cli main file """
import pkg_resources

__author__  = "Manolis Stamatogiannakis"
__email__   = "mstamat@gmail.com"
__version__ = pkg_resources.get_distribution('jj2cli').version

from jj2cli.cli import main

if __name__ == '__main__':
    main()
