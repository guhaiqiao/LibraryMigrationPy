from distutils.core import run_setup
import subprocess
import git
import os
import pandas as pd
from parallel import parallel
from get_depchange import Log

total_df = pd.read_csv('data/setup_commit_from_git_log.csv')


def get_dep_from_setup(s):
    project = s[0]
    repo = project.split('/')[1]
    owner = project.split('/')[0]
    project_setup_commits = total_df[total_df['Name with Owner']
                                     == project].values
    df = pd.DataFrame(columns=['Name with Owner', 'commit', 'deps'])
    for row in project_setup_commits:
        commit = row[1]

        oldcwd = os.getcwd()
        REPOS_DIR = '/data/hrz/LibraryMigrationPy/repos_50'
        path = os.path.abspath(f'{REPOS_DIR}/{owner}/{repo}/master/')
        os.chdir(path)

        cmd = f'git checkout -f {commit} & python /home/guhaiqiao/LibraryMigrationPy/parse_setup.py'
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, cwd=path)
        out, _ = p.communicate()
        deps = out.decode().split('\n')[0]  # str
        os.chdir(oldcwd)

        assert(os.getcwd() == oldcwd)
        data = {
            'Name with Owner': project,
            'commit': commit,
            'deps': deps
        }
        df = df.append(data, ignore_index=True)
    return df


def multi_get_dep_from_setup(filename, write=False):
    projects = pd.read_csv(filename).values
    df_dep_from_setup = parallel(get_dep_from_setup, 96, projects)
    print(len(df_dep_from_setup))
    print(df_dep_from_setup.head(10))
    if write:
        df_dep_from_setup.to_csv('data/dep_from_setup.csv', index=False)


def get_setup_commit_from_log(project):
    project = project[0]
    repo = project.split('/')[1]
    owner = project.split('/')[0]
    df = pd.DataFrame(columns=['Name with Owner', 'commit', 'date', 'message'])

    REPO_DIR = '/data/hrz/LibraryMigrationPy/repos_50/{}/{}/master'
    cmd = 'cd {} && git log -p setup.py'.format(REPO_DIR.format(owner, repo))
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    out, _ = p.communicate()
    l = Log(project, out)
    for r in l.analyse(parse=False):
        data = {
            'Name with Owner': project,
            'commit': r.commit,
            'date': r.date,
            'message': r.commit_message
        }
        df = df.append(data, ignore_index=True)
    return df


def multi_get_setup_commit_from_log(filename, write=False):
    projects = pd.read_csv(filename).values
    df_from_log = parallel(get_setup_commit_from_log, 96, projects)
    print(len(df_from_log))
    print(df_from_log.head(10))
    if write:
        df_from_log.to_csv(
            'data/setup_commit_from_git_log.csv', index=False, encoding='UTF-8')


if __name__ == '__main__':
    # multi_get_dep_from_setup('data/projects_with_setup.csv', write=True)
    get_dep_from_setup(['pallets/flask', '025589e'])
