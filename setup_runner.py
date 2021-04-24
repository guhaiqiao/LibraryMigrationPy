# setup.py runner with exception caught, replaces parse_setup.py
# 12f23eddde <rzhe@pku.edu.cn> - Apr 24 2021

import os
import sys
from distutils.core import run_setup
from utils.redirect_stdout import StdoutToString
from pydriller import GitRepository

# run a checkouted setup script
# return (['req1', 'req2'], out)
def setup_runner(file_path: str):
    
    oldcwd = os.getcwd()
    
    path = os.path.abspath(file_path)
    dirname, basename = os.path.split(path)
    os.chdir(dirname)
    result = None
    
    with StdoutToString() as out:
        try:
            result = run_setup(basename, stop_after="init")
        except Exception as e:
            print(e, file=sys.stderr)
                
    os.chdir(oldcwd)
    assert(os.getcwd() == oldcwd)
    return (result.install_requires if result else None, str(out))


# checkout to one commit, avoid concurrency issues
# >>> with CheckoutToCommit('repos_50/shuwarin/dreaming/master', 'aabbccddeeff'):
# >>>    your code here
class CheckoutToCommit:
    def __init__(self, repo_path: str, commit_sha: str, branch='master'):
        self._branch = branch
        self._commit_sha = commit_sha
        self._repo_path = os.path.abspath(repo_path)
        self._lock_path = os.path.abspath(self._repo_path + '/checkout.lock')

    def __enter__(self):
        # acquire lock
        if os.path.exists(self._lock_path):
            with open(self._lock_path, 'r') as f:
                sha = f.readline()
            raise Exception(f'lock {self._lock_path} exists: checking out {sha}')

        with open(self._lock_path, 'w+') as f:
            f.write(self._commit_sha)

        # checking out to commit
        repo = GitRepository(self._repo_path)
        repo.checkout(self._commit_sha)
        

    def __exit__(self, type, value, traceback):
        # checking out to current branch
        repo = GitRepository(self._repo_path)
        head = repo.get_head().hash
        
        if not head == self._commit_sha:
            # fixes: up to date with master
            try:
                repo.checkout(self._branch)
            except Exception as e:
                print(e)

        # release lock
        if not os.path.exists(self._lock_path):
            raise Exception(f'lock {self._lock_path} not found')
        os.remove(self._lock_path)
        

if __name__ == '__main__':
    print(setup_runner('repos_50/hall-lab/svtyper/master/setup.py'))