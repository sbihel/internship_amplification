#!/bin/env python3

""" PR_MESSAGE_GEN
"""
import argparse
import json
import os
from collections import Counter

import git_link


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
    else:
        raise ValueError("Unknown category.")


def describe_asserts(new_asserts):
    """
    Natural language description of a set of assertions.
    """
    new_asserts_shortname = [assertion["newValue"].split(
        '=')[-1] for assertion in new_asserts]
    count_asserts = Counter(new_asserts_shortname)
    res = ""
    for shortname in count_asserts:
        res += str(count_asserts[shortname]) + \
            " assertions for the return value of `" + shortname + "`\n"
    return res[:-1]


def describe_mutant(mutant, project_root_path, module_path, src_path):
    """
    Natural language description of a mutant.
    """
    file_class = mutant['locationClass']
    line_number = mutant['lineNumber']
    class_path = file_class.replace('.', '/') + '.java'
    link = git_link.create_url_file_line(
        project_root_path, os.path.join(
            module_path, src_path, class_path), line_number)
    return "Bug introduced in `" + file_class.split('.')[-1] + '#' + \
        mutant["locationMethod"] + "` at [line " + str(line_number) + \
        "](" + link + "), using " + mutant["ID"].split('.')[-1]


def describe_test_class(test_class_report_path,
                        project_root_path, module_path, src_path, test_path):
    """
    Natural language description of an amplified test class.
    """
    if not os.path.exists(test_class_report_path + '_mutants_killed.json'):
        return
    print(
        "========== Class: " + test_class_report_path.split('.')[-1] +
        " ==========")
    with open(test_class_report_path+'_mutants_killed.json', 'r') as json_file:
        mutation_score = json.load(json_file)
    with open(test_class_report_path+'_amp_log.json', 'r') as json_file:
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
            print('===== Generated test: `' + amplified_test + '` from `' +
                  mutation_score["testCases"][i]["parentName"] + '` =====')
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
                print(
                    describe_mutant(
                        mutant,
                        project_root_path,
                        module_path,
                        src_path))
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

    dir_prop = os.path.join(*(opts.properties_file.split(os.sep)[:-1]))
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

    if opts.test:
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
        for file in os.listdir(report_dir):
            if file.endswith('_mutants_killed.json'):
                describe_test_class(
                    report_dir + os.sep + file[: -len('_mutants_killed.json')],
                    project_root_path, module_path, src_path, test_path)


if __name__ == '__main__':
    main()
