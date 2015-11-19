# -*- coding: utf-8 -*-
from freitag.releaser.changelog import UpdateDistChangelog
from git import Repo
from plone.releaser.buildout import Source
from tempfile import mkdtemp
from testfixtures import LogCapture

import os
import shutil
import unittest


class TestUpdateDistChangelog(unittest.TestCase):

    def setUp(self):
        self.upstream_repo = Repo.init(mkdtemp(), bare=True)

        self.remote_repo = self.upstream_repo.clone(mkdtemp())
        self._commit(self.remote_repo, msg='First commit')
        self.remote_repo.remote().push('master:refs/heads/master')

        self.user_repo = self.upstream_repo.clone(mkdtemp())

        # create a Source
        self.source = Source(
            protocol='git',
            url='file://{0}'.format(self.upstream_repo.working_dir),
            branch='master'
        )

    def tearDown(self):
        shutil.rmtree(self.upstream_repo.working_dir)
        shutil.rmtree(self.remote_repo.working_dir)
        shutil.rmtree(self.user_repo.working_dir)

    def _commit(self, repo, filename='dummy', msg='Random commit'):
        dummy_file = os.path.join(repo.working_tree_dir, filename)
        open(dummy_file, 'wb').close()
        repo.index.add([dummy_file, ])
        repo.index.commit(msg)

    def _get_logging_as_string(self, output):
        messages = [
            f.getMessage()
            for f in output.records
        ]
        return '\n'.join(messages)

    def test_non_existing_path(self):
        """Check that a non existing path exits early with a message"""
        path = '/tmp/probably-not-existing-path'
        changelog = UpdateDistChangelog(path)

        with LogCapture() as output:
            self.assertRaises(SystemExit, changelog)

        self.assertIn(
            '{0} does not exist'.format(path),
            self._get_logging_as_string(output)
        )
        # output is shown on info level
        self.assertEqual(
            output.records[0].levelname,
            'INFO'
        )

    def test_non_existing_file(self):
        """Check that a non existing file path exits early with a message"""
        path = self.user_repo.working_tree_dir
        changelog = UpdateDistChangelog(path)

        with LogCapture() as output:
            self.assertRaises(SystemExit, changelog)

        self.assertIn(
            '{0}/CHANGES.rst does not exist'.format(path),
            self._get_logging_as_string(output)
        )
        # output is shown on info level
        self.assertEqual(
            output.records[0].levelname,
            'INFO'
        )

    def test_git_history(self):
        """Check that the git history is shown on debug level"""
        # make some commits
        for i in range(3):
            self._commit(
                self.user_repo,
                filename='CHANGES.rst',
                msg='Commit {0}'.format(i)
            )
        # create a tag
        self.user_repo.create_tag('taaaag')
        # 2 more commits
        for i in range(3, 5):
            self._commit(
                self.user_repo,
                filename='CHANGES.rst',
                msg='Commit {0}'.format(i)
            )
        self.user_repo.remote().push()

        path = self.user_repo.working_tree_dir
        changelog = UpdateDistChangelog(path)

        with LogCapture() as output:
            changelog()

        # output is only shown on debug level
        self.assertEqual(
            output.records[0].levelname,
            'DEBUG'
        )

        # 2 commits after the tag + 1 commit on the tag
        messages = self._get_logging_as_string(output)
        self.assertEqual(
            len(messages.split('\n')),
            3
        )

    def test_changes_updated(self):
        """Check that CHANGES.rst is updated with the changelog"""
        # make some commits
        for i in range(3):
            self._commit(
                self.user_repo,
                filename='CHANGES.rst',
                msg='Commit {0}'.format(i)
            )
        # create a tag
        self.user_repo.create_tag('taaaag')
        # 2 more commits
        for i in range(3, 5):
            self._commit(
                self.user_repo,
                filename='CHANGES.rst',
                msg='Commit {0}'.format(i)
            )
        self.user_repo.remote().push()

        path = self.user_repo.working_tree_dir
        changelog = UpdateDistChangelog(path)

        with LogCapture() as output:
            changelog()

        with open('{0}/CHANGES.rst'.format(path)) as changes:
            changes_file = changes.read()

        self.assertIn(
            self._get_logging_as_string(output),
            changes_file
        )
