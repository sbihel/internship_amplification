#!/bin/env python3

""" PR_MESSAGE_GEN
Functions related to assertions.
"""
from collections import Counter


MAX_NB_ASSERTS = 10


def __is_trycatch(assert_stmt):
    return assert_stmt[:3] == 'try'


def __is_assign(assert_stmt):
    return ('=' in assert_stmt and
            not assert_stmt.lstrip().startswith('org.junit.Assert.assert'))


def __is_assert(assert_stmt):
    return (not __is_trycatch(assert_stmt)) and (not __is_assign(assert_stmt))


def __get_assert_target(assertion):
    """
    Extract the variable/method tested by an assertion.
    """
    assert_stmt = assertion["newValue"]
    if __is_trycatch(assert_stmt):
        return assert_stmt.split('} catch (')[-1].split(' ')[0]
    elif __is_assign(assert_stmt):
        return assert_stmt.split('=')[-1].lstrip()
    else:  # assert statement
        # parse the line, extracting the target of the assert
        # javalang was taking a long time, and could not pretty print
        position = 0  # position of the arguments of the assert
        for char in assert_stmt:
            position += 1
            if char == '(':
                break
        position_1st = position

        looking_for = [',']
        skip_next = False
        for char in assert_stmt[position_1st:]:
            position += 1
            if skip_next:
                skip_next = False
                continue

            if char == looking_for[0]:
                looking_for.pop(0)
                if looking_for == []:
                    break
            elif char == '\"':
                looking_for = ['\"'] + looking_for
            elif char == '(':
                looking_for = [')'] + looking_for
            elif char == '\\':
                skip_next = True
                continue

        if looking_for != []:  # only 1 argument, go back to beginning
            position = position_1st
        return assert_stmt[position:-1].strip()


def describe_asserts(new_asserts):
    """
    Natural language description of a set of assertions.
    """
    new_asserts_shortname = []
    for assertion in new_asserts:
        new_asserts_shortname += [__get_assert_target(assertion)]

    count_asserts = Counter(new_asserts_shortname)
    res = ""
    for shortname in count_asserts:
        nb_asserts = count_asserts[shortname]
        res += "Generated " + str(nb_asserts) + " assertion" + \
            ("s" if nb_asserts > 1 else "") + " for the return value of `" + \
            shortname + "`.\n"
        if len(new_asserts) < MAX_NB_ASSERTS:  # add diff
            for assertion in new_asserts:
                new_value = assertion["newValue"]
                if (__is_trycatch(new_value) and
                        __get_assert_target(assertion) == shortname):
                    lines = new_value.split('\n')
                    lines[0] = '+ ' + lines[0]
                    lines[-1] = '+ ' + lines[-1]
                    lines[-2] = '+ ' + lines[-2]
                    nb_lines_modified_end = 3
                    if lines[-3].lstrip()[0] == '}':
                        nb_lines_modified_end = 4
                        lines[-4] = '+ ' + lines[-4]
                    lines[-3] = '+ ' + lines[-3]
                    for i in range(1, len(lines)-nb_lines_modified_end):
                        lines[i] = '  ' + lines[i]
                    res += "```diff\n" + '\n'.join(lines) + "\n```\n"
                elif (__is_assign(new_value) and
                      new_value.split('=')[-1].lstrip() == shortname):
                    res += "```diff\n+ " + new_value.replace('\n', '\n+ ') + \
                        "\n```\n"
                elif __get_assert_target(assertion) == shortname:
                    res += "```diff\n+ " + new_value + "\n```\n"
    return res[:-1]
