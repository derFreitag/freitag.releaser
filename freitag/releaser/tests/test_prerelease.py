# -*- coding: utf-8 -*-
from freitag.releaser.prerelease import vcs_updated
from git import Repo
from tempfile import mkdtemp
from testfixtures import OutputCapture
from zest.releaser import utils

import os
import shutil
import unittest


# Hack for testing questions
utils.TESTMODE = True


class TestVcsUpdated(unittest.TestCase):

    def setUp(self):
        self.upstream_repo = Repo.init(mkdtemp(), bare=True)
        self.cloned_repo = self.upstream_repo.clone(mkdtemp())
        self._commit(self.cloned_repo, msg='First commit')
        self.cloned_repo.remote().push('master:refs/heads/master')
        self.third_repo = self.upstream_repo.clone(mkdtemp())

        self.data = {
            'workingdir': self.cloned_repo.working_tree_dir,
        }

        # by default it answers 'yes' to the question on vcs_updated
        utils.test_answer_book.set_answers(['y', ])

    def tearDown(self):
        shutil.rmtree(self.upstream_repo.working_dir)
        shutil.rmtree(self.cloned_repo.working_dir)
        shutil.rmtree(self.third_repo.working_dir)

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
            vcs_updated(self.data)
        # no output means no question was asked
        self.assertEqual(
            output.captured,
            ''
        )
        shutil.rmtree(folder)

    def test_no_update(self):
        """What if the user does not want to update to latest version.

        If the user does not want to look for upstream changes on her branches
        the entry point should end silently.
        """
        utils.test_answer_book.set_answers(['n', ])
        with OutputCapture() as output:
            vcs_updated(self.data)
        # no output means no question was asked
        self.assertIn(
            'Do you want to update',
            output.captured,
        )

    def test_no_develop_branch(self):
        """What if a develop branch does not exist.

        If the git repository does not have a develop branch the entry point
        should end silently.
        """
        with OutputCapture() as output:
            vcs_updated(self.data)

        # output after the question
        text = '\n'.join(output.captured.split('\n')[2:])
        self.assertNotIn(
            'develop',
            text,
        )

    def test_up_to_date_develop_branch(self):
        """What if the develop branch is already up-to-date.

        The entry point should say so.
        """
        # add a commit on a develop branch and push it
        self._add_commit_on_branch(self.cloned_repo, branch='develop')
        self.cloned_repo.heads.develop.checkout()
        remote = self.cloned_repo.remote()
        remote.push('develop:refs/heads/develop')
        self.cloned_repo.branches.develop.set_tracking_branch(
            remote.refs.develop
        )

        with OutputCapture() as output:
            vcs_updated(self.data)

        self.assertIn(
            'develop branch is already updated.',
            output.captured
        )

    def test_no_local_develop_branch(self):
        """What if the develop branch does not exist locally but only upstream?

        The entry point should say so.
        """
        # add a commit on upstream repo via third_repo not via cloned_repo
        self._add_commit_on_branch(self.third_repo, branch='develop')
        self.third_repo.heads.develop.checkout()
        remote = self.third_repo.remote()
        remote.push('develop:refs/heads/develop')

        with OutputCapture() as output:
            vcs_updated(self.data)

        self.assertIn(
            'develop branch did not exist locally, checked out.',
            output.captured
        )

    def test_outdated_develop_branch(self):
        """What if the develop branch is outdated.

        The branch should be updated and the entry point should show it.
        """
        # add a commit on upstream repo via third_repo not via cloned_repo
        self._add_commit_on_branch(self.third_repo, branch='develop')
        self.third_repo.heads.develop.checkout()
        remote = self.third_repo.remote()
        remote.push('develop:refs/heads/develop')

        # fetch develop branch and check it out locally
        remote = self.cloned_repo.remote()
        remote.fetch()
        new_branch = self.cloned_repo.create_head(
            'develop',
            remote.refs['develop']
        )
        new_branch.set_tracking_branch(remote.refs['develop'])

        # more changes on develop branch
        self._add_commit_on_branch(self.third_repo, branch='develop')
        remote = self.third_repo.remote()
        remote.push('develop:refs/heads/develop')

        with OutputCapture() as output:
            vcs_updated(self.data)

        self.assertEqual(
            self.cloned_repo.branches.develop.commit,
            self.cloned_repo.remote().refs.develop.commit
        )

        self.assertIn(
            'Updated develop branch to latest commits.',
            output.captured
        )

    def test_no_master_branch(self):
        """What if a master branch does not exist.

        If the git repository does not have a master branch the entry point
        should end silently.
        """
        # rename master branch and clone again
        self.upstream_repo.refs.master.rename('dev')
        shutil.rmtree(self.cloned_repo.working_tree_dir)
        self.cloned_repo = self.upstream_repo.clone(mkdtemp())
        self.data = {
            'workingdir': self.cloned_repo.working_tree_dir,
        }

        with OutputCapture() as output:
            vcs_updated(self.data)

        # no output after the question
        text = '\n'.join(output.captured.split('\n')[2:])
        self.assertEqual(
            text,
            '',
        )

    def test_no_local_master_branch(self):
        """What if the master branch does not exist locally but only upstream?

        The entry point should say so.
        """
        # rename master branch, clone again and then create the upstream master
        # branch
        self.upstream_repo.refs.master.rename('dev')
        shutil.rmtree(self.cloned_repo.working_tree_dir)
        self.cloned_repo = self.upstream_repo.clone(mkdtemp())
        self.data = {
            'workingdir': self.cloned_repo.working_tree_dir,
        }
        self._add_commit_on_branch(self.third_repo, branch='master')
        remote = self.third_repo.remote()
        remote.push('master:refs/heads/master')

        with OutputCapture() as output:
            vcs_updated(self.data)

        self.assertIn(
            'master branch did not exist locally, checked out.',
            output.captured
        )

    def test_up_to_date_master_branch(self):
        """What if the master branch is already up-to-date.

        The entry point should say so.
        """
        with OutputCapture() as output:
            vcs_updated(self.data)

        self.assertIn(
            'master branch is already updated.',
            output.captured
        )

    def test_outdated_master_branch(self):
        """What if the master branch is outdated.

        The branch should be updated and the entry point should show it.
        """
        # add a commit on upstream repo via third_repo not via cloned_repo
        self._add_commit_on_branch(self.third_repo)
        remote = self.third_repo.remote()
        remote.push()

        # fetch develop branch and check it out locally
        remote = self.cloned_repo.remote()
        remote.fetch()

        # more changes on develop branch
        self._add_commit_on_branch(self.third_repo)
        remote = self.third_repo.remote()
        remote.push()

        with OutputCapture() as output:
            vcs_updated(self.data)

        self.assertEqual(
            self.cloned_repo.branches.master.commit,
            remote.refs.master.commit
        )

        self.assertIn(
            'Updated master branch to latest commits.',
            output.captured
        )

    def test_master_and_develop_in_sync(self):
        """What if the master and develop branches point to the same commit?

        The entry point should say so.
        """
        self.upstream_repo.create_head('develop')

        with OutputCapture() as output:
            vcs_updated(self.data)

        self.assertEqual(
            self.cloned_repo.branches.master.commit,
            self.cloned_repo.branches.develop.commit,
        )

        self.assertIn(
            'master branch is already in sync with develop branch.',
            output.captured
        )

    def test_master_and_develop_out_of_sync(self):
        """What if the master and develop branches are pointing to different
        commits?

        The master branch should  be updated and the  entry point should say
        so.
        """
        # add a commit on upstream repo via third_repo not via cloned_repo
        self._add_commit_on_branch(self.third_repo, branch='develop')
        self.third_repo.heads.develop.checkout()
        remote = self.third_repo.remote()
        remote.push('develop:refs/heads/develop')

        with OutputCapture() as output:
            vcs_updated(self.data)

        self.assertEqual(
            self.cloned_repo.branches.master.commit,
            self.cloned_repo.branches.develop.commit,
        )

        self.assertIn(
            'Rebased master branch on top of develop.',
            output.captured
        )
