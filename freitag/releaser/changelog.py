# -*- coding: utf-8 -*-
from freitag.releaser.utils import filter_git_history
from freitag.releaser.utils import get_compact_git_history
from git import Repo
from git.exc import GitCommandError

import os
import sys


class VersionException(Exception):
    """Raised when a version is not in the expected or value range."""
    pass


class GatherChangelog(object):

    newest_version = 0
    earliest_version = 0

    def __call__(self):
        # ask which changelog entries are wanted (between which versions)
        self.ask_versions()

        msg = '\nGATHERING CHANGELOG FROM {0} to {1}'
        print(msg.format(self.earliest_version, self.newest_version))

        changelog = self.gather_changelog(
            self.newest_version,
            self.earliest_version
        )
        print(changelog)

    def ask_versions(self):
        last_version = self._get_buildout_version()

        # newest release
        question = 'Newest version from where to gather changelog ({0})? '
        self.newest_version = self.ask_question(
            question.format(last_version),
            last_version,
            default=True
        )

        # oldest release
        previous_release = last_version - 1
        question = 'Oldest version to gather changelog from ({0})? '
        self.earliest_version = self.ask_question(
            question.format(previous_release),
            previous_release,
            default=True
        )

        if self.newest_version <= self.earliest_version:
            msg = 'newest release {0} must be bigger than oldest release {1}!'
            raise VersionException(
                msg.format(
                    self.newest_version,
                    self.earliest_version
                )
            )

    @staticmethod
    def _get_buildout_version():
        version_file = open('VERSION')
        line = version_file.read()
        version_file.close()
        # minus one as VERSION file always points to the next release
        return int(line.strip()) - 1

    def ask_question(self, question, last_version, default=False):
        answer = False
        while not answer:
            try:
                answer = self.ask(question, last_version, default=default)
            except VersionException:
                print('Please provide a valid value for version.')
        return answer

    @staticmethod
    def ask(question, last_version, default=False):
        """Interactively ask a question, sanitize the input and return it.

        :param question: Question to be asked to the user.
        :type question: string
        :param last_version: Last buildout release version.
        :type last_version: int
        :param default: If no answer is provided the `last_version` is used.
        :type default: bool
        :returns: Sanitized answer provided by user interactively.
        :rtype: int
        :raises:
            :class:`VersionException`
        """
        response = raw_input(question)

        # if there's a default answer and no input is provided return
        # last_version.
        if default and response == '':
            return last_version

        # check if the returned value can be casted as a number.
        try:
            response = int(response)
        except ValueError:
            raise VersionException('Version must be a number')

        if response > last_version:
            raise VersionException('This version still does not exist!')
        if response < 1:
            raise VersionException(
                'This version does not exist, first version was 1'
            )

        return response

    @staticmethod
    def gather_changelog(newest, oldest):
        repo = Repo(os.path.curdir)

        new_releases = '\n\n'
        other_commits = '\n\n'
        begin = 'New version: {0}'.format(newest)
        end = 'New version: {0}'.format(oldest)
        at_begin = False

        for commit in repo.iter_commits():
            msg = commit.message
            if msg.startswith(end):
                break
            if msg.startswith(begin):
                at_begin = True
            if at_begin:
                if msg.startswith('New releases of:'):
                    new_releases = new_releases + msg + '\n'
                elif not msg.startswith('New version:'):
                    other_commits = other_commits + msg + '\n'

        return new_releases + other_commits


class UpdateDistChangelog(object):
    """Update CHANGES.rst on the given distribution"""

    #: system path where the distribution should be found
    path = None

    def __init__(self, path):
        self.path = path

    def __call__(self):
        if not os.path.exists(self.path):
            print('{0} does not exist'.format(self.path))
            sys.exit(1)

        path = '{0}/CHANGES.rst'.format(self.path)
        if not os.path.exists(path):
            print('{0} does not exist'.format(path))
            sys.exit(1)

        repo = Repo(self.path)
        remote = repo.remote()
        latest_master_commit = remote.refs['master'].commit.hexsha
        try:
            latest_tag = repo.git.describe(
                '--abbrev=0',
                '--tags',
                latest_master_commit
            )
        except GitCommandError:
            # get the second to last commit
            # for the way get_compact_git_history gets the commit before the
            # earliest you pass
            commits = [
                c
                for c in repo.iter_commits()
            ]
            latest_tag = commits[-2].hexsha

        history = get_compact_git_history(repo, latest_tag)
        cleaned_git_changes = filter_git_history(history)
        print(cleaned_git_changes)

        with open(path) as changes:
            current_data = changes.read()

        with open(path, 'w') as changes:
            changes.write(history)
            changes.write('\n')
            changes.write('\n')
            changes.write(current_data)
