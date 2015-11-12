# -*- coding: utf-8 -*-
from freitag.releaser.utils import is_everything_pushed
from git import InvalidGitRepositoryError
from git import Repo
from git.exc import GitCommandError
from plone.releaser.buildout import Buildout
from plone.releaser.package import git_repo
from zest.releaser import fullrelease
from zest.releaser.utils import ask

import os
import sys


DISTRIBUTION = '\033[1;91m{0}\033[0m'
BRANCH = PATH = '\033[1;30m{0}\033[0m'


class FullRelease(object):
    """Releases all distributions that have changes and want to be released

    Does lots of QA before and after any release actually happens as well as
    another bunch of boring tasks worth automating.
    """

    #: system path where to look for distributions to be released
    path = 'src'

    #: distributions that will be released
    distributions = []

    #: plone.releaser.buildout.Buildout instance to get distribution's info
    #: and save new versions
    buildout = None

    #: git branches that will be updated/checked, etc
    branches = (
        'master',
        'develop',
    )

    def __init__(self, path='src'):
        self.path = path
        self.buildout = Buildout(
            sources_file='develop.cfg',
            checkouts_file='develop.cfg',
        )

    def __call__(self):
        """Go through all distributions and release them if needed *and* wanted
        """
        self.get_all_distributions()
        self.check_pending_local_changes()
        self.check_changes_to_be_released()
        self.ask_what_to_release()
        self.release_all()
        self.gather_changelogs()
        self.update_buildout()
        self.update_batou()

    def get_all_distributions(self):
        """Get all distributions that are found in self.path"""
        for folder in sorted(os.listdir(self.path)):
            path = '{0}/{1}'.format(self.path, folder)
            if not os.path.isdir(path):
                continue

            try:
                Repo(path)
            except InvalidGitRepositoryError:
                continue

            self.distributions.append(path)

    def check_pending_local_changes(self):
        """Check that the distributions do not have local changes"""
        clean_distributions = []
        for distribution_path in self.distributions:
            repo = Repo(distribution_path)

            dirty = False
            local_changes = False

            if repo.is_dirty():
                dirty = True

            if is_everything_pushed(repo, branches=self.branches):
                local_changes = True

            if dirty or local_changes:
                print('{0} has non-committed/unpushed changes.')

                msg = 'Do you want to continue? {0} will NOT be released '
                if not ask(msg, default=True):
                    exit(0)

                continue

            clean_distributions.append(distribution_path)

        self.distributions = clean_distributions

    def check_changes_to_be_released(self):
        """Check which distributions have changes that could need a release"""
        need_a_release = []
        for distribution_path in self.distributions:
            dist_name = distribution_path.split('/')[-1]
            dist_clone = self.buildout.sources.get(dist_name)

            with git_repo(dist_clone) as repo:
                # get the latest tag
                try:
                    latest_tag = repo.git.describe('--abbrev=0', '--tags')
                except GitCommandError:
                    # if there is no tag it definitely needs a release
                    need_a_release.append(distribution_path)
                    continue

                tag = repo.tags[latest_tag]
                tag_sha = tag.commit.hexsha

                for branch in self.branches:
                    branch_sha = repo.refs[branch].commit.hexsha

                    if tag_sha != branch_sha:
                        # a branch is ahead of the last tag: needs a release
                        need_a_release.append(distribution_path)
                        break

        self.distributions = need_a_release

    def ask_what_to_release(self):
        pass

    def release_all(self):
        pass

    def gather_changelogs(self):
        pass

    def update_buildout(self):
        pass

    def update_batou(self):
        pass


class ReleaseDistribution(object):
    """Release a single distribution with zest.releaser

    It does some QA checks before/after the actual release happens.
    """

    #: system path where the distribution should be found
    path = None
    #: name of the distribution
    name = None
    #: git repository of the distribution
    repo = None

    #: parent repository which will be updated with the new release
    parent_repo = None
    #: plone.releaser.buildout.Buildout instance of the parent repository
    buildout = None

    def __init__(self, path):
        self.path = path
        self.name = path.split('/')[1]

    def __call__(self):
        self._check_parent_branch()
        self._check_distribution_exists()
        self._zest_releaser()

        self.buildout = Buildout(
            sources_file='develop.cfg',
            checkouts_file='develop.cfg',
        )
        self.buildout.set_version(self.name, self.get_version())

    def _check_parent_branch(self):
        self.parent_repo = Repo(os.path.curdir)
        current_branch = self.parent_repo.active_branch.name

        if current_branch != 'master':
            text = '{0} is not on master branch, but on {1}'
            raise ValueError(
                text.format(
                    DISTRIBUTION.format('zope repository'),
                    BRANCH.format(current_branch)
                )
            )

    def _check_distribution_exists(self):
        """Check that the folder exists"""
        if not os.path.exists(self.path):
            raise IOError(
                'Path {0} does NOT exist'.format(PATH.format(self.path))
            )

    def _zest_releaser(self):
        """Release the distribution"""
        # remove arguments so zest.releaser is not confused
        # will most probably *not* be fixed by zest.releaser itself:
        # https://github.com/zestsoftware/zest.releaser/issues/146
        original_args = sys.argv
        sys.argv = ['']

        # change to the distribution root folder
        original_path = os.getcwd()
        os.chdir(self.path)

        fullrelease.main()

        os.chdir(original_path)
        sys.argv = original_args

    def get_version(self):
        self.repo = Repo(self.path)
        return self.repo.tags[-1].name
