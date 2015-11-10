# -*- coding: utf-8 -*-
from argh import ArghParser
from plone.releaser.manage import checkAllPackagesForUpdates
from plone.releaser.manage import checkPackageForUpdates
from plone.releaser.manage import jenkins_report
from plone.releaser.manage import set_package_version


class Manage(object):

    def __call__(self, **kwargs):
        parser = ArghParser()

        commands = [
            checkAllPackagesForUpdates,
            checkPackageForUpdates,
            jenkins_report,
            set_package_version,
        ]

        parser.add_commands(commands)
        parser.dispatch()


manage = Manage()
