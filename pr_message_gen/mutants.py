#!/bin/env python3

""" PR_MESSAGE_GEN
Functions related to mutants.
"""
import os
from collections import Counter


import git_link
import utils


def __PIT_descriptions(mutants: list) -> str:
    res = ''
    for i in range(len(mutants)):
        res += str(i+1) + '. ' + mutants[i]['description'] + '\n'
    list_title = 'Mutant' + ('s' if len(mutants) > 1 else '') + ' description'
    return utils.fold_block(list_title, res)


def describe_mutants(mutants, project_root_path, module_path, src_path):
    """
    Natural language description of a set of mutants.
    """
    res = ''
    mutants_line = [
        (mutant["lineNumber"],
         mutant['locationClass'],
         mutant["locationMethod"]) for mutant in mutants]
    count_lines = Counter(mutants_line)
    for mutant in count_lines:
        line_number, class_mutated, method_mutated = mutant
        nb_mutants = count_lines[mutant]
        class_path = class_mutated.replace('.', '/') + '.java'
        link = git_link.create_url_file_line(
            project_root_path, os.path.join(
                module_path, src_path, class_path), line_number)
        res += "#### The new test can detect " + str(nb_mutants) + \
            " change" + ('s' if nb_mutants > 1 else '') + " in `" + \
            class_mutated.split('.')[-1] + '#' + method_mutated + \
            "`, line " + str(line_number) + ".\n" + link + "\n"
        res += __PIT_descriptions(
            [full_mutant for full_mutant in mutants
             if (full_mutant['lineNumber'] == mutant[0] and
                 full_mutant['locationClass'] == mutant[1] and
                 full_mutant['locationMethod'] == mutant[2])])
        res += '\n'
    return res[:-1]
