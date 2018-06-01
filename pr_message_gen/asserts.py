#!/bin/env python3

""" PR_MESSAGE_GEN
Functions related to assertions.
"""
from collections import Counter


import utils


MAX_NB_ASSERTS = 10


def is_trycatch(assert_stmt):
    return assert_stmt[:3] == 'try'


def is_assign(assert_stmt):
    return ('=' in assert_stmt and
            not assert_stmt.lstrip().startswith('org.junit.Assert.assert'))


def is_assert(assert_stmt):
    return (not is_trycatch(assert_stmt)) and (not is_assign(assert_stmt))


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


def __is_direct_variable_test(assign_stmt, variable_tested):
    left_part = list(assign_stmt.split(variable_tested)[-1])
    try:
        while left_part[0] == ')' or left_part[0] == ';':
            left_part.pop(0)
        return False
    except IndexError:
        return True


def __get_first_argument(assert_stmt):
    """
    Return the first argument of an assert with 2 arguments.
    """
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
    return assert_stmt[position_1st:position-1]


def __get_a_amp_target(a_amp):
    """
    Extract the variable/method tested by an a-amplification.
    """
    assert_stmt = a_amp["newValue"]
    if is_trycatch(assert_stmt):
        return __get_trycatch_target(assert_stmt)
    if is_assign(assert_stmt):
        return __get_assign_target(assert_stmt)
    # assert statement
    return __get_assert_target(assert_stmt)


def __sort_asserts(a_amps):
    trycatchs = []
    assigns = []
    asserts = []
    while a_amps:
        amplification = a_amps.pop(0)
        if is_trycatch(amplification['newValue']):
            trycatchs += [amplification]
        elif is_assign(amplification['newValue']):
            assigns += [amplification]
        else:
            asserts += [amplification]
    return trycatchs, assigns, asserts


def __get_variable_name(assign):
    return assign['newValue'].split(' ')[1]


def __describe_trycatch(trycatch):
    res = "#### Generated an exception handler for `" + \
        __get_a_amp_target(trycatch) + "` aroung the whole test.\n"
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
        if nb_related_asserts > 1:
            res += "#### Generated " + str(nb_related_asserts) + \
                " assertions for the observations from `" + \
                __get_a_amp_target(assign) + "`.\n"
        else:
            res += "#### Generated an assertion for an observation from `" + \
                __get_a_amp_target(assign) + "`.\n"
        res += "```diff\n+ " + assign['newValue'].replace('\n', '\n+ ') + \
            "\n```\n"

        if nb_asserts < MAX_NB_ASSERTS:
            if (nb_related_asserts == 1 and
                __is_direct_variable_test(related_asserts[0]['newValue'],
                                          assign_variable)):
                res += __paraphrase_assert(related_asserts[0]['newValue'],
                                           assign_variable)
            else:
                list_title = "Assertion" + ('s' if nb_related_asserts > 1
                                            else '')
                list_asserts = ''
                for i in range(nb_related_asserts):
                    list_asserts += str(i+1) + '. ' + \
                        __describe_assert_variable(
                            related_asserts[i]['newValue'],
                            assign_variable)
                res += utils.fold_block(list_title, list_asserts)

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


def __paraphrase_assert(assert_stmt: str, target: str) -> str:
    beggining = "Check that `" + target + "` "
    if assert_stmt.startswith('org.junit.Assert.assertEquals'):
        if __is_direct_variable_test(assert_stmt, target):
            return beggining + 'is equal to `' + \
                __get_first_argument(assert_stmt) + '`.\n'
        else:
            return beggining + 'returns `' + \
                __get_first_argument(assert_stmt) + '`.\n'
    if assert_stmt.startswith('org.junit.Assert.assertFalse'):
        if __is_direct_variable_test(assert_stmt, target):
            return beggining + " is false.\n"
        else:
            return beggining + " returns false.\n"
    if assert_stmt.startswith('org.junit.Assert.assertTrue'):
        if __is_direct_variable_test(assert_stmt, target):
            return beggining + " is true.\n"
        else:
            return beggining + " returns true.\n"
    if assert_stmt.startswith('org.junit.Assert.assertNull'):
        if __is_direct_variable_test(assert_stmt, target):
            return beggining + " is null.\n"
        else:
            return beggining + " returns null.\n"
    raise ValueError("Unknown assert function.")


def __describe_assert_variable(assert_stmt: str, variable: str) -> str:
    """
    Natural language paraphrasing of an assert that checks something on a
    variable.

    Assumes that the assertion tests the return value of a method call on the
    variable.
    """
    method_called = list(assert_stmt.split(variable)[-1].strip())
    if method_called[-1] == ';':
        method_called = method_called[:-1]
    while method_called[0] == ')':  # remove parentheses
        method_called.pop(0)
    method_called.pop(0)  # remove dot
    extra_closing = method_called.count(')') - method_called.count('(')
    if extra_closing:
        method_called = method_called[: -extra_closing]
    method_called = ''.join(method_called)

    return __paraphrase_assert(assert_stmt, method_called)


def describe_asserts(a_amps):
    """
    Natural language description of a set of assertions.
    """
    trycatchs, assigns, new_asserts = __sort_asserts(a_amps[:])
    res = ""
    nb_asserts = len(new_asserts)
    useless_assigns = []
    nb_a_amps = nb_asserts + len(trycatchs) + len(assigns)

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
        asserts_targeting = [assertion for assertion in new_asserts
                             if __get_a_amp_target(assertion) == target]
        if __is_direct_variable_test(asserts_targeting[0]['newValue'], target):
            res += "#### Generated " + str(nb_asserts) + " assertion" + \
                ("s" if nb_asserts > 1 else "") + \
                " for the value of `" + target + "`.\n\n"
        else:
            res += "#### Generated " + str(nb_asserts) + " assertion" + \
                ("s" if nb_asserts > 1 else "") + \
                " for the return value of `" + target + "`.\n\n"
        if nb_asserts < MAX_NB_ASSERTS:  # add diff
            similar_asserts = Counter([assertion['newValue']
                                       for assertion in asserts_targeting])
            for assert_stmt in similar_asserts:
                if similar_asserts[assert_stmt] > 1:
                    res += str(similar_asserts[assert_stmt]) + \
                        " identical assertions:\n"
                res += "```diff\n+ " + assert_stmt + "\n```\n\n"

    return res[:-1], useless_assigns, nb_a_amps - len(useless_assigns)
