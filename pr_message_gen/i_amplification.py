#!/bin/env python3

""" PR_MESSAGE_GEN
Functions related to input amplifications.
"""


USELESS_PARENTS = ['CtBlockImpl']
USELESS_ROLES = ['child', 'statement']


def __add_amp(amplification):
    amp_tokens = amplification['newValue'].lstrip().split(' ')
    nb_tokens = len(amp_tokens)
    if nb_tokens > 2 and amp_tokens[2] == '=':  # new assignment
        return 'Created new variable `' + amp_tokens[1] + '`.\n'
    elif nb_tokens > 1 and amp_tokens[1] == '=':  # change value of variable
        return 'Modified the value of `' + amp_tokens[0] + '`.\n'
    else:
        if (amplification['role'] in USELESS_ROLES and
                amplification['parent'].split('.')[-1].split('@')[0]
                in USELESS_PARENTS):
            return "Added new statement.\n"
        else:
            return "Added new " + amplification["role"] + " to `" + \
                amplification["parent"] + "`.\n"


def __modify_amp(amplification):
    amp_tokens = amplification['newValue'].lstrip().split(' ')
    nb_tokens = len(amp_tokens)
    if nb_tokens > 2 and amp_tokens[2] == '=':  # new assignment
        return 'Modified variable `' + amp_tokens[1] + '` initialization.\n'
    elif nb_tokens > 1 and amp_tokens[1] == '=':  # change value of variable
        return 'Modified variable `' + amp_tokens[0] + ' assignment`.\n'
    else:
        if (amplification['role'] in USELESS_ROLES and
                amplification['parent'].split('.')[-1].split('@')[0]
                in USELESS_PARENTS):
            return ""
        else:
            return "Modified " + amplification["role"] + ' of `' + \
                amplification['parent'] + "`.\n"


def describe_amplification(amplification):
    """
    Natural language description of an amplification.
    """
    categ = amplification["ampCategory"]
    if categ == "ASSERT":
        raise ValueError("Not for assertions.")
    elif categ == "ADD":
        new_value_diff = amplification["newValue"].replace('\n', '\n+ ')
        diff = "```diff\n+ " + new_value_diff + "\n```\n"
        return __add_amp(amplification) + diff
    elif categ == "REMOVE":
        old_value_diff = amplification["oldValue"].replace('\n', '\n- ')
        diff = "```diff\n- " + old_value_diff + "\n```\n"
        return "Removed " + amplification["role"] + " from `" + \
            amplification["parent"] + "`.\n" + diff
    elif categ == "MODIFY":
        old_value_diff = amplification["oldValue"].replace('\n', '\n- ')
        new_value_diff = amplification["newValue"].replace('\n', '\n+ ')
        diff = "```diff\n- " + old_value_diff + "\n+ " + new_value_diff + \
            "\n```\n"
        return __modify_amp(amplification) + diff
    else:
        raise ValueError("Unknown category.")
