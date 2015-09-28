# -*- coding: utf-8 -*-
from git import InvalidGitRepositoryError
from git import Repo
from zest.releaser.utils import ask


def update_branches(data):
    """update_develop_branches"""
    try:
        repo = Repo(data['workingdir'])
    except InvalidGitRepositoryError:
        return

    branch = 'develop'
    if branch not in repo.heads:
        return

    if not ask('Do you want to update develop branch with changes in master?'):
        return

    develop_branch = repo.heads.develop
    remote = repo.remote()

    develop_branch.checkout()
    repo.git.rebase(remote.refs.master.path)
    remote.push('develop:refs/heads/develop')
