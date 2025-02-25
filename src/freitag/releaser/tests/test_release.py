from freitag.releaser.release import FullRelease
from freitag.releaser.release import ReleaseDistribution
from freitag.releaser.utils import is_branch_synced
from freitag.releaser.utils import wrap_folder
from git import Repo
from tempfile import mkdtemp
from testfixtures import LogCapture
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
            msg='First commit',
        )
        self.remote_buildout_repo.create_head('main')
        self.remote_buildout_repo.remote().push('main:refs/heads/main')

        self.user_buildout_repo = self.buildout_repo.clone(mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.buildout_repo.working_dir)
        shutil.rmtree(self.remote_buildout_repo.working_dir)
        shutil.rmtree(self.user_buildout_repo.working_dir)

    def _commit(self, repo, content='', filename='dummy', msg='Random commit'):
        dummy_file = os.path.join(repo.working_tree_dir, filename)
        with open(dummy_file, 'w') as a_file:
            a_file.write(content)
        repo.index.add([dummy_file])
        repo.index.commit(msg)

        return repo.commit().hexsha

    def _add_source(self, repo):
        source_line = f'my.distribution = git file://{repo.working_tree_dir}'
        self._commit(
            repo,
            content=BUILDOUT_FILE_CONTENTS.format(source_line),
            filename='develop.cfg',
            msg='Add source',
        )

    def _add_changes(self, repo):
        self._commit(
            self.user_buildout_repo,
            content=CHANGES,
            filename='CHANGES.rst',
            msg='Update changes',
        )

    def _get_logging_as_string(self, output):
        messages = [f.getMessage() for f in output.records]
        return '\n'.join(messages)


