# -*- coding: utf-8 -*-


def update_branch(repo, branch):
    remote = repo.remote()
    repo.heads[branch].checkout()
    local_commit = repo.head.commit
    remote_commit = remote.refs[branch].commit
    if local_commit != remote_commit:
        repo.git.rebase('origin/{0}'.format(branch))


def is_everything_pushed(repo):
    """Check if the branches on the given repository have local commits

    :param repo: the repository that will be used to check the branches
    :type repo: git.Repo
    """
    branch = 'master'
    # get new code, if any
    remote = repo.remote()
    remote.fetch()

    try:
        local_branch = repo.refs[branch]
    except IndexError:
        print('master branch does not exist locally')
        # no problem then, all commits are pushed
        return True

    try:
        remote_branch = remote.refs[branch]
    except IndexError:
        print('master branch does not exist remotely')
        # it's pointless to check if a branch has local commits if it does
        # not exist remotely
        return False

    local_commit = local_branch.commit.hexsha
    remote_commit = remote_branch.commit.hexsha

    if local_commit != remote_commit:
        return False

    return True


def get_compact_git_history(repo, tag):
    return repo.git.log(
        '--oneline',
        '--graph',
        '{0}~1..master'.format(tag)
    )
