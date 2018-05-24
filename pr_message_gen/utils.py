#!/bin/env python3

""" PR_MESSAGE_GEN
Various utilities functions.
"""


def fold_block(title: str, content: str) -> str:
    res = '<details><summary>' + title + '</summary>\n\n'
    res += content
    return res + '</details>\n'
