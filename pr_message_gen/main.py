#!/bin/env python3

""" PR_MESSAGE_GEN
"""
import argparse
import json
import os

from asserts import describe_asserts
from mutants import describe_mutants
from i_amplification import describe_amplification


def describe_test_class(test_class_report_path,
                        project_root_path, module_path, src_path, test_path):
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
                res += '\n'
            parent_name = mutation_score["testCases"][i]["parentName"]
            if amplified_test != parent_name:
                res += '## Generated test `' + amplified_test + \
                    '` based on `' + parent_name + '`\n'
            else:
                res += '## Original test `' + amplified_test + '`\n'
            new_asserts = [
                amplification
                for amplification in amplification_log[amplified_test]
                if amplification["ampCategory"] == "ASSERT"]

            input_res = ''
            for amplification in amplification_log[amplified_test]:
                if amplification not in new_asserts:
                    input_res += describe_amplification(amplification) + '\n'
            if input_res:
                res += '### ' + \
                    str(mutation_score["testCases"][i]["nbInputAdded"]) + \
                    ' generated inputs.\n'
                res += input_res

            assert_res = ''
            if new_asserts:
                assert_res += describe_asserts(new_asserts) + '\n'
            if assert_res:
                res += '### ' + \
                    str(mutation_score["testCases"][i]["nbAssertionAdded"]) + \
                    ' generated assertions.\n'
                res += assert_res

            mutants = mutation_score["testCases"][i]["mutantsKilled"]
            res += "### " + str(len(mutants)) + " new behavior" + \
                ("s" if len(mutants) > 1 else "") + " covered.\n"
            res += describe_mutants(
                mutants,
                project_root_path,
                module_path,
                src_path) + '\n'
            i += 1
    return res[:-1]


def describe_test_classes(report_dir, project_root_path,
                          module_path, src_path, test_path):
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
                report_dir + os.sep + filename[: -len('_mutants_killed.json')],
                project_root_path, module_path, src_path, test_path)
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
    module_path = None
    src_path = None
    test_path = None
    output_directory = None
    with open(opts.properties_file, 'r') as properties_file:
        for line in properties_file:
            line = line.strip()
            if line.startswith('project='):
                project_root = line[len("project="):]
            elif line.startswith('targetModule='):
                module_path = line[len('targetModule='):]
            elif line.startswith('src='):
                src_path = line[len('src='):]
            elif line.startswith('testSrc='):
                test_path = line[len('testSrc='):]
            elif line.startswith('outputDirectory='):
                output_directory = line[len('outputDirectory='):]
    project_root_path = os.path.join(dir_prop, project_root)

    # Message generation
    if opts.test:  # describe only the provided test class
        test_class_report_path = os.path.join(dir_prop,
                                              project_root,
                                              module_path,
                                              output_directory,
                                              opts.test)
        if not os.path.exists(test_class_report_path+"_mutants_killed.json"):
            raise ValueError("Test class report not found.")
        describe_test_class(
            test_class_report_path,
            project_root_path,
            module_path,
            src_path,
            test_path)
    else:  # describe every amplified test class
        report_dir = os.path.join(
            dir_prop,
            project_root,
            module_path,
            output_directory)
        describe_test_classes(
            report_dir,
            project_root_path,
            module_path,
            src_path,
            test_path)


if __name__ == '__main__':
    main()
