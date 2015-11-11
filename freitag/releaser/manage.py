# -*- coding: utf-8 -*-
from argh import ArghParser
from git import Repo
from paramiko import SSHClient
from plone.releaser.buildout import Buildout
from plone.releaser.manage import checkAllPackagesForUpdates
from plone.releaser.manage import checkPackageForUpdates
from plone.releaser.manage import jenkins_report
from plone.releaser.manage import set_package_version
from scp import SCPClient
from zest.releaser import fullrelease

import os
import sys


DISTRIBUTION = '\033[1;91m{0}\033[0m'
BRANCH = PATH = '\033[1;30m{0}\033[0m'


def release(path):
    """Release the distribution found on the given path."""
    distribution_name = path.split('/')[1]

    _check_master_branch()
    _check_distribution_exists(path)
    version = _release(path)

    buildout = Buildout(
        sources_file='develop.cfg',
        checkouts_file='develop.cfg',
    )
    buildout.set_version(distribution_name, version)


def _check_master_branch():
    repo = Repo(os.path.curdir)
    current_branch = repo.active_branch.name

    if current_branch != 'master':
        text = '{0} is not on master branch, but on {1}'
        raise ValueError(
            text.format(
                DISTRIBUTION.format('zope repository'),
                BRANCH.format(current_branch)
            )
        )


def _check_distribution_exists(path):
    """Check that the folder exists"""
    if not os.path.exists(path):
        raise IOError(
            'Path {0} does NOT exist'.format(PATH.format(path))
        )


def _release(path):
    """Release the distribution"""
    # remove arguments so zest.releaser is not confused
    # will be fixed by https://github.com/zestsoftware/zest.releaser/issues/146
    original_args = sys.argv
    sys.argv = ['']

    # change to the distribution root folder
    original_path = os.getcwd()
    os.chdir(path)

    fullrelease.main()

    os.chdir(original_path)
    sys.argv = original_args

    repo = Repo(path)
    return repo.tags[-1].name


def collect_changelog():
    """Collect changes made on distributions between a commit time frame."""
    pass


def publish_cfg_files():
    """Push buildout .cfg files on a remote server."""
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


def sync_batou():
    """Update version pins on batou"""
    pass


class Manage(object):

    def __call__(self, **kwargs):
        parser = ArghParser()

        commands = [
            checkAllPackagesForUpdates,
            checkPackageForUpdates,
            jenkins_report,
            set_package_version,
            release,
            collect_changelog,
            publish_cfg_files,
            sync_batou,
        ]

        parser.add_commands(commands)
        parser.dispatch()


manage = Manage()
