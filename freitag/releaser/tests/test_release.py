# -*- coding: utf-8 -*-
from freitag.releaser.release import FullRelease
from git import Repo
from tempfile import mkdtemp
from testfixtures import OutputCapture
from zest.releaser import utils

import os
import shutil
import unittest


BUILDOUT_FILE_CONTENTS = """
[versions]

[sources]
"""

# Hack for testing questions
utils.TESTMODE = True


class TestFullRelease(unittest.TestCase):

    def setUp(self):
        self.buildout_repo = Repo.init(mkdtemp(), bare=True)

        self.remote_buildout_repo = self.buildout_repo.clone(mkdtemp())
        self._commit(
            self.remote_buildout_repo,
            content=BUILDOUT_FILE_CONTENTS,
            filename='develop.cfg',
            msg='First commit'
        )
        self.remote_buildout_repo.remote().push('master:refs/heads/master')

        self.user_buildout_repo = self.buildout_repo.clone(mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.buildout_repo.working_dir)
        shutil.rmtree(self.remote_buildout_repo.working_dir)
        shutil.rmtree(self.user_buildout_repo.working_dir)

    def _commit(self, repo, content='', filename='dummy', msg='Random commit'):
        dummy_file = os.path.join(repo.working_tree_dir, filename)
        with open(dummy_file, 'w') as afile:
            afile.write(content)
        repo.index.add([dummy_file, ])
        repo.index.commit(msg)

    def test_create_instance(self):
        """Check that the values passed on creation are safed"""
        path = '/tmp/la/li/somewhere'
        dry_run = True
        dist_filter = 'some random filter'

        full_release = FullRelease(
            path=path,
            dry_run=dry_run,
            filter_distributions=dist_filter
        )
        self.assertEqual(
            full_release.path,
            path
        )
        self.assertEqual(
            full_release.dry_run,
            dry_run
        )
        self.assertEqual(
            full_release.filter,
            dist_filter
        )

    def test_get_all_distributions_folder(self):
        """Check that a folder is not considered a distribution"""
        path = '{0}/src'.format(self.user_buildout_repo.working_tree_dir)
        # create a folder
        os.makedirs('{0}/folder-not-repo'.format(path))

        full_release = FullRelease(path=path)

        with OutputCapture():
            full_release.get_all_distributions()

        self.assertEqual(
            full_release.distributions,
            []
        )

    def test_get_all_distributions_file(self):
        """Check that a file is not considered a distribution"""
        path = '{0}/src'.format(self.user_buildout_repo.working_tree_dir)
        # create a file
        os.makedirs(path)
        with open('{0}/random-file'.format(path), 'w') as afile:
            afile.write('something')

        full_release = FullRelease(path=path)

        with OutputCapture():
            full_release.get_all_distributions()

        self.assertEqual(
            full_release.distributions,
            []
        )

    def test_get_all_distributions_repo(self):
        """Check that a git repository is considered a distribution"""
        path = '{0}/src'.format(self.user_buildout_repo.working_tree_dir)
        os.makedirs(path)
        repo_folder = '{0}/my.distribution'.format(path)
        repo1 = self.buildout_repo.clone(repo_folder)
        repo_folder = '{0}/my.distribution2'.format(path)
        repo2 = self.buildout_repo.clone(repo_folder)

        full_release = FullRelease(path=path)

        with OutputCapture():
            full_release.get_all_distributions()

        self.assertEqual(
            full_release.distributions,
            [repo1.working_tree_dir, repo2.working_tree_dir, ]
        )

    def test_check_pending_local_changes_dirty(self):
        """Check that a repository with local changes (uncommitted) is removed
        from the list of distributions to be released
        """
        # create repo
        path = '{0}/src'.format(self.user_buildout_repo.working_tree_dir)
        os.makedirs(path)
        repo_folder = '{0}/my.distribution'.format(path)
        repo = self.buildout_repo.clone(repo_folder)

        # add a file
        file_path = '{0}/tmp_file'.format(repo_folder)
        with open(file_path, 'w') as afile:
            afile.write('something')
            repo.index.add([file_path, ])

        # full release
        full_release = FullRelease(path=path)
        full_release.distributions = [repo_folder, ]

        utils.test_answer_book.set_answers(['Y', ])
        with OutputCapture():
            full_release.check_pending_local_changes()

        # check the distribution is removed
        self.assertEqual(
            full_release.distributions,
            []
        )

    def test_check_pending_local_changes_unpushed(self):
        """Check that a repository with local commits is removed from the list
        of distributions to be released
        """
        # create repo
        path = '{0}/src'.format(self.user_buildout_repo.working_tree_dir)
        os.makedirs(path)
        repo_folder = '{0}/my.distribution'.format(path)
        repo = self.buildout_repo.clone(repo_folder)

        # make a commit on the repo
        self._commit(repo)

        # full release
        full_release = FullRelease(path=path)
        full_release.distributions = [repo_folder, ]

        utils.test_answer_book.set_answers(['Y', ])
        with OutputCapture():
            full_release.check_pending_local_changes()

        # check the distribution is removed
        self.assertEqual(
            full_release.distributions,
            []
        )

    def test_check_pending_local_changes_exit(self):
        """Check that if a repository has local commits you are given the
        option to quit.
        """
        # create repo
        path = '{0}/src'.format(self.user_buildout_repo.working_tree_dir)
        os.makedirs(path)
        repo_folder = '{0}/my.distribution'.format(path)
        repo = self.buildout_repo.clone(repo_folder)

        # make a commit on the repo
        self._commit(repo)

        # full release
        full_release = FullRelease(path=path)
        full_release.distributions = [repo_folder, ]

        utils.test_answer_book.set_answers(['n', ])
        with OutputCapture():
            self.assertRaises(
                SystemExit,
                full_release.check_pending_local_changes
            )

    def test_check_pending_local_changes_unpushed_dry_run(self):
        """Check that a repository with local commits is *not* removed from
        the list of distributions to be released if dry_run is True
        """
        # create repo
        path = '{0}/src'.format(self.user_buildout_repo.working_tree_dir)
        os.makedirs(path)
        repo_folder = '{0}/my.distribution'.format(path)
        repo = self.buildout_repo.clone(repo_folder)

        # make a commit on the repo
        self._commit(repo)

        # full release
        full_release = FullRelease(path=path, dry_run=True)
        full_release.distributions = [repo_folder, ]

        with OutputCapture():
            full_release.check_pending_local_changes()

        # check the distribution is not removed
        self.assertEqual(
            full_release.distributions,
            [repo_folder, ]
        )

    def test_check_pending_local_changes_clean(self):
        """Check that a clean repository is not removed from the list of
        distributions to be released
        """
        # create repo
        path = '{0}/src'.format(self.user_buildout_repo.working_tree_dir)
        os.makedirs(path)
        repo_folder = '{0}/my.distribution'.format(path)
        self.buildout_repo.clone(repo_folder)

        # full release
        full_release = FullRelease(path=path)
        full_release.distributions = [repo_folder, ]

        utils.test_answer_book.set_answers(['Y', ])
        with OutputCapture():
            full_release.check_pending_local_changes()

        # check the distribution is not removed
        self.assertEqual(
            full_release.distributions,
            [repo_folder, ]
        )

    def test_changes_to_be_released_no_tag(self):
        """Check that if a distribution does not have any tag is kept as a
        distribution that needs to be released
        """
        # create repo
        path = '{0}/src'.format(self.user_buildout_repo.working_tree_dir)
        os.makedirs(path)
        repo_folder = '{0}/my.distribution'.format(path)
        repo = self.buildout_repo.clone(repo_folder)

        # create some commits
        self._commit(repo)
        self._commit(repo)
        repo.remote().push()

        # full release
        full_release = FullRelease(path=path)
        full_release.distributions = [repo_folder, ]

        # run check_changes_to_be_released
        with OutputCapture():
            full_release.check_changes_to_be_released()

        # check that the distribution is still there
        self.assertEqual(
            full_release.distributions,
            [repo_folder, ]
        )

    def test_changes_to_be_released_nothing_to_release(self):
        """Check that if there is a tag on the last commit the distribution is
        removed from the list of distributions needing a release
        """
        # create repo
        path = '{0}/src'.format(self.user_buildout_repo.working_tree_dir)
        os.makedirs(path)
        repo_folder = '{0}/my.distribution'.format(path)
        repo = self.buildout_repo.clone(repo_folder)

        # create a tag
        repo.create_tag('my-tag')

        # full release
        full_release = FullRelease(path=path)
        full_release.distributions = [repo_folder, ]

        # run check_changes_to_be_released
        with OutputCapture():
            full_release.check_changes_to_be_released()

        # check that the distribution is still there
        self.assertEqual(
            full_release.distributions,
            []
        )

    def test_changes_to_be_released_commits_to_release(self):
        """Check that if there is a tag on the last commit the distribution is
        removed from the list of distributions needing a release
        """
        # create repo
        path = '{0}/src'.format(self.user_buildout_repo.working_tree_dir)
        os.makedirs(path)
        repo_folder = '{0}/my.distribution'.format(path)
        repo = self.buildout_repo.clone(repo_folder)

        # create a tag
        repo.create_tag('my-tag')

        # create a commit
        self._commit(repo)
        repo.remote().push()

        # full release
        full_release = FullRelease(path=path)
        full_release.distributions = [repo_folder, ]

        # run check_changes_to_be_released
        with OutputCapture():
            full_release.check_changes_to_be_released()

        # check that the distribution is still there
        self.assertEqual(
            full_release.distributions,
            [repo_folder, ]
        )

    def test_changes_to_be_released_dry_run(self):
        """Check that if the distribution was supposed to be removed, it is not
        if dry_run is True
        """
        # create repo
        path = '{0}/src'.format(self.user_buildout_repo.working_tree_dir)
        os.makedirs(path)
        repo_folder = '{0}/my.distribution'.format(path)
        repo = self.buildout_repo.clone(repo_folder)

        # create a tag
        repo.create_tag('my-tag')

        # full release
        full_release = FullRelease(path=path, dry_run=True)
        full_release.distributions = [repo_folder, ]

        # run check_changes_to_be_released
        with OutputCapture():
            full_release.check_changes_to_be_released()

        # check that the distribution is still there
        self.assertEqual(
            full_release.distributions,
            [repo_folder, ]
        )

    def test_changes_to_be_released_last_tags_filled(self):
        """Check that if the distribution has a tag is stored on last_tags dict
        """
        # create repo
        path = '{0}/src'.format(self.user_buildout_repo.working_tree_dir)
        os.makedirs(path)
        repo_folder = '{0}/my.distribution'.format(path)
        repo = self.buildout_repo.clone(repo_folder)

        # create a tag
        repo.create_tag('my-tag')

        # full release
        full_release = FullRelease(path=path)
        full_release.distributions = [repo_folder, ]

        # run check_changes_to_be_released
        with OutputCapture():
            full_release.check_changes_to_be_released()

        # check that the tag has been saved on the dictionary
        self.assertEqual(
            full_release.last_tags['my.distribution'],
            'my-tag'
        )

    def test_changes_to_be_released_last_tags_no_tag(self):
        """Check that if the distribution does not have a tag the latest
        commit is stored on last_tags dict
        """
        # create repo
        path = '{0}/src'.format(self.user_buildout_repo.working_tree_dir)
        os.makedirs(path)
        repo_folder = '{0}/my.distribution'.format(path)
        repo = self.buildout_repo.clone(repo_folder)

        # create some commits
        self._commit(repo)
        self._commit(repo)
        repo.remote().push()

        # full release
        full_release = FullRelease(path=path)
        full_release.distributions = [repo_folder, ]

        # run check_changes_to_be_released
        with OutputCapture():
            full_release.check_changes_to_be_released()

        # check that the distribution key has been created
        self.assertIn(
            'my.distribution',
            full_release.last_tags
        )

        # check that what's stored is the hexsha of a commit
        commit = [
            c
            for c in repo.iter_commits()
            if c.hexsha == full_release.last_tags['my.distribution']
        ]
        self.assertEqual(
            len(commit),
            1
        )
