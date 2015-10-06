# -*- coding: utf-8 -*-
from freitag.releaser.postrelease import update_branches
from git import Repo
from tempfile import mkdtemp
from testfixtures import OutputCapture
from zest.releaser import utils

import os
import shutil
import unittest


# Hack for testing questions
utils.TESTMODE = True


class TestUpdateBranches(unittest.TestCase):

    def setUp(self):
        self.upstream_repo = Repo.init(mkdtemp(), bare=True)
        self.cloned_repo = self.upstream_repo.clone(mkdtemp())
        self._commit(self.cloned_repo, msg='First commit')
        self.cloned_repo.remote().push('master:refs/heads/master')

        self.data = {
            'workingdir': self.cloned_repo.working_tree_dir,
        }

        # by default it answers 'yes' to the question on vcs_updated
        utils.test_answer_book.set_answers(['y', ])

    def tearDown(self):
        shutil.rmtree(self.upstream_repo.working_dir)
        shutil.rmtree(self.cloned_repo.working_dir)

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

    def test_no_git_repo(self):
        """What if the repository is not git controlled.

        No question should be asked and the entry point should end silently.
        """
        # Override the directory to somewhere where no git repository exists.
        folder = mkdtemp()
        self.data = {
            'workingdir': folder,
        }
        with OutputCapture() as output:
            update_branches(self.data)
        # no output means no question was asked
        self.assertEqual(
            output.captured,
            ''
        )
        shutil.rmtree(folder)

    def test_no_develop_branch(self):
        """What if a develop branch does not exist.

        If the git repository does not have a develop branch the entry point
        should end silently.
        """
        with OutputCapture() as output:
            update_branches(self.data)

        # no output means no question was asked
        self.assertEqual(
            output.captured,
            ''
        )

    def test_no_want_to_update(self):
        """What if a develop branch does not exist.

        If the git repository does not have a develop branch the entry point
        should end silently.
        """
        self.cloned_repo.create_head('develop')
        utils.test_answer_book.set_answers(['n', ])
        with OutputCapture() as output:
            update_branches(self.data)

        # it has not been changed to master branch
        self.assertEqual(
            self.cloned_repo.head.ref.name,
            self.cloned_repo.branches.master.name,
        )

        self.assertTrue(
            'Do you want to update' in output.captured
        )

    def test_update_develop_branch(self):
        """What if the user wants to update the develop branch.

        develop branch should be rebased on top of master and the be left
        as the current active branch.
        """
        self.cloned_repo.create_head('develop')
        self._add_commit_on_branch(self.cloned_repo)
        remote = self.cloned_repo.remote()
        remote.push()

        with OutputCapture():
            update_branches(self.data)

        self.assertEqual(
            self.cloned_repo.head.ref,
            self.cloned_repo.branches.develop
        )

        # master and develop point to the same commit
        self.assertEqual(
            self.cloned_repo.branches.develop.commit,
            self.cloned_repo.branches.master.commit,
        )
