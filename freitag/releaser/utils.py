# -*- coding: utf-8 -*-


def update_repo(repo):
    # get new code, if any
    remote = repo.remote()
    remote.fetch()

    branch = 'develop'
    if branch in remote.refs:
        # the branch does not exist locally, check it out
        if branch not in repo.heads:
            _checkout_branch(repo, branch)
        else:
            _update_branch(repo, branch)

    branch = 'master'
    if branch in remote.refs:
        # the branch does not exist locally, check it out
        if branch not in repo.heads:
            _checkout_branch(repo, branch)
        else:
            _update_branch(repo, branch)

        if 'develop' in repo.heads:
            # add all commits from develop to master
            develop_commit = repo.branches.develop.commit
            master_commit = repo.branches.master.commit
            if develop_commit == master_commit:
                print('master branch is already in sync with develop branch.')
            else:
                repo.git.rebase('origin/develop')
                print('Rebased master branch on top of develop.')


def _checkout_branch(repo, branch):
    remote = repo.remote()
    new_branch = repo.create_head(branch, remote.refs[branch])
    new_branch.set_tracking_branch(remote.refs[branch])
    print('{0} branch did not exist locally, checked out.'.format(branch))


def _update_branch(repo, branch):
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
