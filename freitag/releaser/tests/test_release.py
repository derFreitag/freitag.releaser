# -*- coding: utf-8 -*-
from freitag.releaser.release import FullRelease
from freitag.releaser.release import ReleaseDistribution
from freitag.releaser.utils import wrap_folder
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
{0}
"""

CHANGES = """

Changelog
=========

0.1 (unreleased)
----------------

- change log entry 1

- change log entry 2

0.0.1 (2015-11-12)
------------------

- Initial release
"""

# Hack for testing questions
utils.TESTMODE = True


class BaseTest(unittest.TestCase):

    def setUp(self):
        self.buildout_repo = Repo.init(mkdtemp(), bare=True)

        self.remote_buildout_repo = self.buildout_repo.clone(mkdtemp())
        self._commit(
            self.remote_buildout_repo,
            content=BUILDOUT_FILE_CONTENTS.format(''),
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

        return repo.commit().hexsha

    def _add_source(self, repo):
        source_line = 'my.distribution = git file://{0}'.format(
            repo.working_tree_dir
        )
        self._commit(
            repo,
            content=BUILDOUT_FILE_CONTENTS.format(source_line),
            filename='develop.cfg',
            msg='Add source'
        )

    def _add_changes(self, repo):
        self._commit(
            self.user_buildout_repo,
            content=CHANGES,
            filename='CHANGES.rst',
            msg='Update changes'
        )


class TestFullRelease(BaseTest):

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

    def test_filter_distros_no_filter(self):
        """Check that if no filter is applied all distributions are used"""
        full_release = FullRelease()
        full_release.distributions = ['one', 'two', 'three', ]
        with OutputCapture():
            full_release.filter_distros()

        self.assertEqual(
            full_release.distributions,
            ['one', 'two', 'three', ]
        )

    def test_filter_distros_filter(self):
        """Check that if a filter is applied only the matching distributions
        are kept
        """
        full_release = FullRelease(filter_distributions='w')
        full_release.distributions = ['one', 'two', 'three', ]
        with OutputCapture():
            full_release.filter_distros()

        self.assertEqual(
            full_release.distributions,
            ['two', ]
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

    def test_ask_what_to_release_no_source(self):
        """Check that if the distribution has no source defined it will not be
        released
        """
        path = '{0}/src'.format(self.user_buildout_repo.working_tree_dir)
        repo_folder = '{0}/my.distribution'.format(path)

        # full release
        full_release = FullRelease(path=path)
        full_release.distributions = [repo_folder, ]

        # run check_changes_to_be_released
        with wrap_folder(self.user_buildout_repo.working_tree_dir):
            with OutputCapture():
                full_release.ask_what_to_release()

        # check that the distribution is not going to be released
        self.assertEqual(
            full_release.distributions,
            []
        )

    def test_ask_what_to_release_clean_some_lines_of_git_history(self):
        """Check that if the some commits are administrative they are not
        shown to the user, the other non-administrative are shown
        """
        repo = self.user_buildout_repo

        # add some commits
        # save the sha to make the git history go as back as to this commit
        first_commit_sha = self._commit(repo, msg='Random commit 1')
        self._commit(repo, msg='Random commit 2')
        self._commit(repo, msg='Random commit 3')
        # this one will be filtered
        self._commit(repo, msg='Bump version this is not kept')

        # add source, CHANGES.rst and push the repo
        self._add_source(repo)
        self._add_changes(repo)
        self.user_buildout_repo.remote().push()

        # clone the repo
        path = '{0}/src'.format(self.user_buildout_repo.working_tree_dir)
        os.makedirs(path)
        repo_folder = '{0}/my.distribution'.format(path)
        self.buildout_repo.clone(repo_folder)

        # full release
        full_release = FullRelease(path=path)
        full_release.distributions = [repo_folder, ]
        full_release.last_tags['my.distribution'] = first_commit_sha

        utils.test_answer_book.set_answers(['Y', ])
        with wrap_folder(self.user_buildout_repo.working_tree_dir):
            with OutputCapture() as output:
                full_release.ask_what_to_release()

        self.assertIn(
            'Random commit 2',
            output.captured
        )

        self.assertNotIn(
            'Bump version',
            output.captured
        )

        self.assertIn(
            'Add source',
            output.captured
        )

    def test_ask_what_to_release_clean_all_lines_of_git_history(self):
        """Check that if the commits on the distribution are only
        administrative ones, the distribution is discarded
        """
        repo = self.user_buildout_repo

        # add source, CHANGES.rst, commits and push the repo
        self._add_source(repo)
        self._add_changes(repo)
        first_commit_sha = self._commit(repo, msg='Back to development')
        self._commit(repo, msg='New version:')
        self._commit(repo, msg='Preparing release la la')

        self.user_buildout_repo.remote().push()

        # clone the repo
        path = '{0}/src'.format(self.user_buildout_repo.working_tree_dir)
        os.makedirs(path)
        repo_folder = '{0}/my.distribution'.format(path)
        self.buildout_repo.clone(repo_folder)

        # full release
        full_release = FullRelease(path=path)
        full_release.distributions = [repo_folder, ]
        full_release.last_tags['my.distribution'] = first_commit_sha

        with wrap_folder(self.user_buildout_repo.working_tree_dir):
            with OutputCapture():
                full_release.ask_what_to_release()

        # check that the distribution is not going to be released
        self.assertEqual(
            full_release.distributions,
            []
        )

    def test_ask_what_to_release_changes_rst_is_shown(self):
        """Check that the CHANGES.rst are shown to the user"""
        repo = self.user_buildout_repo

        # add source, CHANGES.rst, commits and push the repo
        self._add_source(repo)
        self._add_changes(repo)
        first_commit_sha = self._commit(repo, msg='Random commit 1')
        self.user_buildout_repo.remote().push()

        # clone the repo
        path = '{0}/src'.format(self.user_buildout_repo.working_tree_dir)
        os.makedirs(path)
        repo_folder = '{0}/my.distribution'.format(path)
        self.buildout_repo.clone(repo_folder)

        # full release
        full_release = FullRelease(path=path)
        full_release.distributions = [repo_folder, ]
        full_release.last_tags['my.distribution'] = first_commit_sha

        utils.test_answer_book.set_answers(['Y', ])
        with wrap_folder(self.user_buildout_repo.working_tree_dir):
            with OutputCapture() as output:
                full_release.ask_what_to_release()

        self.assertIn(
            'change log entry 1',
            output.captured
        )
        self.assertIn(
            'change log entry 2',
            output.captured
        )

    def test_ask_what_to_release_dry_run(self):
        """Check that in dry_run mode no question is asked"""
        repo = self.user_buildout_repo

        # add source, CHANGES.rst, commits and push the repo
        self._add_source(repo)
        self._add_changes(repo)
        first_commit_sha = self._commit(repo, msg='Random commit 1')
        self.user_buildout_repo.remote().push()

        # clone the repo
        path = '{0}/src'.format(self.user_buildout_repo.working_tree_dir)
        os.makedirs(path)
        repo_folder = '{0}/my.distribution'.format(path)
        self.buildout_repo.clone(repo_folder)

        # full release
        full_release = FullRelease(path=path, dry_run=True)
        full_release.distributions = [repo_folder, ]
        full_release.last_tags['my.distribution'] = first_commit_sha

        with wrap_folder(self.user_buildout_repo.working_tree_dir):
            with OutputCapture() as output:
                full_release.ask_what_to_release()

        self.assertEqual(
            full_release.distributions,
            [repo_folder, ]
        )
        self.assertNotIn(
            'Is the change log ready for release?',
            output.captured
        )

    def test_ask_what_to_release_user_can_not_release_a_distribution(self):
        """Check that even if the distribution meets all the criteria,
        the user can still decide not to release it
        """
        repo = self.user_buildout_repo

        # add source, CHANGES.rst, commits and push the repo
        self._add_source(repo)
        self._add_changes(repo)
        first_commit_sha = self._commit(repo, msg='Random commit 1')
        self.user_buildout_repo.remote().push()

        # clone the repo
        path = '{0}/src'.format(self.user_buildout_repo.working_tree_dir)
        os.makedirs(path)
        repo_folder = '{0}/my.distribution'.format(path)
        self.buildout_repo.clone(repo_folder)

        # full release
        full_release = FullRelease(path=path)
        full_release.distributions = [repo_folder, ]
        full_release.last_tags['my.distribution'] = first_commit_sha

        utils.test_answer_book.set_answers(['n', ])
        with wrap_folder(self.user_buildout_repo.working_tree_dir):
            with OutputCapture() as output:
                full_release.ask_what_to_release()

        self.assertEqual(
            full_release.distributions,
            []
        )
        self.assertIn(
            'Is the change log ready for release?',
            output.captured
        )

    def test_create_commit_message(self):
        """Check that the commit message is generated correctly"""
        full_release = FullRelease()
        full_release.versions['my.distribution'] = '3.4.5'
        full_release.versions['my.other'] = '5.4.3'
        full_release.versions['last.one'] = '1.2'

        full_release.changelogs['my.distribution'] = '\n'.join([
            '- one change',
            '  [gforcada]',
            '',
            '- second change',
            '  [someone else]'
            ''
        ])
        full_release.changelogs['my.other'] = '\n'.join([
            '- third change',
            '  [gforcada]',
            '',
            '- related one',
            '  [someone else]'
            ''
        ])
        full_release.changelogs['last.one'] = '\n'.join([
            '- one more change',
            '  [gforcada]',
            '',
            '- really last change',
            '  [someone else]'
            ''
        ])

        self.assertEqual(
            full_release.commit_message,
            ''
        )

        full_release._create_commit_message()

        self.assertEqual(
            full_release.commit_message,
            '\n'.join([
                'New releases:',
                '',
                'last.one 1.2',
                'my.distribution 3.4.5',
                'my.other 5.4.3',
                '',
                'Changelogs:',
                '',
                'last.one',
                '--------',
                '- one more change',
                '  [gforcada]',
                '',
                '- really last change',
                '  [someone else]',
                '',
                'my.distribution',
                '---------------',
                '- one change',
                '  [gforcada]',
                '',
                '- second change',
                '  [someone else]',
                '',
                'my.other',
                '--------',
                '- third change',
                '  [gforcada]',
                '',
                '- related one',
                '  [someone else]',
                '',
            ])
        )


class TestReleaseDistribution(BaseTest):

    def test_create_instance(self):
        """Check that path and name are set properly"""
        release = ReleaseDistribution('some/random/path')
        self.assertEqual(
            release.path,
            'some/random/path'
        )
        self.assertEqual(
            release.name,
            'path'
        )

    def test_check_parent_branch_on_master(self):
        """Check that the parent repository is on master branch"""
        folder = self.user_buildout_repo.working_tree_dir
        release = ReleaseDistribution(folder)

        with wrap_folder(folder):
            release._check_parent_branch()

        self.assertEqual(
            self.user_buildout_repo.active_branch.name,
            'master'
        )

    def test_check_parent_branch_no_master(self):
        """Check that the parent repository is not on master branch"""
        folder = self.user_buildout_repo.working_tree_dir
        release = ReleaseDistribution(folder)

        self.user_buildout_repo.create_head('another-branch')
        self.user_buildout_repo.heads['another-branch'].checkout()

        with OutputCapture():
            with wrap_folder(folder):
                self.assertRaises(
                    ValueError,
                    release._check_parent_branch
                )

        self.assertEqual(
            self.user_buildout_repo.active_branch.name,
            'another-branch'
        )

    def test_check_distribution_does_not_exists(self):
        """Check that if a distribution does not exist it raises an error"""
        folder = self.user_buildout_repo.working_tree_dir
        release = ReleaseDistribution('{0}/lala'.format(folder))

        self.assertRaises(
            IOError,
            release._check_distribution_exists
        )

    def test_check_distribution_exists(self):
        """Check that the parent repository is not on master branch"""
        folder = self.user_buildout_repo.working_tree_dir
        release = ReleaseDistribution(folder)

        release._check_distribution_exists()

        self.assertTrue(
            os.path.exists(folder)
        )

    def test_get_version(self):
        """Check that the latest tag is returned"""
        folder = self.user_buildout_repo.working_tree_dir
        release = ReleaseDistribution(folder)

        self._commit(self.user_buildout_repo)
        self.user_buildout_repo.create_tag('first-tag')

        self._commit(self.user_buildout_repo)
        self.user_buildout_repo.create_tag('last-tag')

        self.assertEqual(
            release.get_version(),
            'last-tag'
        )
