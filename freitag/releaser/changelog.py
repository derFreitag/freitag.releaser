# -*- coding: utf-8 -*-
from freitag.releaser.utils import filter_git_history
from freitag.releaser.utils import get_compact_git_history
from freitag.releaser.utils import get_latest_tag
from git import Repo

import logging
import os
import re
import sys


logger = logging.getLogger(__name__)

CHANGELOG_ENTRY = """- {1}
  https://www.pivotaltracker.com/story/show/{0}
  [gforcada]
"""

PARSE_GIT_CHANGELOG_RE = re.compile(r'\[\#(\d+)\]\s+([\s\w]+)')


class UpdateDistChangelog(object):
    """Update CHANGES.rst on the given distribution"""

    #: system path where the distribution should be found
    path = None

    def __init__(self, path):
        self.path = path

    def __call__(self):
        if not os.path.exists(self.path):
            logger.info('{0} does not exist'.format(self.path))
            sys.exit(1)

        self.write_changes()

    def write_changes(self, changes_path=None, history=None):
        if changes_path is None:
            changes_path = self.get_changes_path()

        if history is None:
            history = self.get_git_history()

        with open(changes_path) as changes:
            current_data = changes.read()

        with open(changes_path, 'w') as changes:
            changes.write(history.encode('utf-8'))
            changes.write('\n')
            changes.write('\n')
            for line in history.split('\n'):
                parsed = PARSE_GIT_CHANGELOG_RE.search(line)
                if parsed:
                    changes.write(CHANGELOG_ENTRY.format(*parsed.groups()))
            changes.write('\n')
            changes.write('\n')
            changes.write(current_data)

    def get_changes_path(self):
        changes_path = '{0}/CHANGES.rst'.format(self.path)
        if not os.path.exists(changes_path):
            logger.info('{0} does not exist'.format(changes_path))
            sys.exit(1)

        return changes_path

    def get_git_history(self):
        repo = Repo(self.path)
        latest_tag = get_latest_tag(repo, 'master')
        history = get_compact_git_history(repo, latest_tag)
        cleaned_git_changes = filter_git_history(history)
        logger.debug(cleaned_git_changes)

        return cleaned_git_changes
