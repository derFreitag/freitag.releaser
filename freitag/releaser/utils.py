# -*- coding: utf-8 -*-
from contextlib import contextmanager
from freitag.releaser import IGNORE_COMMIT_MESSAGES
from git import Repo
from git.exc import GitCommandError
from paramiko import AutoAddPolicy
from paramiko import SSHClient
from scp import SCPClient
from shutil import rmtree
from tempfile import mkdtemp

import logging
import os
import sys


logger = logging.getLogger(__name__)


def configure_logging(debug):
    if debug:
        level = logging.DEBUG
    else:
        level = logging.INFO
    logging.basicConfig(
        level=level,
        format='%(message)s'
    )


def update_branch(repo, branch):
    """Update the given branch on the given repository

    :param  repo: git repository where the branch should exist
    :type repo: git.Repo
    :param branch: branch that will be updated
    :type branch: str
    :return: whether updating the branch was successful or not
    :rtype: bool
    """
    remote = repo.remote()
    remote.fetch()
    try:
        repo.heads[branch].checkout()
    except IndexError:
        logger.debug('branch {0} does not exist remotely'.format(branch))
        return False

    local_commit = repo.head.commit
    remote_commit = remote.refs[branch].commit
    if local_commit != remote_commit:
        repo.git.rebase('origin/{0}'.format(branch))

    return True


def is_branch_synced(repo, branch='master'):
    """Check if master branch on the given repository has local commits

    :param repo: the repository that will be used to check the branches
    :type repo: git.Repo
    :param branch: the branch that needs to be checked if it is synced
    :type branch: str
    :return: whether the given repo's master branch is in sync with upstream
    :rtype: bool
    """
    # get new code, if any
    remote = repo.remote()
    remote.fetch()

    try:
        local_branch = repo.refs[branch]
    except IndexError:
        logger.debug('{0} branch does not exist locally'.format(branch))
        # no problem then, all commits are pushed
        return True

    try:
        remote_branch = remote.refs[branch]
    except IndexError:
        logger.debug('{0} branch does not exist remotely'.format(branch))
        # it's pointless to check if a branch has local commits if it does
        # not exist remotely
        return False

    local_commit = local_branch.commit.hexsha
    remote_commit = remote_branch.commit.hexsha

    if local_commit != remote_commit:
        return False

    return True


def get_compact_git_history(repo, tag):
    """Gets all the commits between the tag and master

    :param repo: the repository that will be used to get the history
    :type repo: git.Repo
    :param tag: the tag that will be used as a base from where to get commits
    :type tag: str
    :return: whether the given repo's master branch is in sync with upstream
    :rtype: str
    """
    try:
        return repo.git.log(
            '--oneline',
            '--graph',
            '{0}~1..master'.format(tag)
        )
    except GitCommandError:
        return ''


def push_cfg_files():
    ssh = SSHClient()
    ssh.load_system_host_keys()
    ssh.set_missing_host_key_policy(AutoAddPolicy())

    user, server, path = check_connection()

    ssh.connect(server, username=user)

    with SCPClient(ssh.get_transport()) as scp:
        files = [
            'versions.cfg',
            'distribution-qa.cfg',
            'release.cfg',
            'sources.cfg',
            'qa.cfg',
            'solr.cfg',
        ]
        scp.put(files, remote_path=path)
        logger.debug('Files uploaded: ')
        logger.debug('\n'.join(files))


def filter_git_history(changes):
    """Removes administrative/boilerplate commits from the given git history.

    :param changes: the git changes that need to be filtered
    :type changes: str
    :return: the original git changes without any uninteresting commit message
    :rtype: str
    """
    cleaned_changes = []
    for line in changes.split('\n'):
        found = False
        for ignore_message in IGNORE_COMMIT_MESSAGES:
            if line.find(ignore_message) != -1:
                found = True
                break
        if not found:
            cleaned_changes.append(line)

    return '\n'.join(cleaned_changes)


def get_latest_tag(repo, branch):
    """Returns the tag closest to the given branch on the given repository.

    If no tag can be found,
    then the earliest possible commit is returned instead.

    :param repo: the repository where to look for the tag
    :type repo: git.Repo
    :param branch: the branch where to look for a tag
    :type branch: str
    :return: closest reachable tag from given branch,
      or the earliest commit possible
    :rtype: str
    :raises: IndexError if the given branch can not be found on the
      default git remote
    """
    remote = repo.remote()
    latest_master_commit = remote.refs[branch].commit.hexsha
    try:
        latest_tag = repo.git.describe(
            '--abbrev=0',
            '--tags',
            latest_master_commit
        )
    except GitCommandError:
        # get the second to last commit
        # for the way get_compact_git_history gets the commit before
        # the earliest you pass
        commits = [
            c
            for c in repo.iter_commits()
        ]
        latest_tag = commits[-2].hexsha

    return latest_tag


@contextmanager
def git_repo(source, shallow=True, depth=100):
    """Handle temporal git repositories.

    It ensures that a git repository is cloned on a temporal folder that is
    removed after being used.

    See an example of this kind of context managers here:
    http://preshing.com/20110920/the-python-with-statement-by-example/

    :param source: the configuration to clone the repository
    :type source: plone.releaser.buildout.Source
    :param shallow: if the clone needs to be trimmed or a complete clone
    :type shallow: bool
    :param depth: how many commits will be fetched
    :type depth: int
    :return: the cloned repository
    :rtype: git.Repo
    """
    tmp_dir = mkdtemp()
    url = source.url
    if source.push_url is not None:
        url = source.push_url

    if shallow:
        repo = Repo.clone_from(
            source.url,
            tmp_dir,
            depth=depth,
            no_single_branch=True,
        )
    else:
        repo = Repo.clone_from(
            url,
            tmp_dir
        )

    # give the control back
    yield repo

    # cleanup
    del repo
    rmtree(tmp_dir)


@contextmanager
def wrap_folder(new_folder):
    """Context manager to do some work on a folder and move back

    :param new_folder: path to the folder one wants to move to
    :type new_folder: str
    :return: nothing, gives the control back
    """
    current_directory = os.getcwd()
    os.chdir(new_folder)

    yield

    os.chdir(current_directory)


@contextmanager
def wrap_sys_argv():
    """Context manager to temporally save sys.argv and restore if afterwards"""
    original_args = sys.argv
    sys.argv = ['', ]

    yield

    sys.argv = original_args


def check_connection():
    """Check that a connection string exists

    This is a generic way to get a connection string without having to
    """
    user = None
    server = None
    path = None
    try:
        with open('release.cfg') as config:
            connection = config.read()
            if '@' not in connection:
                raise ValueError('No user/server on release.cfg')
            user, server = connection.strip().split('@')

            if ':' not in server:
                raise ValueError('No server/path on release.cfg')
            server, path = server.split(':')

    except Exception:
        logger.info('Something went wrong trying to get the connection string')
        sys.exit(1)

    return user, server, path
