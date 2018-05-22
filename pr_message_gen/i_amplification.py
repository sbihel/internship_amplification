#!/bin/env python3

""" PR_MESSAGE_GEN
Functions related to input amplifications.
"""


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
        return "Added new " + amplification["role"] + " to `" + \
            amplification["parent"] + "`.\n" + diff
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
        return "Modified " + amplification["role"] + ' of `' + \
            amplification['parent'] + "`.\n" + diff
    else:
        raise ValueError("Unknown category.")
