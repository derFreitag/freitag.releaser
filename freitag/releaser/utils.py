# -*- coding: utf-8 -*-


def update_repo(repo):
    # get new code, if any
    remote = repo.remote()
    remote.fetch()

    branch = 'develop'
    if branch in remote.refs:
        # the branch does not exist locally, check it out
        if branch not in repo.heads:
            create_branch_locally(repo, branch)
        else:
            update_branch(repo, branch)

    branch = 'master'
    if branch in remote.refs:
        # the branch does not exist locally, check it out
        if branch not in repo.heads:
            create_branch_locally(repo, branch)
        else:
            update_branch(repo, branch)

        if 'develop' in repo.heads:
            # add all commits from develop to master
            develop_commit = repo.branches.develop.commit
            master_commit = repo.branches.master.commit
            if develop_commit == master_commit:
                print('master branch is already in sync with develop branch.')
            else:
                repo.git.rebase('origin/develop')
                print('Rebased master branch on top of develop.')


def create_branch_locally(repo, branch):
    remote = repo.remote()
    new_branch = repo.create_head(branch, remote.refs[branch])
    new_branch.set_tracking_branch(remote.refs[branch])
    print('{0} branch did not exist locally, checked out.'.format(branch))


def update_branch(repo, branch):
    # update develop branch to its latest commit
    remote = repo.remote()
    repo.heads[branch].checkout()
    local_commit = repo.head.commit
    remote_commit = remote.refs[branch].commit
    if local_commit == remote_commit:
        print('{0} branch is already updated.'.format(branch))
    else:
        repo.git.rebase('origin/{0}'.format(branch))
        print('Updated {0} branch to latest commits.'.format(branch))


def is_everything_pushed(repo, branches=()):
    """Check if the branches on the given repository have local commits

    :param repo: the repository that will be used to check the branches
    :type repo: git.Repo
    :param branches: the branches that will be checked to see if they have
      unpushed commits
    :type branches: tuple
    """
    # get new code, if any
    remote = repo.remote()
    remote.fetch()

    for branch in branches:
        try:
            local_branch = repo.refs[branch]
        except IndexError:
            print('{0} branch does not exist locally'.format(branch))
            # no problem then, all commits are pushed
            continue

        try:
            remote_branch = remote.refs[branch]
        except IndexError:
            print('{0} branch does not exist remotely'.format(branch))
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
