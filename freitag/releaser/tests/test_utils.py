# -*- coding: utf-8 -*-
from freitag.releaser.utils import is_branch_synced
from freitag.releaser.utils import update_branch
from git import Repo
from tempfile import mkdtemp
from testfixtures import OutputCapture

import os
import shutil
import unittest


class TestUtils(unittest.TestCase):

    def setUp(self):
        self.upstream_repo = Repo.init(mkdtemp(), bare=True)
        self.remote_repo = self.upstream_repo.clone(mkdtemp())
        self._commit(self.remote_repo, msg='First commit')
        self.remote_repo.remote().push('master:refs/heads/master')
        self.user_repo = self.upstream_repo.clone(mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.upstream_repo.working_dir)
        shutil.rmtree(self.remote_repo.working_dir)
        shutil.rmtree(self.user_repo.working_dir)

    def _add_commit_on_branch(self, repo, branch='master'):
        if branch not in repo.heads:
            repo.create_head(branch)
        repo.heads[branch].checkout()
        self._commit(repo)

    def _commit(self, repo, msg='Random commit'):
        dummy_file = os.path.join(repo.working_tree_dir, 'dummy')
        open(dummy_file, 'wb').close()
        repo.index.add([dummy_file, ])
        repo.index.commit(msg)

    def test_update_branch(self):
        """Check that branch really gets updated"""
        # local has one commit
        commits = len([c for c in self.user_repo.iter_commits()])
        self.assertEqual(
            commits,
            1
        )

        # add a commit upstream
        self._commit(self.remote_repo, msg='Second commit')
        self.remote_repo.remote().push()
        commits = len([c for c in self.upstream_repo.iter_commits()])
        self.assertEqual(
            commits,
            2
        )

        # update the branch
        update_branch(self.user_repo, 'master')

        # local has two commits now as well
        commits = len([c for c in self.user_repo.iter_commits()])
        self.assertEqual(
            commits,
            2
        )

    def test_update_non_existing_branch(self):
        """Check that trying to update a non-existing branch does not fail"""
        with OutputCapture():
            result = update_branch(self.user_repo, 'non-existing-branch')

        self.assertFalse(result)

    def test_is_branch_synced_in_sync(self):
        """Check that synchronicity is tested correctly"""
        with OutputCapture() as output:
            result = is_branch_synced(self.user_repo)

        self.assertTrue(result)
        self.assertEqual(
            output.captured,
            ''
        )

    def test_is_branch_synced_out_of_sync(self):
        """Check that synchronicity is tested correctly"""
        # add a remote commit
        self._commit(self.remote_repo, msg='Second commit')
        self.remote_repo.remote().push()

        with OutputCapture() as output:
            result = is_branch_synced(self.user_repo)

        self.assertFalse(result)
        self.assertEqual(
            output.captured,
            ''
        )

    def test_is_branch_synced_non_existing_local_branch(self):
        """Check that if a branch does not exist locally it reports so"""
        with OutputCapture() as output:
            result = is_branch_synced(
                self.user_repo,
                'non-existing-branch'
            )
        self.assertTrue(result)
        self.assertIn(
            'non-existing-branch branch does not exist locally',
            output.captured
        )

    def test_is_branch_synced_non_existing_remote_branch(self):
        """Check that if a branch does not exist remotely it reports so"""
        # create a local branch
        branch_name = 'local-branch'
        self.user_repo.create_head(branch_name)
        self.user_repo.heads[branch_name].checkout()

        with OutputCapture() as output:
            result = is_branch_synced(
                self.user_repo,
                branch_name
            )

        self.assertFalse(result)
        self.assertIn(
            '{0} branch does not exist remotely'.format(branch_name),
            output.captured
        )
