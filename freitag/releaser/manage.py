# -*- coding: utf-8 -*-
from argh import ArghParser
from plone.releaser.manage import checkAllPackagesForUpdates
from plone.releaser.manage import checkPackageForUpdates
from plone.releaser.manage import jenkins_report
from plone.releaser.manage import set_package_version


def release(path):
    """Release the distribution found on the given path."""
    pass


def collect_changelog():
    """Collect changes made on distributions between a commit time frame."""
    pass


def publish_cfg_files():
    """Push buildout .cfg files on a remote server."""
    pass


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
