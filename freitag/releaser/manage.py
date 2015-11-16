# -*- coding: utf-8 -*-
from argh import ArghParser
from freitag.releaser.changelog import GatherChangelog
from freitag.releaser.changelog import UpdateDistChangelog
from freitag.releaser.release import FullRelease
from freitag.releaser.release import ReleaseDistribution
from paramiko import SSHClient
from scp import SCPClient


def full_release(path='src', dry_run=False):
    """Release all distribution found on src/"""
    # TODO: add verbosity control (-v -vv and -vvv ?)
    release_all = FullRelease(path=path, dry_run=dry_run)
    release_all()


def release(path):
    """Release the distribution found on the given path"""
    release_distribution = ReleaseDistribution(path)
    release_distribution()


def update_distribution_changelog(path):
    """Update CHANGES.rst with the git changelog"""
    changelog = UpdateDistChangelog(path)
    changelog()


def collect_changelog():
    """Collect changes made on distributions between a commit time frame."""
    changelog = GatherChangelog()
    changelog()


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
            full_release,
            release,
            collect_changelog,
            publish_cfg_files,
            sync_batou,
            update_distribution_changelog,
        ]

        parser.add_commands(commands)
        parser.dispatch()


manage = Manage()
