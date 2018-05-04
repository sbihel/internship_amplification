#!/bin/env python3

""" PR_MESSAGE_GEN
"""
import argparse
import json
from os import path


def describe_amplification(amplification):
    """
    Natural language description of an amplification
    """
    categ = amplification["ampCategory"]
    if categ == "ASSERT":
        return "Added new assertion for" + \
            amplification["newValue"].split('=')[-1]
    elif categ == "ADD":
        return "Added new " + \
            amplification["role"] + " `" + amplification["newValue"] + "`"
    elif categ == "REMOVE":
        return "Remove " + amplification["role"] + \
            " from " + amplification["parent"]
    elif categ == "MODIFY":
        return "Modified " + amplification["role"] + ", from " + \
            amplification["oldValue"] + " to " + amplification["newValue"]


def describe_mutant(mutant):
    """
    Natural language description of a mutant
    """
    return "Bug introduced in `" + mutant["locationClass"].split('.')[-1] + \
        '#' + mutant["locationMethod"] + "` at line " + \
        str(mutant["lineNumber"]) + ", using " + mutant["ID"].split('.')[-1]


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
    command_parser.add_argument(
        '-test', '--test', type=str,
        help='path for both mutation_score report and amplification log')

    opts, _ = command_parser.parse_known_args()

    if opts.test:
        if not path.exists(opts.test + '_mutants_killed.json'):
            return
        with open(opts.test+'_mutants_killed.json', 'r') as json_file:
            mutation_score = json.load(json_file)
        with open(opts.test+'_amp_log.json', 'r') as json_file:
            amplification_log = json.load(json_file)
    else:
        if not path.exists(opts.mutation_score):
            return
        with open(opts.mutation_score, 'r') as json_file:
            mutation_score = json.load(json_file)
        with open(opts.amplification_log, 'r') as json_file:
            amplification_log = json.load(json_file)

    amplified_tests = (test_case["name"]
                       for test_case in mutation_score["testCases"])
    i = 0
    for amplified_test in list(amplification_log):
        if amplified_test not in amplified_tests:
            amplification_log.pop(amplified_test, None)
        else:
            print("")
            print("\t" + amplified_test)
            for amplification in amplification_log[amplified_test]:
                print(describe_amplification(amplification))
            print("\tKilled mutants")
            for mutant in mutation_score["testCases"][i]["mutantsKilled"]:
                print(describe_mutant(mutant))
        i += 1


if __name__ == '__main__':
    main()
