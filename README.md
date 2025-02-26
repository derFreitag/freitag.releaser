# freitag.releaser

Release facilities to ease the management of buildout based projects.

## Standing on the shoulder of giants

This distribution intends to be as small as possible
by integrating a few custom release choices done by the [der Freitag](https://www.freitag.de) development team.

For that it heavily relies on a couple of well known distributions:

- [`plone.releaser`](https://pypi.python.org/pypi/plone.releaser)
- [`zest.releaser`](https://pypi.python.org/pypi/zest.releaser)

## What's in?

A few `zest.releaser` plugins that:

- check that the git repository is updated *update_git_branch*
- update development branches after a release *update_develop_branches*
- check translation files are updated *check_translations*

Additions to `plone.releaser`:

- ability to release a distribution within the parent (buildout) project

  - check to ensure the correct branch on the parent project is used *check_zope_branch*
  - check that the distribution about to release exists *check_folders*
  - update versions.cfg with the new released version *update_versions_cfg*

- gather the changes on distributions (more than only *collect_changelog*)
- push cfg files *publish_cfg_files*
- check which distributions need a release
- update batou version pins (components/plone/versions/versions.cfg)
