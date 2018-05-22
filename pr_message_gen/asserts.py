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


def __get_trycatch_target(trycatch_stmt):
    return trycatch_stmt.split('} catch (')[-1].split(' ')[0]


def __get_assign_target(assign_stmt):
    return '='.join(assign_stmt.split('=')[1:]).strip()


def __get_assert_target(assert_stmt):
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


def __get_a_amp_target(a_amp):
    """
    Extract the variable/method tested by an a-amplification.
    """
    assert_stmt = a_amp["newValue"]
    if __is_trycatch(assert_stmt):
        return __get_trycatch_target(assert_stmt)
    if __is_assign(assert_stmt):
        return __get_assign_target(assert_stmt)
    # assert statement
    return __get_assert_target(assert_stmt)


def __sort_asserts(a_amps):
    trycatchs = []
    assigns = []
    asserts = []
    while a_amps:
        amplification = a_amps.pop(0)
        if __is_trycatch(amplification['newValue']):
            trycatchs += [amplification]
        elif __is_assign(amplification['newValue']):
            assigns += [amplification]
        else:
            asserts += [amplification]
    return trycatchs, assigns, asserts


def __get_variable_name(assign):
    return assign['newValue'].split(' ')[1]


def __describe_trycatch(trycatch):
    res = "#### Generated an exception handler for `" + \
        __get_a_amp_target(trycatch) + "`.\n"
    lines = trycatch["newValue"].split('\n')
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
    return res


def __describe_assign(assign, new_asserts, new_asserts_targets, nb_asserts):
    res = ""
    assign_variable = __get_variable_name(assign)
    i = 0
    related_asserts = []
    asserts_done = []
    useless_assigns = []
    for assertion in new_asserts:
        if assign_variable in new_asserts_targets[i]:
            related_asserts += [assertion]
            asserts_done += [i]
        i += 1
    nb_related_asserts = len(related_asserts)
    if nb_related_asserts:
        res += "#### Generated " + str(nb_related_asserts) + " assertion" + \
            ('s' if nb_related_asserts > 1 else '') + \
            " for the observations from `" + __get_a_amp_target(assign) + \
            "`.\n"
        res += "```diff\n+ " + assign['newValue'].replace('\n', '\n+ ') + \
            "\n```\nAssertion" + ('s' if nb_related_asserts > 1 else '') + \
            ":\n"
        if nb_asserts < MAX_NB_ASSERTS:
            for related_assert in related_asserts:
                res += "```diff\n+ " + related_assert['newValue'] + "\n```\n"

        for index in reversed(asserts_done):
            new_asserts.pop(index)
            new_asserts_targets.pop(index)
    else:  # seemingly useless amplification
        useless_assigns += [assign]

    return res, useless_assigns


def __describe_assign_with_assert(assign):
    res = "#### Generated a bundle input amplification with assertions.\n"
    stmt = assign['newValue']
    # Remove overindented (non-first) lines
    if stmt[0] != '\t' and stmt.split('\n')[1][0] == '\t':
        stmt = stmt.replace('\n\t', '\n')
    res += "```diff\n+ " + stmt.replace('\n', '\n+ ') + "\n```\n\n"
    return res


def describe_asserts(a_amps):
    """
    Natural language description of a set of assertions.
    """
    trycatchs, assigns, new_asserts = __sort_asserts(a_amps[:])
    res = ""
    nb_asserts = len(new_asserts)
    useless_assigns = []

    # Try/catchs first.
    for trycatch in trycatchs:
        res += __describe_trycatch(trycatch)

    new_asserts_targets = []
    for assertion in new_asserts:
        new_asserts_targets += [__get_a_amp_target(assertion)]

    # Group assertions by the variable they're testing.
    for assign in assigns:
        if 'org.junit.Assert' not in assign['newValue']:  # normal assign
            message, useless_assigns_ = __describe_assign(assign, new_asserts,
                                                          new_asserts_targets,
                                                          nb_asserts)
            if message:
                res += message + '\n'
            useless_assigns += useless_assigns_
        else:  # assign with assert
            res += __describe_assign_with_assert(assign)

    # Remaining assertions.
    count_asserts = Counter(new_asserts_targets)
    for target in count_asserts:
        nb_asserts = count_asserts[target]
        res += "#### Generated " + str(nb_asserts) + " assertion" + \
            ("s" if nb_asserts > 1 else "") + " for the return value of `" + \
            target + "`.\n\n"
        if nb_asserts < MAX_NB_ASSERTS:  # add diff
            for assertion in new_asserts:
                new_value = assertion["newValue"]
                if __get_a_amp_target(assertion) == target:
                    res += "```diff\n+ " + new_value + "\n```\n\n"

    return res[:-1], useless_assigns
