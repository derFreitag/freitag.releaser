# CHANGES

<!-- towncrier release notes start -->

## 4.0.3 (2025-04-30)


### Bug fixes

- Do not push to servers some outdated cfg files @gforcada 

## 4.0.2 (2025-02-26)


### Bug fixes

- re-release @gforcada 

## 4.0.1 (2025-02-26)


### Bug fixes

- do not add the CI skip mark on commits @gforcada 
- overhaul configuration to use something close to `plone.meta` @gforcada 

## 4.0.1 (2025-01-17)

### Bug fixes:

- replace `push_url` by `pushurl` as plone.releaser changed it @gforcada

## 4.0.0 (2024-10-01)

- Remove the `assets` command, it's no longer useful @gforcada

## 3.1.0 (2024-09-30)

- Allow releases from `main` branch @gforcada

- Be more flexible with news snippets file names @gforcada

## 3.0.0 (2024-03-05)

- Use implicit namespaces @gforcada

## 2.0.2 (2024-02-15)

- Drop unneeded `plone.recipe.codeanalysis` dependency @gforcada

## 2.0.1 (2023-12-28)

- Handle a few more towncrier suffixes @gforcada

## 2.0.0 (2022-09-27)

- Lots of changes: cleanups, enhancements, etc @gforcada

## 1.0.post0 (2015-11-24)

- Minor cleanup, 1.0 release was half broken @gforcada

## 1.0 (2015-11-24)

- Only show the meaningful commits @gforcada

- Remove develop branch support. This massively simplifies all the code @gforcada

- Allow to release only some packages.
  See `-f` option on full-release command @gforcada

- Push cfg files when doing a full release @gforcada

- Test nearly everything @gforcada

- Fix coverage and speed up travis @gforcada

- Add more utility functions @gforcada

- Add debug option to all commands,
  use python logging module to log information at various levels @gforcada

- Avoid cloning repositories (speed ups everything) @gforcada

## 0.7.1 (2015-11-16)

- Clone a pushable repository @gforcada

- Update the local branches after release @gforcada

- Filter distributions to release @gforcada

## 0.7 (2015-11-16)

- Lots of minor fixes here and there,
  too small and too many of them to list here @gforcada

## 0.6.3 (2015-11-13)

- Adapt `git_repo` context manager from `plone.releaser` @gforcada

- Adjust verbosity @gforcada

## 0.6.2 (2015-11-13)

- More verbose and more string formatting fixes @gforcada

- Check that a distribution has a source defined on buildout before trying
  to clone it @gforcada

## 0.6.1 (2015-11-13)

- Be more verbose, so one know about which distribution the output is about @gforcada

- Fix two strings that were not formatted @gforcada

## 0.6 (2015-11-13)

- Add dry-run mode to `fullrelease` command @gforcada

## 0.5 (2015-11-13)

- Add update distribution `CHANGES.rst`  @gforcada

## 0.4 (2015-11-13)

- Add gather changelog command @gforcada

## 0.3 (2015-11-13)

- Cleanups and code reorganization @gforcada

- Add full-release command @gforcada

## 0.2 (2015-11-11)

- 0.1 was never released, due to not being registered on PyPI @gforcada

## 0.1 (2015-11-11)

- add `zest.releaser` plugins:

  - `vcs_updated`: checkouts master and develop branches,
    rebases the former on top of the later (master catches up with develop)
    and leaves the checked out branch as master,
    ready to be released
  - `i18n`: runs `bin/i18ndude find-untranslated` and reports back if there
    are any strings not marked for translation
  - `update_branches`: the opposite from vcs_updated,
    rebased develop branch on top of master (which was used to make the release)

  @gforcada

- emulate `plone.releaser` and create a `freitag_manage` command with:

  - publish_cfg_files: send two specific files to a specific server
  - release: releases a distribution (with `zest.releaser`)

  @gforcada

- initial release @gforcada
