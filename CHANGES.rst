* a0ac894 test: ReleaseDistribution
* 4fc5b74 test: ReleaseDistribution.__init__
* 791e8e4 test: FullRelease._create_commit_message
* 87f81c0 test: add more CHANGES.rst
* 933d66e test: FullRelease.filter_distros
* 1fa3e43 test: FullRelease.ask_what_to_release
* 56f8f18 Another todo -> nice to have
* 834afeb By no means that's a TODO
* e1c67f5 test: FullRelease.check_changes_to_be_released
* 02aa48c test: more pending_local_changes test
* a153836 Use sys.exit
* 4e4270e Initial test for FullRelease
*   82405b5 Merge pull request #1 from derFreitag/fix-coverage
|\  
| * 7755847 Really fix coverage
|/  
* 0106bda Ignore (coverage) buildout cache folder
* a6bea9a Speed up travis builds
* 3fef130 More coverage fixes for coveralls
* c4bb1de More coverage fixes for coveralls
* 2e99bb2 Fix coveralls report
* ec907aa Add .coveragerc
* d5a0315 Do not shadwo a built-in name (filter)
* c6991cd Fix coveralls
* 73daf7b Python 3.x fails due to plone.releaser
* 5bddce8 Revert "Remove coverage"
* 28e7f5e Remove unused method
* 88e2351 test: f.r.changelog.UpdateDistChangelog
* 2b5f159 test: f.r.utils.wrap_sys_argv
* 665973b test: f.r.utils.wrap_folder
* 22d41b1 test: f.r.utils.git_repo
* cd5f072 test: f.r.utils.get_compact_git_history
* ba6781a test: f.r.utils.is_branch_synced
* d79f1d5 test: f.r.utils.update_branch
* e0f1987 push cfg files and zope repository
* c4aacb2 Store the commit message
* a067ae8 Push cfg files when doing a full release
* c9b996d Move publish cfg files logic into utils.py
* 0cb5fab Allow to release only some packages
* 6a9b9e7 cleaned_git_changes does not have new lines
* 387abd1 As the loop for the branches is gone, so has the break statement
* 282b1f4 Create context managers and move them to utils.py
* 238a434 Leftover
* b8dd66a No develop branch, it's all too simple
* 5701284 No develop branch no prerelease step needed
* 20cae4d No develop branch
* f36738f No develop branch no postrelease step needed
* 0b72d16 Correctly enable the distribution
* 337a29f Only show the meaningful commits
* 453c70a Missed a comma
* 9200c86 Back to development: 0.7.2
* 0b2a53b Preparing release 0.7.1

.. -*- coding: utf-8 -*-

Changelog
=========

0.7.2 (unreleased)
------------------

- Nothing changed yet.


0.7.1 (2015-11-16)
------------------
- Clone a pushable repository.
  [gforcada]

- Update the local branches after release.
  [gforcada]

- Filter distributions to release.
  [gforcada]

0.7 (2015-11-16)
----------------

- Lots of minor fixes here and there,
  too small and too many of them to list here.
  [gforcada]

0.6.3 (2015-11-13)
------------------

- Adapt git_repo context manager from plone.releaser.
  [gforcada]

- Adjust verbosity.
  [gforcada]

0.6.2 (2015-11-13)
------------------

- More verbose and more string formatting fixes.
  [gforcada]

- Check that a distribution has a source defined on buildout before trying
  to clone it.
  [gforcada]

0.6.1 (2015-11-13)
------------------

- Be more verbose, so one know about which distribution the output is about.
  [gforcada]

- Fix two strings that were not formatted.
  [gforcada]

0.6 (2015-11-13)
----------------

- Add dry-run mode to fullrelease command.
  [gforcada]

0.5 (2015-11-13)
----------------

- Add update distribution ``CHANGES.rst``.
  [gforcada]

0.4 (2015-11-13)
----------------

- Add gather changelog command.
  [gforcada]

0.3 (2015-11-13)
----------------

- Cleanups and code reorganization.
  [gforcada]

- Add full-release command.
  [gforcada]

0.2 (2015-11-11)
----------------

- 0.1 was never released, due to not being registered on PyPI.
  [gforcada]

0.1 (2015-11-11)
----------------
- add zest.releaser plugins:

  - vcs_updated: checkouts master and develop branches,
    rebases the former on top of the later (master catches up with develop)
    and leaves the checked out branch as master,
    ready to be released
  - i18n: runs ``bin/i18ndude find-untranslated`` and reports back if there
    are any strings not marked for translation
  - update_branches: the oposite from vcs_updated,
    rebased develop branch on top of master (which was used to make the release)

  [gforcada]

- emulate ``plone.releaser`` and create a ``freitag_manage`` command with:

  - publish_cfg_files: send two specific files to a specific server
  - release: releases a distribution (with ``zest.releaser``)

  [gforcada]

- initial release
  [gforcada]
