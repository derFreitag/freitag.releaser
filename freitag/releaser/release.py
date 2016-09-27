# -*- coding: utf-8 -*-
from freitag.releaser.changelog import UpdateDistChangelog
from freitag.releaser.utils import filter_git_history
from freitag.releaser.utils import get_compact_git_history
from freitag.releaser.utils import get_latest_tag
from freitag.releaser.utils import git_repo
from freitag.releaser.utils import is_branch_synced
from freitag.releaser.utils import push_cfg_files
from freitag.releaser.utils import update_branch
from freitag.releaser.utils import wrap_folder
from freitag.releaser.utils import wrap_sys_argv
from git import InvalidGitRepositoryError
from git import Repo
from plone.releaser.buildout import Buildout
from zest.releaser import fullrelease
from zest.releaser.utils import ask

import logging
import os
import re
import sys


logger = logging.getLogger(__name__)

DISTRIBUTION = '\033[1;91m{0}\033[0m'
BRANCH = PATH = '\033[1;30m{0}\033[0m'


class FullRelease(object):
    """Releases all distributions that have changes and want to be released

    Does lots of QA before and after any release actually happens as well as
    another bunch of boring tasks worth automating.
    """

    #: system path where to look for distributions to be released
    path = 'src'

    #: if actual releases have to happen or only gathering an overview of
    #: what's pending to be released
    test = None

    #: if network will be used (only to be used together with test)
    offline = None

    #: only release the distributions that their name match with this string
    filters = None

    #: distributions that will be released
    distributions = []

    #: plone.releaser.buildout.Buildout instance to get distribution's info
    #: and save new versions
    buildout = None

    #: changelog for each released distribution
    changelogs = {}

    #: version for each released distribution
    versions = {}

    #: last tag for each released distribution (before the new release)
    last_tags = {}

    #: global commit message for zope and deployment repositories which lists
    #: all distributions released and their changelog
    commit_message = ''

    def __init__(
        self,
        path='src',
        test=False,
        filter_distributions='',
        offline=False,
        branch='master',
    ):
        self.path = path
        self.test = test
        self.offline = offline
        self.filters = filter_distributions
        self.branch = branch
        self.buildout = Buildout(
            sources_file='sources.cfg',
            checkouts_file='buildout.cfg',
        )

        if self.offline and not self.test:
            logger.warn(
                'Offline operations means that no release can be done. '
                'Test option has been turned on as well.'
            )
            self.test = True

    def __call__(self):
        """Go through all distributions and release them if needed *and* wanted
        """
        self.get_all_distributions()
        self.filter_distros()
        if not self.offline:
            self.check_pending_local_changes()
        self.check_changes_to_be_released()
        self.ask_what_to_release()

        if not self.test and len(self.distributions) > 0:
            self.release_all()
            self._create_commit_message()
            self.update_buildout()
            # push cfg files so that jenkins gets them already
            push_cfg_files()
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

        logger.debug('Distributions: ')
        logger.debug('\n'.join(self.distributions))

    def filter_distros(self):
        if not self.filters:
            return

        tmp_list = []
        for f in self.filters:
            tmp_list += [
                d
                for d in self.distributions
                if d.find(f) != -1
            ]
        # keep them sorted
        self.distributions = sorted(tmp_list)

    def check_pending_local_changes(self):
        """Check that the distributions do not have local changes"""
        logger.info('')
        msg = 'Check pending local changes'
        logger.info(msg)
        logger.info('-' * len(msg))
        clean_distributions = []
        for distribution_path in self.distributions:
            # nice to have: add some sort of progress bar like plone.releaser
            repo = Repo(distribution_path)

            dirty = False
            local_changes = False

            if repo.is_dirty():
                dirty = True

            if not is_branch_synced(repo, branch=self.branch):
                local_changes = True

            if dirty or local_changes:
                msg = '{0} has non-committed/unpushed changes, ' \
                      'it will not be released.'
                msg = msg.format(DISTRIBUTION.format(distribution_path))
                logger.info(msg)
                continue

            clean_distributions.append(distribution_path)

        # if nothing is about to be released, do not filter the distributions
        if not self.test:
            if len(self.distributions) != len(clean_distributions):
                if not ask('Do you want to continue?', default=True):
                    sys.exit()

            self.distributions = clean_distributions

        logger.debug('Distributions: ')
        logger.debug('\n'.join(self.distributions))

    def check_changes_to_be_released(self):
        """Check which distributions have changes that could need a release"""
        logger.info('')
        msg = 'Check changes to be released'
        logger.info(msg)
        logger.info('-' * len(msg))
        need_a_release = []
        for distribution_path in self.distributions:
            dist_name = distribution_path.split('/')[-1]
            logger.debug(DISTRIBUTION.format(distribution_path))
            repo = Repo(distribution_path)
            remote = repo.remote()

            latest_tag = get_latest_tag(repo, self.branch)
            if latest_tag not in repo.tags:
                # if there is no tag it definitely needs a release
                need_a_release.append(distribution_path)
                self.last_tags[dist_name] = latest_tag
                continue

            self.last_tags[dist_name] = latest_tag
            # get the commit where the latest tag is on
            tag = repo.tags[latest_tag]
            tag_sha = tag.commit.hexsha

            branch_sha = remote.refs[self.branch].commit.hexsha
            if tag_sha != branch_sha:
                # self.branch is ahead of the last tag: needs a release
                need_a_release.append(distribution_path)

        # if nothing is about to be released, do not filter the distributions
        if not self.test:
            self.distributions = need_a_release

    def ask_what_to_release(self):
        """Show changes both in CHANGES.rst and on git history

        For that checkout the repository, show both changes to see if
        everything worth writing in CHANGES.rst from git history is already
        there.
        """
        logger.info('')
        msg = 'What to release'
        logger.info(msg)
        logger.info('-' * len(msg))
        to_release = []
        for distribution_path in self.distributions:
            dist_name = distribution_path.split('/')[-1]
            repo = Repo(distribution_path)

            git_changes = get_compact_git_history(
                repo,
                self.last_tags[dist_name],
                self.branch,
            )
            cleaned_git_changes = filter_git_history(git_changes)

            # a git history without any meaningful commit should not be
            # released
            if cleaned_git_changes == '':
                continue

            logger.info(DISTRIBUTION.format(distribution_path))

            change_log_path = '{0}/CHANGES.rst'.format(
                repo.working_tree_dir
            )
            try:
                changes = self._grab_changelog(change_log_path)
            except IOError:
                logger.debug('Changelog not found, skipping.')
                continue
            self.changelogs[dist_name] = changes[2:]

            # nice to have: show them side-by-side
            logger.info('')
            logger.info(cleaned_git_changes)
            logger.info('')
            logger.info('')
            logger.info(''.join(changes))
            msg = '{0}: write the above git history on CHANGES.rst?'
            if self.test and ask(msg.format(dist_name)):
                changelog = UpdateDistChangelog(
                    distribution_path,
                    branch=self.branch,
                )
                changelog.write_changes(history=cleaned_git_changes)
            elif not self.test and \
                    ask('Is the change log ready for release?'):
                to_release.append(distribution_path)

        if not self.test:
            self.distributions = to_release

        logger.debug('Distributions: ')
        logger.debug('\n'.join(self.distributions))

    def release_all(self):
        """Release all distributions"""
        logger.info('')
        msg = 'Release!'
        logger.info(msg)
        logger.info('-' * len(msg))
        for distribution_path in self.distributions:
            logger.info(DISTRIBUTION.format(distribution_path))
            dist_name = distribution_path.split('/')[-1]
            repo = Repo(distribution_path)

            release = ReleaseDistribution(repo.working_tree_dir)
            new_version = release()
            self.versions[dist_name] = new_version

            self.buildout.set_version(dist_name, new_version)

            # update the local repository
            update_branch(repo, self.branch)

    def _create_commit_message(self):
        msg = ['New releases:', '', ]
        changelogs = ['', 'Changelogs:', '', ]
        for dist in sorted(self.versions.keys()):
            tmp_msg = '{0} {1}'.format(
                dist,
                self.versions[dist]
            )
            msg.append(tmp_msg)

            changelogs.append(dist)
            changelogs.append('-' * len(dist))
            changelogs.append(''.join(self.changelogs[dist]))
            changelogs.append('')

        # There's no need to run CI when doing releases...
        ci_skip = ['[ci-skip]', ]

        self.commit_message = '\n'.join(msg + changelogs + ci_skip)

    def update_buildout(self):
        """Commit the changes on buildout"""
        msg = 'Update buildout'
        logger.info(msg)
        logger.info('-' * len(msg))

        repo = Repo(os.path.curdir)
        repo.git.add('versions.cfg')
        repo.git.commit(message=self.commit_message)
        # push the changes
        repo.remote().push()

    def update_batou(self):
        """Update the version pins on batou as well"""
        deployment_repo = self.buildout.sources.get('deployment')
        if deployment_repo is None:
            logger.info(
                'No deployment repository sources found!'
                '\n'
                'Batou can not be updated!'
            )
            return
        # clone the repo
        with git_repo(deployment_repo, shallow=False) as repo:
            # get components/plone/versions/versions.cfg Buildout
            path = 'components/plone/versions/versions.cfg'
            plone_versions = '{0}/{1}'.format(
                repo.working_tree_dir,
                path
            )
            deployment_buildout = Buildout(
                sources_file=plone_versions,
                checkouts_file=plone_versions,
                versions_file=plone_versions
            )
            # update version pins
            for dist_name in self.versions:
                deployment_buildout.set_version(
                    dist_name,
                    self.versions[dist_name]
                )
            # commit and push the repo
            repo.index.add([path, ])
            repo.index.commit(message=self.commit_message.encode('utf-8'))
            # push the changes
            repo.remote().push()

    @staticmethod
    def _grab_changelog(changelog_path):
        unreleased_regex = re.compile(r' \(unreleased\)$')
        release = re.compile(r' \(\d+-\d+-\d+\)$')
        lines = []
        with open(changelog_path) as changelog:
            on_changelog = False
            for line in changelog:
                if unreleased_regex.search(line):
                    on_changelog = True

                if release.search(line):
                    break

                if on_changelog:
                    lines.append(line)
        return lines


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

    def __init__(self, path):
        self.path = path
        self.name = path.split('/')[-1]

    def __call__(self):
        self._check_parent_branch()
        self._check_distribution_exists()
        self._zest_releaser()

        return self.get_version()

    def _check_parent_branch(self):
        self.parent_repo = Repo(os.path.curdir)
        current_branch = self.parent_repo.active_branch.name

        if current_branch not in ('master', '4.x'):
            text = '{0} is not on master or 4.x branch, but on {1}'
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
        with wrap_folder(self.path):
            with wrap_sys_argv():
                fullrelease.main()

    def get_version(self):
        self.repo = Repo(self.path)
        return self.repo.git.describe('--tags').split('-')[0]
