# -*- coding: utf-8 -*-
from contextlib import contextmanager
from git import Repo
from paramiko import SSHClient
from scp import SCPClient
from shutil import rmtree
from tempfile import mkdtemp

import os
import sys


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
        print('branch {0} does not exist remotely'.format(branch))
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
        print('{0} branch does not exist locally'.format(branch))
        # no problem then, all commits are pushed
        return True

    try:
        remote_branch = remote.refs[branch]
    except IndexError:
        print('{0} branch does not exist remotely'.format(branch))
        # it's pointless to check if a branch has local commits if it does
        # not exist remotely
        return False

    local_commit = local_branch.commit.hexsha
    remote_commit = remote_branch.commit.hexsha

    if local_commit != remote_commit:
        return False

    return True


def get_compact_git_history(repo, tag):
    return repo.git.log(
        '--oneline',
        '--graph',
        '{0}~1..master'.format(tag)
    )


def push_cfg_files():
    ssh = SSHClient()
    ssh.load_system_host_keys()

    ssh.connect(
        'docs.freitag-verlag.de',
        username='service',
    )

    with SCPClient(ssh.get_transport()) as scp:
        files = [
            'versions.cfg',
            'buildout.standalone.d/distribution-qa.cfg',
        ]
        scp.put(files, remote_path='sphinx')


@contextmanager
def git_repo(source, shallow=True):
    """Handle temporal git repositories.

    It ensures that a git repository is cloned on a temporal folder that is
    removed after being used.

    See an example of this kind of context managers here:
    http://preshing.com/20110920/the-python-with-statement-by-example/

    :param source: the configuration to clone the repository
    :type source: plone.releaser.buildout.Source
    :param shallow: if the clone needs to be trimmed or a complete clone
    :type shallow: bool
    """
    tmp_dir = mkdtemp()
    url = source.url
    if source.push_url is not None:
        url = source.push_url

    if shallow:
        repo = Repo.clone_from(
            source.url,
            tmp_dir,
            depth=100,
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
    :return:
    """
    current_directory = os.getcwd()
    os.chdir(new_folder)

    yield

    os.chdir(current_directory)


@contextmanager
def wrap_sys_argv():
    """Context manager to temporally save sys.argv and restore if afterwards"""
    original_args = sys.argv
    sys.argv = ['']

    yield

    sys.argv = original_args
