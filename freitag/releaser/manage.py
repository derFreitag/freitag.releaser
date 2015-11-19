# -*- coding: utf-8 -*-
from argh import ArghParser
from argh.decorators import named
from freitag.releaser.changelog import GatherChangelog
from freitag.releaser.changelog import UpdateDistChangelog
from freitag.releaser.release import FullRelease
from freitag.releaser.release import ReleaseDistribution
from freitag.releaser.utils import configure_logging
from freitag.releaser.utils import push_cfg_files


def full_release(
        path='src',
        dry_run=False,
        filter_distributions='',
        debug=False
):
    """Release all distribution found on src/

    :param path: where to look for filter to release
    :type path: str
    :param dry_run: if filter will be released or only an overview
      about what's pending to be released
    :type dry_run: bool
    :param filter_distributions: only filter that match the given string will
      be considered to release
    :type filter_distributions: str
    :param debug: controls how much output is shown to the user
    :type debug: bool
    """
    configure_logging(debug)
    release_all = FullRelease(
        path=path,
        dry_run=dry_run,
        filter_distributions=filter_distributions
    )
    release_all()


def release(path, debug=False):
    """Release the distribution found on the given path

    :param path: filesystem path of the distribution about to release
    :type path: str
    :param debug: controls how much output is shown to the user
    :type debug: bool
    """
    configure_logging(debug)
    release_distribution = ReleaseDistribution(path)
    release_distribution()


@named('update-changelog')
def update_distribution_changelog(path, debug=False):
    """Update CHANGES.rst with the git changelog

    :param path: filesystem path of the distribution about to release
    :type path: str
    :param debug: controls how much output is shown to the user
    :type debug: bool
    """
    configure_logging(debug)
    changelog = UpdateDistChangelog(path)
    changelog()


def collect_changelog(debug=False):
    """Collect changes made on distributions between a commit time frame

    :param debug: controls how much output is shown to the user
    :type debug: bool
    """
    configure_logging(debug)
    changelog = GatherChangelog()
    changelog()


def publish_cfg_files(debug):
    """Push buildout .cfg files on a remote server

    :param debug: controls how much output is shown to the user
    :type debug: bool
    """
    configure_logging(debug)
    push_cfg_files()


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
