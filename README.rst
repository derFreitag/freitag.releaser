.. -*- coding: utf-8 -*-

.. image:: https://travis-ci.org/derFreitag/freitag.releaser.svg?branch=master
   :target: https://travis-ci.org/derFreitag/freitag.releaser

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
- check translation files are updated *check_translations*

Additions to plone.releaser:

- **(TODO)**: ability to release a distribution within the parent (buildout) project

  - check to ensure the correct branch on the parent project is used *check_zope_branch*
  - check that the distribution about to release exists *check_folders*
  - update versions.cfg with the new released version *update_versions_cfg*

- **(TODO)**: create a new release of the parent project *create_new_buildout_release*
- **(TODO)**: gather the changes on distributions (more than only *collect_changelog*)
- push cfg files *publish_cfg_files*
- **(TODO)**: update batou version pins (components/{plone,zeo}/versions/versions.cfg
- **(TODO)**: check which distributions need a release
- **(TODO)**: add git changelog to CHANGES.rst


.. _`der Freitag`: https://www.freitag.de
.. _`plone.releaser`: https://pypi.python.org/pypi/plone.releaser
.. _`zest.releaser`: https://pypi.python.org/pypi/zest.releaser
