# -*- coding: utf-8 -*-
from freitag.releaser.utils import update_repo
from git import InvalidGitRepositoryError
from git import Repo
from zest.releaser.utils import ask

import os
import subprocess
import sys


def vcs_updated(data):
    try:
        repo = Repo(data['workingdir'])
    except InvalidGitRepositoryError:
        return

    if not ask('Do you want to update develop and master branches?'):
        return

    update_repo(repo)


def check_translations(data):
    """Check that all strings are marked as translatable."""
    if not os.path.exists('{0}/bin/i18ndude'.format(data['workingdir'])):
        return

    process = subprocess.Popen(
        ['bin/i18ndude', 'find-untranslated', '-n', 'src/', ],
        stdout=subprocess.PIPE
    )
    stdout, stderr = process.communicate()
    if 'ERROR' not in stdout:
        return

    print(stdout)
    msg = 'There are strings not marked as translatable, ' \
          'do you want to continue?'
    if not ask(msg, default=False):
        sys.exit(1)
