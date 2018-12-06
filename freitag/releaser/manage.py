# -*- coding: utf-8 -*-
from argh import arg
from argh import ArghParser
from argh.decorators import named
from freitag.releaser.release import FullRelease
from freitag.releaser.utils import check_connection
from freitag.releaser.utils import check_delivery_servers
from freitag.releaser.utils import configure_logging
from freitag.releaser.utils import push_cfg_files


@named('r')
@arg('-f', '--filter-distributions', nargs='*')
def full_release(
    path='src',
    test=False,
    filter_distributions=None,
    debug=False,
    offline=False,
    branch='master',
):
    """Release all distribution found on src/

    :param path: where to look for filter to release
    :type path: str
    :param test: if distributions will be released or only an overview
      about what's pending to be released
    :type test: bool
    :param filter_distributions: only distributions that match the given
      string will be considered to release (multiples can be specified
      space-separated)
    :type filter_distributions: str
    :param debug: controls how much output is shown to the user
    :type debug: bool
    :param offline: controls if network will be used (turns test on as well)
    :type offline: bool
    :param branch: which branch should be used as a base for comparsion
    :type branch: string
    """
    configure_logging(debug)
    check_connection()
    release_all = FullRelease(
        path=path,
        test=test,
        filter_distributions=filter_distributions,
        offline=offline,
        branch=branch,
    )
    release_all()


@named('push')
def publish_cfg_files(debug=False):
    """Push buildout .cfg files on a remote server

    :param debug: controls how much output is shown to the user
    :type debug: bool
    """
    configure_logging(debug)
    check_connection()
    push_cfg_files()


@named('assets')
def publish_assets(debug=False):
    """Push freitag.theme assets to delivery servers

    :param debug: controls how much output is shown to the user
    :type debug: bool
    """
    configure_logging(debug)
    check_delivery_servers()
    release = FullRelease(path='src')
    release.distributions = ['src/freitag.theme', ]
    release.assets()


class Manage(object):

    def __call__(self, **kwargs):
        parser = ArghParser()
        commands = [
            full_release,
            publish_cfg_files,
            publish_assets,
        ]

        parser.add_commands(commands)
        parser.dispatch()


manage = Manage()
