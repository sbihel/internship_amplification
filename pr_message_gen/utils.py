#!/bin/env python3

""" PR_MESSAGE_GEN
Various utilities functions.
"""


def fold_block(title: str, content: str) -> str:
    res = '<details><summary>' + title + '</summary>\n\n'
    res += content
    return res + '</details>\n'


def get_test_method(file_path: str, test_name: str,
                    unindent: bool = False) -> str:
    res = ''
    with open(file_path, 'r') as test_file:
        log_line = False
        indent_level = ''
        for line in test_file:
            if 'public void ' + test_name + '()' in line:
                log_line = True
                indent_level = line[: len(line) - len(line.lstrip())]
            elif line.startswith(indent_level + '}'):
                res += line
                if unindent:
                    res = res[len(indent_level):].replace('\n' + indent_level,
                                                          '\n')
                return res
            if log_line:
                res += line
    raise ValueError("Couldn't get the test method.")
