.. -*- coding: utf-8 -*-

.. image:: https://travis-ci.org/derFreitag/freitag.releaser.svg?branch=master
   :target: https://travis-ci.org/derFreitag/freitag.releaser

.. image:: https://coveralls.io/repos/derFreitag/freitag.releaser/badge.svg?branch=master&service=github
   :target: https://coveralls.io/github/derFreitag/freitag.releaser?branch=master

================
freitag.releaser
================
Release facilities to ease the management of buildout based projects.

Standing on the shoulder of giants
==================================
This distribution intends to be as small as possible by integrating a few custom release choices done by the `der Freitag`_ development team.

For that it heavily relies on a couple of well known distributions:

- `plone.releaser`_
- `zest.releaser`_

What's in?
==========
A few zest.releaser plugins that:

- check that the git repository is updated *update_git_branch*
- update development branches after a release *update_develop_branches*
- **(TODO)**: check translation files are updated *check_translations*
- **(TODO)**: check that a new release is actually needed *check_current_versions*
- **(TODO)**: check that the next release version number is higher *check_new_version*
- **(TODO)**: check that the changelog is not empty *check_changelog*
- **(TODO)**: update setup.py and CHANGES.rst *update_versions*
- **(TODO)**: create egg and upload it to private pypi *create_new_eggs*
- **(TODO)**: push commits and tags *push_git_repository*
- (TODO):

Additions to plone.releaser:

- **(TODO)**: ability to release a distribution within the parent (buildout) project
- **(TODO)**: pre-check to ensure the correct branch on the parent project is used *check_zope_branch*
- **(TODO)**: check that the distribution about to release exists *check_folders*
- **(TODO)**: check that release exists on versions.cfg *check_versions_cfg*
- **(TODO)**: update versions.cfg with the new released version *update_versions_cfg*
- **(TODO)**: create a new release of the parent project *create_new_buildout_release*
- **(TODO)**: gather the changes on distributions (more than only *collect_changelog*)
- **(TODO)**: push cfg files *publish_cfg_files*
- (TODO):

.. _`der Freitag`: https://www.freitag.de
.. _`plone.releaser`: https://pypi.python.org/pypi/plone.releaser
.. _`zest.releaser`: https://pypi.python.org/pypi/zest.releaser
