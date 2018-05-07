#!/bin/env python3

""" PR_MESSAGE_GEN
Utils to generate url link for files.
"""
import git


def create_url_file_line(project_root, file_relative_path, line_number):
    """
    Creates a browser link for a line.
    """
    url = ''
    repo = git.Repo(project_root)
    url += next(repo.remote().urls).rstrip('/')
    url += '/blob/' + repo.head.commit.hexsha
    url += '/' + file_relative_path
    url += '#L' + str(line_number)
    return url.replace('/./', '/')


if __name__ == '__main__':
    print(create_url_file_line('..', "pr_message_gen/main.py", 11))
