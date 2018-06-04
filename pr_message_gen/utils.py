#!/bin/env python3

""" PR_MESSAGE_GEN
Various utilities functions.
"""
from functools import reduce
from typing import Dict, List


def fold_block(title: str, content: str) -> str:
    """
    Add html tags so that GitHub will fold/hide the content.
    """
    res = '<details><summary>' + title + '</summary>\n\n'
    res += content
    return res + '</details>\n'


def get_test_method(file_path: str, test_name: str,
                    unindent: bool = False) -> str:
    """
    Get the whole test method.
    """
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


def __join_skipped_parents(
        parenting_lists: List[List[str]]) -> List[List[str]]:
    """
    Try to join lists of parenting that have a skipped parent.

    We can only handle one skipped parent, as the amplification process
    wouldn't have produced an amplified test with 2 levels of useless parents.
    """
    if len(parenting_lists) < 2:
        return parenting_lists
    insert_al = parenting_lists[0]
    first_el = insert_al[0]
    last_el = insert_al[-1]
    for lists_i in range(1, len(parenting_lists)):
        lst = parenting_lists[lists_i]
        if last_el in lst[0]:
            parenting_lists[lists_i] = insert_al + lst
            return __join_skipped_parents(parenting_lists[1:])
        elif lst[-1] in first_el:
            parenting_lists[lists_i] += lst
            return __join_skipped_parents(parenting_lists[1:])
    return [insert_al] + __join_skipped_parents(parenting_lists[1:])


def order_tests(tests_parenting: Dict[str, str]) -> List[List[str]]:
    """
    Order by parenting (not just direct parenting).
    """
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

    # lists of direct parenting, now we try to group them if a parent was
    # skipped
    ordered_lists = __join_skipped_parents(ordered_lists)

    assert(len(tests_parenting) == reduce(lambda x, y: x + y,
                                          [len(test_list)
                                           for test_list in ordered_lists]))
    return ordered_lists


def is_not_original(amplified_test_name: str, parent_name: str = None) -> bool:
    # TODO assumes that the project uses camelCase
    return amplified_test_name != parent_name or '_' in amplified_test_name


def index_in_mutation_score(mutation_score, test_name: str) -> int:
    for i in range(len(mutation_score['testCases'])):
        if mutation_score['testCases'][i]['name'] == test_name:
            return i
    return None


if __name__ == '__main__':
    test_parenting = {'2': '1', '15': '14', '3': '2', '16': '15', '14': '14',
                      '1': '0', '0': '0', '4': '3'}
    print(test_parenting, order_tests(test_parenting))
