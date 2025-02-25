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
from zest.releaser import bumpversion
from zest.releaser import fullrelease
from zest.releaser.utils import ask

import logging
import os
import re
import sys
import time


logger = logging.getLogger(__name__)

DISTRIBUTION = '\033[1;91m{0}\033[0m'
BRANCH = PATH = '\033[1;30m{0}\033[0m'

NEWS_ENTRY_FILENAME_RE = re.compile(r'(\+?[\-\d\w]+).(\w+)(.\d)*')


class FullRelease:
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
        branch='main',
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
            logger.warning(
                'Offline operations means that no release can be done. '
                'Test option has been turned on as well.'
            )
            self.test = True

    def __call__(self):
        """Go through all distributions and release them if needed *and* wanted"""
        self.get_all_distributions()
        self.filter_distros()
        if not self.offline:
            self.check_tooling()
            self.check_parent_repo_changes()
            self.check_pending_local_changes()
        self.check_changes_to_be_released()
        self.ask_what_to_release()

        if not self.test and len(self.distributions) > 0:
            self.check_branches()
            self.report_whats_to_release()
            self.release_all()
            self._create_commit_message()
            self.update_buildout()
            self.update_batou()
            self.push_cfg_files()

    def get_all_distributions(self):
        """Get all distributions that are found in self.path"""
        for folder in sorted(os.listdir(self.path)):
            path = f'{self.path}/{folder}'
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
            tmp_list += [d for d in self.distributions if d.find(f) != -1]
        # keep them sorted
        self.distributions = sorted(tmp_list)

    def check_tooling(self):
        """Ensure that the tools needed are available

        Tools to check:
        - towncrier: without it the news/ folder would not be used
        """
        logger.info('')
        msg = 'Check tools'
        logger.info(msg)
        logger.info('-' * len(msg))

        # that's how zestreleaser.towncrier searches for towncrier
        import distutils

        path = distutils.spawn.find_executable('towncrier')
        if not path:
            raise ValueError(
                'towncrier is not available, '
                'activate the virtualenv and/or '
                'install what is on requirements.txt'
            )

    def check_parent_repo_changes(self):
        """Check that the parent repository does not have local or upstream
        changes
        """
        logger.info('')
        msg = 'Check parent repository'
        logger.info(msg)
        logger.info('-' * len(msg))

        repo = Repo(os.path.curdir)

        dirty = False
        local_changes = False

        if repo.is_dirty():
            dirty = True

        if not is_branch_synced(repo, branch=self.branch):
            local_changes = True

        if dirty or local_changes:
            msg = (
                'zope has non-committed/unpushed changes, '
                'no releases can be made on that state.'
            )
            raise ValueError(msg)

    def check_pending_local_changes(self):
        """Check that the distributions do not have local changes"""
        logger.info('')
        msg = 'Check pending local changes'
        logger.info(msg)
        logger.info('-' * len(msg))
        clean_distributions = []
        for index, distribution_path in enumerate(self.distributions, start=1):
            # nice to have: add some sort of progress bar like plone.releaser
            logger.info(
                '[%i/%i] Checking %s',
                index,
                len(self.distributions),
                distribution_path,
            )
            repo = Repo(distribution_path)

            dirty = False
            local_changes = False

            if repo.is_dirty():
                dirty = True

            if not is_branch_synced(repo, branch=self.branch):
                local_changes = True

            if dirty or local_changes:
                distro = DISTRIBUTION.format(distribution_path)
                logger.info(
                    f'{distro} has non-committed/unpushed changes, '
                    'it will not be released.'
                )
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

            news_folder = f'{repo.working_tree_dir}/news'
            try:
                changes, next_release = self._grab_changelog(news_folder)
            except OSError:
                logger.debug('Changelog not found, skipping.')
                continue
            self.changelogs[dist_name] = changes

            # nice to have: show them side-by-side
            logger.info('git changelog')
            logger.info('')
            logger.info(cleaned_git_changes)
            logger.info('')
            logger.info('')
            logger.info('news entries')
            logger.info('')
            logger.info(''.join(changes))
            release_kind = DISTRIBUTION.format(next_release)
            logger.info(f'Next release will be a {release_kind} release\n')
            if next_release != 'bugfix':
                logger.info(
                    'You can still change the version number, see the next question.'
                )
            msg = f'Is the change log for {dist_name} ready for release?'
            if not self.test and ask(msg):
                to_release.append(distribution_path)

                if next_release != 'bugfix':
                    self._decide_version(distribution_path, next_release)

        if not self.test:
            self.distributions = to_release

        logger.debug('Distributions: ')
        logger.debug('\n'.join(self.distributions))

    @staticmethod
    def _decide_version(distribution_path, next_release):
        with wrap_folder(distribution_path):
            with wrap_sys_argv():
                sys.argv = ['bin/bumpversion', f'--{next_release}']
                bumpversion.main()

    def check_branches(self):
        """Check that all distributions to be released, and the parent
        repository, are on the correct branch
        """
        logger.info('')
        msg = 'Check branches'
        logger.info(msg)
        logger.info('-' * len(msg))

        parent_repo = Repo(os.path.curdir)
        current_branch = parent_repo.active_branch.name

        if current_branch != self.branch:
            distro = DISTRIBUTION.format('zope repository')
            expected_branch = BRANCH.format(self.branch)
            actual_branch = BRANCH.format(current_branch)
            raise ValueError(
                f'{distro} is not on {expected_branch} branch, but on {actual_branch}'
            )

        for distribution_path in self.distributions:
            dist_name = distribution_path.split('/')[-1]
            repo = Repo(distribution_path)
            current_branch = repo.active_branch.name

            if current_branch != self.branch:
                distro = DISTRIBUTION.format(f'{dist_name} repository')
                expected_branch = BRANCH.format(self.branch)
                actual_branch = BRANCH.format(current_branch)
                raise ValueError(
                    f'{distro} is not on {expected_branch} branch, but on {actual_branch}'
                )

    def report_whats_to_release(self):
        """Report which distributions are about to be released"""
        logger.info('')
        msg = 'Distributions about to release:'
        logger.info(msg)
        logger.info('-' * len(msg))
        for distribution_path in self.distributions:
            dist_name = distribution_path.split('/')[-1]
            logger.info(f'- {dist_name}')

    def release_all(self):
        """Release all distributions"""
        logger.info('')
        msg = 'Release!'
        logger.info(msg)
        logger.info('-' * len(msg))
        logger.info('Give yourself 5 seconds to decide if all is fine')
        time.sleep(5)
        for distribution_path in self.distributions:
            logger.info(f'\n\n{DISTRIBUTION.format(distribution_path)}')
            dist_name = distribution_path.split('/')[-1]
            repo = Repo(distribution_path)

            release = ReleaseDistribution(repo.working_tree_dir, self.branch)
            new_version = release()
            self.versions[dist_name] = new_version

            self.buildout.set_version(dist_name, new_version)

            # update the local repository
            update_branch(repo, self.branch)

    def _create_commit_message(self):
        msg = ['New releases:', '']
        changelogs = ['', 'Changelogs:', '']
        for dist in sorted(self.versions.keys()):
            tmp_msg = f'{dist} {self.versions[dist]}'
            msg.append(tmp_msg)

            changelogs.append(dist)
            changelogs.append('-' * len(dist))
            changelogs.append(''.join(self.changelogs[dist]))
            changelogs.append('')

        self.commit_message = '\n'.join(msg + changelogs)

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

    def push_cfg_files(self):
        """Push cfg files so that jenkins gets them already"""
        try:
            push_cfg_files()
        except OSError:
            logger.error('Could not connect to the server!!!')

    def update_batou(self):
        """Update the version pins on batou as well"""
        msg = 'Update batou'
        logger.info(msg)
        logger.info('-' * len(msg))

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
            plone_versions = f'{repo.working_tree_dir}/{path}'
            deployment_buildout = Buildout(
                sources_file=plone_versions,
                checkouts_file=plone_versions,
                versions_file=plone_versions,
            )
            # update version pins
            for dist_name in self.versions:
                deployment_buildout.set_version(dist_name, self.versions[dist_name])
            # commit and push the repo
            repo.index.add([path])
            repo.index.commit(message=self.commit_message)
            # push the changes
            repo.remote().push()

    def _grab_changelog(self, news_folder):
        entries, next_release = self.verify_newsentries(news_folder)
        header = '\n- {1} https://gitlab.com/der-freitag/zope/issues/{0}\n'
        lines = []
        for suffix, issue, news_filename in entries:
            news_path = os.sep.join([news_folder, news_filename])
            lines.append(header.format(issue, suffix))
            with open(news_path) as news_file:
                for line in news_file:
                    lines.append(f'  {line}')

        return lines, next_release

    def verify_newsentries(self, news_folder):
        valid_entries = []
        valid_suffixes = ('bugfix', 'feature', 'breaking', 'internal')
        highest_suffix_used = 'bugfix'
        try:
            for news_filename in os.listdir(news_folder):
                if news_filename in ('.gitkeep', '.changelog_template.jinja'):
                    continue
                news_path = os.sep.join([news_folder, news_filename])
                matches = NEWS_ENTRY_FILENAME_RE.match(news_filename)
                if matches:
                    issue, suffix, _ = matches.groups()
                    if suffix not in valid_suffixes:
                        raise ValueError(
                            f'{matches.groups(1)} on "{news_path}" is not valid. '
                            f'Valid suffixes are: {valid_suffixes}'
                        )
                    valid_entries.append([suffix, issue, news_filename])
                    highest_suffix_used = self.highest_suffix(
                        highest_suffix_used, suffix
                    )
                    logger.debug(f'Found a valid news entry: {news_path}')
                else:
                    logger.debug(f'!!! Invalid news entry: {news_path}')
        except OSError:
            logger.warning(f'{news_folder} does not exist')
        return valid_entries, highest_suffix_used

    @staticmethod
    def highest_suffix(current, new):
        suffixes_ordered = ('breaking', 'feature', 'bugfix')
        for suffix in suffixes_ordered:
            if current == suffix or new == suffix:
                return suffix


class ReleaseDistribution:
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

    def __init__(self, path, branch='main'):
        self.path = path
        self.branch = branch
        self.name = path.split('/')[-1]

    def __call__(self):
        self._check_distribution_exists()
        self._zest_releaser()

        return self.get_version()

    def _check_distribution_exists(self):
        """Check that the folder exists"""
        if not os.path.exists(self.path):
            raise OSError(f'Path {PATH.format(self.path)} does NOT exist')

    def _zest_releaser(self):
        """Release the distribution"""
        # remove arguments so zest.releaser is not confused
        # will most probably *not* be fixed by zest.releaser itself:
        # https://github.com/zestsoftware/zest.releaser/issues/146
        with wrap_folder(self.path):
            with wrap_sys_argv():
                sys.argv = ['bin/fullrelease', '--no-input']
                fullrelease.main()

    def get_version(self):
        self.repo = Repo(self.path)
        return self.repo.git.describe('--tags').split('-')[0]
