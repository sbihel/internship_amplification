#!/bin/env python3

""" PR_MESSAGE_GEN
"""
import argparse
import json


def describe_amplification(amplification):
    categ = amplification["ampCategory"]
    if categ == "ASSERT":
        return "Added new assertion for" + amplification["newValue"].split('=')[-1]
    elif categ == "ADD":
        return "Added new " + amplification["role"]
    elif categ == "REMOVE":
        return "Remove " + amplification["role"] + \
            " from " + amplification["parent"]
    elif categ == "MODIFY":
        return "Modified " + amplification["role"] + ", from " + \
            amplification["oldValue"] + " to " + amplification["newValue"]


def main():
    """
    Function to run pr_message_gen.
    """
    command_parser = argparse.ArgumentParser()
    command_parser.add_argument(
        '-amplog', '--amplification_log', type=str,
        help='json file containing the amplification log')
    command_parser.add_argument(
        '-mutants', '--mutation_score', type=str,
        help='json file containing the mutation score report')

    opts, _ = command_parser.parse_known_args()

    with open(opts.amplification_log, 'r') as json_file:
        amplification_log = json.load(json_file)
    with open(opts.mutation_score, 'r') as json_file:
        mutation_score = json.load(json_file)

    amplified_tests = (test_case["name"]
                       for test_case in mutation_score["testCases"])
    for amplified_test in list(amplification_log):
        if amplified_test not in amplified_tests:
            amplification_log.pop(amplified_test, None)
        else:
            for amplification in amplification_log[amplified_test]:
                print(describe_amplification(amplification))


if __name__ == '__main__':
    main()
