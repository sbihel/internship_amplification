#!/bin/env python3

""" PR_MESSAGE_GEN
"""
import argparse
import json
from os import path
from collections import Counter


def describe_amplification(amplification):
    """
    Natural language description of an amplification.
    """
    categ = amplification["ampCategory"]
    if categ == "ASSERT":
        raise ValueError("Not for assertions.")
    elif categ == "ADD":
        return "Added new " + \
            amplification["role"] + " `" + amplification["newValue"] + "`"
    elif categ == "REMOVE":
        return "Remove " + amplification["role"] + \
            " from " + amplification["parent"]
    elif categ == "MODIFY":
        return "Modified " + amplification["role"] + ", from " + \
            amplification["oldValue"] + " to " + amplification["newValue"]


def describe_asserts(new_asserts):
    """
    Natural language description of a set of assertions.
    """
    new_asserts_shortname = [assertion["newValue"].split(
        '=')[-1] for assertion in new_asserts]
    count_asserts = Counter(new_asserts_shortname)
    res = ""
    for shortname in count_asserts:
        res += str(count_asserts[shortname]
                   ) + " assertions for" + shortname + "\n"
    return res[:-1]


def describe_mutant(mutant):
    """
    Natural language description of a mutant.
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
        print("========== Class: " + opts.test.split('.')[-1] + " ==========")
        with open(opts.test+'_mutants_killed.json', 'r') as json_file:
            mutation_score = json.load(json_file)
        with open(opts.test+'_amp_log.json', 'r') as json_file:
            amplification_log = json.load(json_file)
    else:
        if not path.exists(opts.mutation_score):
            return
        print(
            "========== Class: " + opts.mutation_score.split('.')[-2] +
            " ==========")
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
            if i:
                print()
            print('===== Generated test: ' + amplified_test + ' =====')
            new_asserts = [
                amplification
                for amplification in amplification_log[amplified_test]
                if amplification["ampCategory"] == "ASSERT"]
            for amplification in amplification_log[amplified_test]:
                if amplification not in new_asserts:
                    print(describe_amplification(amplification))
            if new_asserts:
                print(describe_asserts(new_asserts))

            print("\tKilled mutants")
            for mutant in mutation_score["testCases"][i]["mutantsKilled"]:
                print(describe_mutant(mutant))
        i += 1


if __name__ == '__main__':
    main()
