#!/bin/env python3

""" PR_MESSAGE_GEN
"""
import argparse
import json
import os

from asserts import describe_asserts
from mutants import describe_mutants
from i_amplification import describe_amplification


PROJECT_ROOT_PATH = ''
MODULE_PATH = ''
SRC_PATH = ''
TEST_PATH = ''


def describe_test_case(amplified_test, mutation_score, amplification_log):
    """
    Natural language description of an amplified test case.
    """
    res = ""
    # HEADER
    parent_name = mutation_score["parentName"]
    if amplified_test != parent_name:
        res += '## Generated test `' + amplified_test + \
            '` based on `' + parent_name + '`\n'
    else:
        res += '## Original test `' + amplified_test + '`\n'
    new_asserts = [amplification
                   for amplification in amplification_log
                   if amplification["ampCategory"] == "ASSERT"]

    # ASSERTS
    assert_res, useless_assigns = '', []
    if new_asserts:
        message, useless_assigns = describe_asserts(new_asserts)
        assert_res += message + '\n'

    # INPUTS
    input_res = ''
    for amplification in amplification_log:
        if amplification not in new_asserts:
            input_res += describe_amplification(amplification) + '\n'
    for amplification in useless_assigns:
        amplification["ampCategory"] = "ADD"
        input_res += describe_amplification(amplification) + '\n'
    if input_res:
        nb_inputs = mutation_score["nbInputAdded"] + len(useless_assigns)
        res += '### Generated ' + str(nb_inputs) + ' input' + \
            ('s' if nb_inputs > 1 else '') + '.\n'
        res += input_res + '\n'

    # show the asserts after the inputs
    if assert_res and assert_res != '\n':
        nb_asserts = mutation_score["nbAssertionAdded"] - len(useless_assigns)
        res += '### Generated ' + str(nb_asserts) + ' assertion' + \
            ('s' if nb_asserts > 1 else '') + '.\n'
        res += assert_res + '\n'

    # MUTANTS
    mutants = mutation_score["mutantsKilled"]
    res += "### " + str(len(mutants)) + " new behavior" + \
        ("s" if len(mutants) > 1 else "") + " covered.\n"
    res += describe_mutants(mutants, PROJECT_ROOT_PATH,
                            MODULE_PATH, SRC_PATH) + '\n'
    return res


def describe_test_class(test_class_report_path):
    """
    Natural language description of an amplified test class.
    """
    if not os.path.exists(test_class_report_path + '_mutants_killed.json'):
        return ''
    res = "# Class: " + test_class_report_path.split('.')[-1] + "\n"
    with open(test_class_report_path+'_mutants_killed.json', 'r') as json_file:
        mutation_score = json.load(json_file)
    with open(test_class_report_path+'_amp_log.json', 'r') as json_file:
        amplification_log = json.load(json_file)

    amplified_tests = [test_case["name"]
                       for test_case in mutation_score["testCases"]]
    i = 0
    for amplified_test in list(amplification_log):
        if amplified_test not in amplified_tests:
            amplification_log.pop(amplified_test, None)
        else:
            if i:
                res += '\n\n'
            res += describe_test_case(amplified_test,
                                      mutation_score["testCases"][i],
                                      amplification_log[amplified_test])
            i += 1
    return res[:-2]


def describe_test_classes(report_dir):
    """
    Natural language description of a set of amplified test classes.
    """
    i = 0
    output_dir = os.listdir(report_dir)
    for filename in output_dir:
        if (filename.endswith('_mutants_killed.json')
                and (filename[: -len('mutants_killed.json')] +
                     'amp_log.json') in output_dir):
            test_class_description = describe_test_class(
                report_dir + os.sep + filename[: -len('_mutants_killed.json')])
            if test_class_description.count('\n') > 1:
                if i:
                    print()
                print(test_class_description)
                i += 1


def main():
    """
    Function to run pr_message_gen.
    """
    command_parser = argparse.ArgumentParser()
    command_parser.add_argument('-p', '--properties_file', type=str,
                                help='dspot.properties file.')
    command_parser.add_argument(
        '-t', '--test', type=str,
        help='Name of a particular test class.'
             'E.g. fr.inria.diversify.dspot.DSpotTest')

    opts, _ = command_parser.parse_known_args()

    if not opts.properties_file:
        raise ValueError("Need properties file")

    # Parse the properties file
    dir_prop = os.path.join(*(opts.properties_file.split(os.sep)[:-1]))
    if opts.properties_file[0] == os.sep:
        dir_prop = os.path.join(os.sep, dir_prop)
    project_root = None
    global MODULE_PATH
    MODULE_PATH = None
    global SRC_PATH
    SRC_PATH = None
    global TEST_PATH
    TEST_PATH = None
    output_directory = None
    with open(opts.properties_file, 'r') as properties_file:
        for line in properties_file:
            line = line.strip()
            if line.startswith('project='):
                project_root = line[len("project="):]
            elif line.startswith('targetModule='):
                MODULE_PATH = line[len('targetModule='):]
            elif line.startswith('src='):
                SRC_PATH = line[len('src='):]
            elif line.startswith('testSrc='):
                TEST_PATH = line[len('testSrc='):]
            elif line.startswith('outputDirectory='):
                output_directory = line[len('outputDirectory='):]
    global PROJECT_ROOT_PATH
    PROJECT_ROOT_PATH = os.path.join(dir_prop, project_root)

    # Message generation
    if opts.test:  # describe only the provided test class
        test_class_report_path = os.path.join(dir_prop,
                                              project_root,
                                              MODULE_PATH,
                                              output_directory,
                                              opts.test)
        if not os.path.exists(test_class_report_path+"_mutants_killed.json"):
            raise ValueError("Test class report not found.")
        describe_test_class(test_class_report_path)
    else:  # describe every amplified test class
        report_dir = os.path.join(
            dir_prop,
            project_root,
            MODULE_PATH,
            output_directory)
        describe_test_classes(report_dir)


if __name__ == '__main__':
    main()
