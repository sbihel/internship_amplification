#!/bin/env python3

""" PR_MESSAGE_GEN
Various utilities functions.
"""
from functools import reduce
from typing import Dict


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
        test_annotation = ''
        for line in test_file:
            if '@Test' in line:
                test_annotation = line
            if 'public void ' + test_name + '()' in line:
                log_line = True
                indent_level = line[: len(line) - len(line.lstrip())]
                if test_annotation != line:
                    res = test_annotation
            elif line.startswith(indent_level + '}'):
                res += line
                if unindent:
                    res = res[len(indent_level):].replace('\n' + indent_level,
                                                          '\n')
                return res
            if log_line:
                res += line
    raise ValueError("Couldn't get the test method.")


def order_tests(tests_parenting: Dict[str, str]):
    reverse_parenting = {}
    for test, parent in tests_parenting.items():
        if parent not in reverse_parenting:
            reverse_parenting[parent] = [test]
        else:
            reverse_parenting[parent] += [test]

    ordered_lists = []
    for test in tests_parenting:
        test_parent = tests_parenting[test]
        for linked_list_i in range(len(ordered_lists)):
            linked_list = ordered_lists[linked_list_i]
            if (len(linked_list) and test in reverse_parenting and
                    linked_list[0] in reverse_parenting[test]):
                ordered_lists[linked_list_i] = [test] + linked_list
                break
            for test_i in range(len(linked_list)):
                if linked_list[test_i] == test_parent:
                    if test_i == len(linked_list) - 1:
                        linked_list += [test]
                    else:
                        linked_list = linked_list[:test_i+1] + [test] + \
                            linked_list[test_i+1:]
                    break
            else:
                continue
            break
        else:
            ordered_lists += [[test]]
    assert(len(tests_parenting) == reduce(lambda x, y: x + y,
                                          [len(test_list)
                                           for test_list in ordered_lists]))
    return ordered_lists


if __name__ == '__main__':
    test_parenting = {'2': '1', '15': '14', '3': '2', '16': '15', '14': '14',
                      '1': '0', '0': '0', '4': '3'}
    print(test_parenting, order_tests(test_parenting))