class TestFullRelease(BaseTest):
    def test_create_instance(self):
        """Check that the values passed on creation are safed"""
        path = '/tmp/la/li/somewhere'
        test = True
        dist_filter = 'some random filter'

        full_release = FullRelease(
            path=path, test=test, filter_distributions=dist_filter
        )
        self.assertEqual(full_release.path, path)
        self.assertEqual(full_release.test, test)
        self.assertEqual(full_release.filters, dist_filter)

    def test_get_all_distributions_folder(self):
        """Check that a folder is not considered a distribution"""
        path = f'{self.user_buildout_repo.working_tree_dir}/src'
        # create a folder
        os.makedirs(f'{path}/folder-not-repo')

        full_release = FullRelease(path=path)

        with OutputCapture():
            full_release.get_all_distributions()

        self.assertEqual(full_release.distributions, [])

    def test_get_all_distributions_file(self):
        """Check that a file is not considered a distribution"""
        path = f'{self.user_buildout_repo.working_tree_dir}/src'
        # create a file
        os.makedirs(path)
        with open(f'{path}/random-file', 'w') as a_file:
            a_file.write('something')

        full_release = FullRelease(path=path)

        with OutputCapture():
            full_release.get_all_distributions()

        self.assertEqual(full_release.distributions, [])

    def test_get_all_distributions_repo(self):
        """Check that a git repository is considered a distribution"""
        path = f'{self.user_buildout_repo.working_tree_dir}/src'
        os.makedirs(path)
        repo_folder = f'{path}/my.distribution'
        repo1 = self.buildout_repo.clone(repo_folder)
        repo_folder = f'{path}/my.distribution2'
        repo2 = self.buildout_repo.clone(repo_folder)

        full_release = FullRelease(path=path)

        with OutputCapture():
            full_release.get_all_distributions()

        self.assertEqual(
            full_release.distributions, [repo1.working_tree_dir, repo2.working_tree_dir]
        )

    def test_filter_distros_no_filter(self):
        """Check that if no filter is applied all distributions are used"""
        full_release = FullRelease()
        full_release.distributions = ['one', 'two', 'three']
        with OutputCapture():
            full_release.filter_distros()

        self.assertEqual(
            full_release.distributions,
            ['one', 'two', 'three'],
        )

    def test_filter_distros_filter(self):
        """Check that if a filter is applied only the matching distributions
        are kept
        """
        full_release = FullRelease(filter_distributions='w')
        full_release.distributions = ['one', 'two', 'three']
        with OutputCapture():
            full_release.filter_distros()

        self.assertEqual(
            full_release.distributions,
            ['two'],
        )

    def test_filter_multiple_filters(self):
        """Check that if multiple filters are passed they are correctly used"""
        full_release = FullRelease(filter_distributions=['w', 'h'])
        full_release.distributions = ['one', 'two', 'three']
        with OutputCapture():
            full_release.filter_distros()

        self.assertEqual(full_release.distributions, ['three', 'two'])

    def test_check_pending_local_changes_dirty(self):
        """Check that a repository with local changes (uncommitted) is removed
        from the list of distributions to be released
        """
        # create repo
        path = f'{self.user_buildout_repo.working_tree_dir}/src'
        os.makedirs(path)
        repo_folder = f'{path}/my.distribution'
        repo = self.buildout_repo.clone(repo_folder)

        # add a file
        file_path = f'{repo_folder}/tmp_file'
        with open(file_path, 'w') as a_file:
            a_file.write('something')
            repo.index.add([file_path])

        # full release
        full_release = FullRelease(path=path)
        full_release.distributions = [repo_folder]

        utils.test_answer_book.set_answers(['Y'])
        with OutputCapture():
            full_release.check_pending_local_changes()

        # check the distribution is removed
        self.assertEqual(full_release.distributions, [])

    def test_check_pending_local_changes_unpushed(self):
        """Check that a repository with local commits is removed from the list
        of distributions to be released
        """
        # create repo
        path = f'{self.user_buildout_repo.working_tree_dir}/src'
        os.makedirs(path)
        repo_folder = f'{path}/my.distribution'
        repo = self.buildout_repo.clone(repo_folder)

        # make a commit on the repo
        self._commit(repo)

        # full release
        full_release = FullRelease(path=path)
        full_release.distributions = [repo_folder]

        utils.test_answer_book.set_answers(['Y'])
        with OutputCapture():
            full_release.check_pending_local_changes()

        # check the distribution is removed
        self.assertEqual(full_release.distributions, [])

    def test_check_pending_local_changes_exit(self):
        """Check that if a repository has local commits you are given the
        option to quit.
        """
        # create repo
        path = f'{self.user_buildout_repo.working_tree_dir}/src'
        os.makedirs(path)
        repo_folder = f'{path}/my.distribution'
        repo = self.buildout_repo.clone(repo_folder)

        # make a commit on the repo
        self._commit(repo)

        # full release
        full_release = FullRelease(path=path)
        full_release.distributions = [repo_folder]

        utils.test_answer_book.set_answers(['n'])
        with OutputCapture():
            self.assertRaises(SystemExit, full_release.check_pending_local_changes)

    def test_check_pending_local_changes_unpushed_test(self):
        """Check that a repository with local commits is *not* removed from
        the list of distributions to be released if test is True
        """
        # create repo
        path = f'{self.user_buildout_repo.working_tree_dir}/src'
        os.makedirs(path)
        repo_folder = f'{path}/my.distribution'
        repo = self.buildout_repo.clone(repo_folder)

        # make a commit on the repo
        self._commit(repo)

        # full release
        full_release = FullRelease(path=path, test=True)
        full_release.distributions = [repo_folder]

        with OutputCapture():
            full_release.check_pending_local_changes()

        # check the distribution is not removed
        self.assertEqual(
            full_release.distributions,
            [repo_folder],
        )

    def test_check_pending_local_changes_clean(self):
        """Check that a clean repository is not removed from the list of
        distributions to be released
        """
        # create repo
        path = f'{self.user_buildout_repo.working_tree_dir}/src'
        os.makedirs(path)
        repo_folder = f'{path}/my.distribution'
        self.buildout_repo.clone(repo_folder)

        # full release
        full_release = FullRelease(path=path)
        full_release.distributions = [repo_folder]

        utils.test_answer_book.set_answers(['Y'])
        with OutputCapture():
            full_release.check_pending_local_changes()

        # check the distribution is not removed
        self.assertEqual(
            full_release.distributions,
            [repo_folder],
        )

    def test_changes_to_be_released_no_tag(self):
        """Check that if a distribution does not have any tag is kept as a
        distribution that needs to be released
        """
        # create repo
        path = f'{self.user_buildout_repo.working_tree_dir}/src'
        os.makedirs(path)
        repo_folder = f'{path}/my.distribution'
        repo = self.buildout_repo.clone(repo_folder)

        # create some commits
        self._commit(repo)
        self._commit(repo)
        repo.remote().push()

        # full release
        full_release = FullRelease(path=path)
        full_release.distributions = [repo_folder]

        # run check_changes_to_be_released
        with OutputCapture():
            full_release.check_changes_to_be_released()

        # check that the distribution is still there
        self.assertEqual(full_release.distributions, [repo_folder])

    def test_changes_to_be_released_nothing_to_release(self):
        """Check that if there is a tag on the last commit the distribution is
        removed from the list of distributions needing a release
        """
        # create repo
        path = f'{self.user_buildout_repo.working_tree_dir}/src'
        os.makedirs(path)
        repo_folder = f'{path}/my.distribution'
        repo = self.buildout_repo.clone(repo_folder)

        # create a tag
        repo.create_tag('my-tag')

        # full release
        full_release = FullRelease(path=path)
        full_release.distributions = [repo_folder]

        # run check_changes_to_be_released
        with OutputCapture():
            full_release.check_changes_to_be_released()

        # check that the distribution is still there
        self.assertEqual(full_release.distributions, [])

    def test_changes_to_be_released_commits_to_release(self):
        """Check that if there is a tag on the last commit the distribution is
        removed from the list of distributions needing a release
        """
        # create repo
        path = f'{self.user_buildout_repo.working_tree_dir}/src'
        os.makedirs(path)
        repo_folder = f'{path}/my.distribution'
        repo = self.buildout_repo.clone(repo_folder)

        # create a tag
        repo.create_tag('my-tag')

        # create a commit
        self._commit(repo)
        repo.remote().push()

        # full release
        full_release = FullRelease(path=path)
        full_release.distributions = [repo_folder]

        # run check_changes_to_be_released
        with OutputCapture():
            full_release.check_changes_to_be_released()

        # check that the distribution is still there
        self.assertEqual(full_release.distributions, [repo_folder])

    def test_changes_to_be_released_test(self):
        """Check that if the distribution was supposed to be removed, it is not
        if test is True
        """
        # create repo
        path = f'{self.user_buildout_repo.working_tree_dir}/src'
        os.makedirs(path)
        repo_folder = f'{path}/my.distribution'
        repo = self.buildout_repo.clone(repo_folder)

        # create a tag
        repo.create_tag('my-tag')

        # full release
        full_release = FullRelease(path=path, test=True)
        full_release.distributions = [repo_folder]

        # run check_changes_to_be_released
        with OutputCapture():
            full_release.check_changes_to_be_released()

        # check that the distribution is still there
        self.assertEqual(
            full_release.distributions,
            [repo_folder],
        )

    def test_changes_to_be_released_last_tags_filled(self):
        """Check that if the distribution has a tag is stored on last_tags dict"""
        # create repo
        path = f'{self.user_buildout_repo.working_tree_dir}/src'
        os.makedirs(path)
        repo_folder = f'{path}/my.distribution'
        repo = self.buildout_repo.clone(repo_folder)

        # create a tag
        repo.create_tag('my-tag')

        # full release
        full_release = FullRelease(path=path)
        full_release.distributions = [repo_folder]

        # run check_changes_to_be_released
        with OutputCapture():
            full_release.check_changes_to_be_released()

        # check that the tag has been saved on the dictionary
        self.assertEqual(full_release.last_tags['my.distribution'], 'my-tag')

    def test_changes_to_be_released_last_tags_no_tag(self):
        """Check that if the distribution does not have a tag the latest
        commit is stored on last_tags dict
        """
        # create repo
        path = f'{self.user_buildout_repo.working_tree_dir}/src'
        os.makedirs(path)
        repo_folder = f'{path}/my.distribution'
        repo = self.buildout_repo.clone(repo_folder)

        # create some commits
        self._commit(repo)
        self._commit(repo)
        repo.remote().push()

        # full release
        full_release = FullRelease(path=path)
        full_release.distributions = [repo_folder]

        # run check_changes_to_be_released
        with OutputCapture():
            full_release.check_changes_to_be_released()

        # check that the distribution key has been created
        self.assertIn('my.distribution', full_release.last_tags)

        # check that what's stored is the hexsha of a commit
        commit = [
            c
            for c in repo.iter_commits()
            if c.hexsha == full_release.last_tags['my.distribution']
        ]
        self.assertEqual(len(commit), 1)

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
        path = f'{self.user_buildout_repo.working_tree_dir}/src'
        os.makedirs(path)
        repo_folder = f'{path}/my.distribution'
        self.buildout_repo.clone(repo_folder)

        # full release
        full_release = FullRelease(path=path)
        full_release.distributions = [repo_folder]
        full_release.last_tags['my.distribution'] = first_commit_sha

        utils.test_answer_book.set_answers(['Y'])
        with wrap_folder(self.user_buildout_repo.working_tree_dir):
            with OutputCapture():
                with LogCapture() as output:
                    full_release.ask_what_to_release()

        self.assertIn('Random commit 2', self._get_logging_as_string(output))

        self.assertNotIn('Bump version', self._get_logging_as_string(output))

        self.assertIn('Add source', self._get_logging_as_string(output))

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
        path = f'{self.user_buildout_repo.working_tree_dir}/src'
        os.makedirs(path)
        repo_folder = f'{path}/my.distribution'
        self.buildout_repo.clone(repo_folder)

        # full release
        full_release = FullRelease(path=path)
        full_release.distributions = [repo_folder]
        full_release.last_tags['my.distribution'] = first_commit_sha

        with wrap_folder(self.user_buildout_repo.working_tree_dir):
            with OutputCapture():
                full_release.ask_what_to_release()

        # check that the distribution is not going to be released
        self.assertEqual(full_release.distributions, [])

    def test_ask_what_to_release_test(self):
        """Check that in test mode no distributions are filtered"""
        repo = self.user_buildout_repo

        # add source, CHANGES.rst, commits and push the repo
        self._add_source(repo)
        self._add_changes(repo)
        first_commit_sha = self._commit(repo, msg='Random commit 1')
        self.user_buildout_repo.remote().push()

        # clone the repo
        path = f'{self.user_buildout_repo.working_tree_dir}/src'
        os.makedirs(path)
        repo_folder = f'{path}/my.distribution'
        self.buildout_repo.clone(repo_folder)

        # full release
        full_release = FullRelease(path=path, test=True)
        full_release.distributions = [
            repo_folder,
        ]
        full_release.last_tags['my.distribution'] = first_commit_sha

        utils.test_answer_book.set_answers(['n'])
        with wrap_folder(self.user_buildout_repo.working_tree_dir):
            with OutputCapture():
                full_release.ask_what_to_release()

        self.assertEqual(
            full_release.distributions,
            [repo_folder],
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
        path = f'{self.user_buildout_repo.working_tree_dir}/src'
        os.makedirs(path)
        repo_folder = f'{path}/my.distribution'
        self.buildout_repo.clone(repo_folder)

        # full release
        full_release = FullRelease(path=path)
        full_release.distributions = [repo_folder]
        full_release.last_tags['my.distribution'] = first_commit_sha

        utils.test_answer_book.set_answers(['n'])
        with wrap_folder(self.user_buildout_repo.working_tree_dir):
            with OutputCapture() as output:
                full_release.ask_what_to_release()

        self.assertEqual(full_release.distributions, [])
        self.assertIn(
            'Is the change log for my.distribution ready for release?', output.captured
        )

    def test_update_buildout(self):
        """Check that repository is updated with commit message"""
        path = self.user_buildout_repo.working_tree_dir

        message = 'New versions: 345'

        with wrap_folder(path):
            with open('versions.cfg', 'w') as versions:
                versions.write('[versions]')

            full_release = FullRelease()
            full_release.commit_message = message
            full_release.update_buildout()

        commit = self.user_buildout_repo.commit()
        self.assertEqual(commit.message.strip(), message)
        self.assertTrue(is_branch_synced(self.user_buildout_repo))

    def test_create_commit_message(self):
        """Check that the commit message is generated correctly"""
        full_release = FullRelease()
        full_release.versions['my.distribution'] = '3.4.5'
        full_release.versions['my.other'] = '5.4.3'
        full_release.versions['last.one'] = '1.2'

        full_release.changelogs['my.distribution'] = '\n'.join(
            [
                '- one change',
                '  [gforcada]',
                '',
                '- second change',
                '  [someone else]' '',
            ]
        )
        full_release.changelogs['my.other'] = '\n'.join(
            [
                '- third change',
                '  [gforcada]',
                '',
                '- related one',
                '  [someone else]' '',
            ]
        )
        full_release.changelogs['last.one'] = '\n'.join(
            [
                '- one more change',
                '  [gforcada]',
                '',
                '- really last change',
                '  [someone else]' '',
            ]
        )

        self.assertEqual(full_release.commit_message, '')

        full_release._create_commit_message()

        self.assertIn(
            '\n'.join(
                [
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
                ]
            ),
            full_release.commit_message,
        )

    def test_update_batou(self):
        """Check that batou repository is updated with new version pins"""
        buildout_path = self.user_buildout_repo.working_tree_dir

        # create the fake batou repository
        remote_batou = Repo.init(mkdtemp(), bare=True)

        # clone the fake batou repository and add the versions.cfg
        tmp_batou_repo = remote_batou.clone(mkdtemp())
        folder_path = '{0}/components/plone/versions'
        folder_path = folder_path.format(tmp_batou_repo.working_tree_dir)
        os.makedirs(folder_path)
        file_path = f'{folder_path}/versions.cfg'
        with open(file_path, 'w') as versions:
            versions.write('[versions]')
        tmp_batou_repo.index.add([file_path])
        tmp_batou_repo.index.commit('lalala')
        tmp_batou_repo.create_head('main')
        tmp_batou_repo.remote().push('main:refs/heads/main')

        shutil.rmtree(tmp_batou_repo.working_dir)

        with wrap_folder(buildout_path):
            with open('sources.cfg', 'w') as versions:
                versions.write('[sources]\n')
                versions.write(f'deployment = git file://{remote_batou.working_dir}')

            full_release = FullRelease()
            full_release.commit_message = 'lalala'
            full_release.versions = {
                'der.freitag': '4.3',
                'freitag.article': '2.7',
            }
            full_release.update_batou()

        tmp_batou_repo = remote_batou.clone(mkdtemp())
        branch = tmp_batou_repo.branches['main']

        self.assertEqual(branch.commit.message, 'lalala')
        self.assertEqual(len(branch.commit.stats.files.keys()), 1)
        self.assertEqual(
            list(branch.commit.stats.files.keys())[0],
            'components/plone/versions/versions.cfg',
        )

        with wrap_folder(tmp_batou_repo.working_tree_dir):
            with open('components/plone/versions/versions.cfg') as a_file:
                data = a_file.read()

        self.assertIn('der.freitag = 4.3', data)
        self.assertIn('freitag.article = 2.7', data)

        shutil.rmtree(remote_batou.working_dir)
        shutil.rmtree(tmp_batou_repo.working_tree_dir)


class TestReleaseDistribution(BaseTest):
    def test_create_instance(self):
        """Check that path and name are set properly"""
        release = ReleaseDistribution('some/random/path')
        self.assertEqual(release.path, 'some/random/path')
        self.assertEqual(release.name, 'path')

    def test_check_distribution_does_not_exists(self):
        """Check that if a distribution does not exist it raises an error"""
        folder = self.user_buildout_repo.working_tree_dir
        release = ReleaseDistribution(f'{folder}/lala')

        self.assertRaises(IOError, release._check_distribution_exists)

    def test_check_distribution_exists(self):
        """Check that the parent repository is not on master branch"""
        folder = self.user_buildout_repo.working_tree_dir
        release = ReleaseDistribution(folder)

        release._check_distribution_exists()

        self.assertTrue(os.path.exists(folder))

    def test_get_version(self):
        """Check that the latest tag is returned"""
        folder = self.user_buildout_repo.working_tree_dir
        release = ReleaseDistribution(folder)

        self._commit(self.user_buildout_repo)
        self.user_buildout_repo.create_tag('4.9')

        self._commit(self.user_buildout_repo)
        self.user_buildout_repo.create_tag('4.11')

        self.assertEqual(release.get_version(), '4.11')
