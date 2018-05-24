#!/bin/env python3

""" PR_MESSAGE_GEN
Various utilities functions.
"""


def fold_block(title: str, content: str) -> str:
    res = '<details><summary>' + title + '</summary>\n\n'
    res += content
    return res + '</details>\n'


def get_test_method(file_path: str, test_name: str) -> str:
    res = ''
    with open(file_path, 'r') as test_file:
        log_line = False
        indent_level = ''
        for line in test_file:
            if 'public void ' + test_name + '()' in line:
                log_line = True
                indent_level = line[: len(line) - len(line.lstrip())]
            elif line.startswith(indent_level + '}'):
                return res + line
            if log_line:
                res += line
    raise ValueError("Couldn't get the test method.")
