#!/bin/sh
find -type f -name '*.mako.py' -exec rm -f {} ';'
find -type f -name '*.pyc' -exec rm -f {} ';'
find -type f -name '*~' -exec rm -f {} ';'
