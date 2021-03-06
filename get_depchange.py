# 获取每个版本的requirements.txt
import datetime
import os
import re
import subprocess
import warnings

import numpy as np
import pandas as pd
import pkg_resources
from git import repo

from data_util import get_repos
from dependency import Dependency
from parallel import parallel

warnings.filterwarnings("ignore")


# 根据git log -p requirements.txt构造时间顺序的依赖变化

cope_repos = set()


class Diff:
    def __init__(self, repo, text):
        self.repo = repo
        self.text = text
        self.date = None
        self.commit = ''
        self.adds = []
        self.rems = []
        self.parent_commits = []
        self.messages = []
        self.commit_message = None

    def analyse(self, parse=False):
        flag = False
        for line in self.text:
            if line.find('commit') == 0:
                self.commit = line[7:]
                continue

            if line.find('Date:') == 0:
                time_str = line[5:].strip()
                self.date = str(datetime.datetime.strptime(
                    time_str, '%a %b %d %H:%M:%S %Y %z').astimezone(tz=None))
                flag = True
                continue

            if line.find('diff') == 0:
                flag = False
                self.commit_message = '\n'.join(self.messages)
                continue

            if flag and line.strip() != '':
                self.messages.append(line.strip())

            if parse:
                if line.find('--- ') == 0:
                    continue

                if line.find('+++ ') == 0:
                    continue

                if line.find('+') == 0:
                    if line[1:].find('-r') == 0:
                        cope_repos.add(self.repo)
                        continue
                    add = Dependency.parse_requirements(line[1:])
                    if add:
                        self.adds.append(add[0])

                if line.find('-') == 0:
                    if line[1:].find('-r') == 0:
                        cope_repos.add(self.repo)
                        continue
                    rem = Dependency.parse_requirements(line[1:])
                    if rem:
                        self.rems.append(rem[0])


class Log:
    def __init__(self, repo, log):
        self.repo = repo
        self.log = log
        self.diffs = []
        self.results = []

    def split_log(self):
        start = -1
        try:
            self.log = self.log.decode().split('\n')
        except:
            return
        for i in range(0, len(self.log)):
            value = self.log[i].find('commit')
            if value == 0:
                if start != -1:
                    new_start = i
                    self.diffs.append(self.log[start:new_start])
                    start = new_start
                else:
                    start = i
        new_start = len(self.log)
        self.diffs.append(self.log[start:new_start])

    def analyse(self, parse=False):
        self.split_log()
        for diff in self.diffs:
            d = Diff(self.repo, diff)
            d.analyse(parse)
            self.results.append(d)
        self.results.sort(key=lambda d: d.date, reverse=False)
        return self.results


def get_depchg_from_git_log_requirements(s):
    project = s[0]
    df = pd.DataFrame(columns=['Name with Owner', 'commit',
                               'date', 'type', 'l1', 'v1', 'l2', 'v2'])

    REPO_DIR = '/data/hrz/LibraryMigrationPy/repos_50/{}/master'
    cmd = 'cd {} && git log -p requirements.txt  '.format(
        REPO_DIR.format(project))
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    out, _ = p.communicate()
    l = Log(project, out)
    for r in l.analyse(parse=True):
        common_l = set([x.project_name for x in r.adds]) & set(
            [x.project_name for x in r.rems])
        for l in common_l:
            data = {
                'Name with Owner': project,
                'commit': r.commit,
                'date': r.date,
                'type': 'verchange',
                'l1': l,
                'v1': [x.spec for x in r.adds if x.project_name == l][0],
                'l2': l,
                'v2': [x.spec for x in r.rems if x.project_name == l][0],
                'message': r.commit_message
            }
            df = df.append(data, ignore_index=True)
        for rem in r.rems:
            if rem.project_name in common_l or rem.project_name is None:
                continue
            data = {
                'Name with Owner': project,
                'commit': r.commit,
                'date': r.date,
                'type': 'rem',
                'l1': np.nan,
                'v1': np.nan,
                'l2': rem.project_name,
                'v2': rem.spec,
                'message': r.commit_message
            }
            df = df.append(data, ignore_index=True)
        for add in r.adds:
            if add.project_name in common_l or add.project_name is None:
                continue
            data = {
                'Name with Owner': project,
                'commit': r.commit,
                'date': r.date,
                'type': 'add',
                'l1': add.project_name,
                'v1': add.spec,
                'l2': np.nan,
                'v2': np.nan,
                'message': r.commit_message
            }
            df = df.append(data, ignore_index=True)
    return df


def multi_get_depchg_from_git_log_requirements(filename, write=False):
    df_project = pd.read_csv(filename).values
    # df_requirements = df_project[df_project['requirements_exists']].values
    df_from_git_log = parallel(
        get_depchg_from_git_log_requirements, 96, df_project)
    print(len(df_from_git_log))
    print(df_from_git_log.head(10))
    if write:
        df_from_git_log.to_csv(
            'data/migration_changes_from_requirements_git_log.csv', index=False, encoding='UTF-8')


def get_commit_message_from_clone(repo, commit):
    cmd = 'cd repos/{} && git show {}'.format(repo, commit)
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    out, _ = p.communicate()
    outs = out.decode().split('\n')
    message = []
    flag = False
    for line in outs:
        if line.find('Date') == 0:
            flag = True
            continue
        if line.find('diff') == 0:
            flag = False
            break

        if flag and line.strip() != '':
            message.append(line.strip())
    return '\n'.join(message)


# 过去的比当前版本小的最大版本
# 获取版本间依赖变化
df = pd.read_excel('data/project_version_with_commit.xlsx')


def get_depchg_from_tag_diff(s):
    repo = s[0]
    date = s[3]
    commit = s[2]
    version = s[1]
    # s行对应的仓库的所有过去版本
    df_repo = df[(df['repoName'] == repo) & (df['date'] < date)].values
    version_num = len(df_repo)

    # 过去的比当前版本小的最大版本
    now_version = pkg_resources.parse_version(s[1])
    now_commit = commit
    last_version = pkg_resources.parse_version('0.0.0')
    last_commit = s[2]
    for i in range(0, version_num):
        temp_version = pkg_resources.parse_version(df_repo[i][1])
        if temp_version < now_version and temp_version > last_version:
            last_version = temp_version
            last_commit = df_repo[i][2]
    # print(now_version, last_version, now_commit, last_commit)
    # git diff tag1 tag2 requirements.txt
    df_dc = pd.DataFrame(columns=[
                         'repoName', 'version', 'commit', 'date', 'type', 'l1', 'v1', 'l2', 'v2', 'message'])

    message = get_commit_message_from_clone(repo, commit)

    cmd = 'cd repos/{} && git diff {} {} requirements.txt  '.format(
        repo, last_commit, now_commit)
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    out, _ = p.communicate()
    r = Diff(repo, out.decode().split('\n'))
    r.analyse()
    common_l = set([x.project_name for x in r.adds]) & set(
        [x.project_name for x in r.rems])
    for l in common_l:
        data = {
            'repoName': repo,
            'version': version,
            'commit': commit,
            'date': date,
            'type': 'verchange',
            'l1': l,
            'v1': [';'.join(['' + spec[0] + spec[1] for spec in x._specs]) for x in r.adds if x.project_name == l][0],
            'l2': l,
            'v2': [';'.join(['' + spec[0] + spec[1] for spec in x._specs]) for x in r.rems if x.project_name == l][0],
            'message': message
        }
        df_dc = df_dc.append(data, ignore_index=True)
    for rem in r.rems:
        if rem.project_name in common_l or rem.project_name is None:
            continue
        data = {
            'repoName': repo,
            'version': version,
            'commit': commit,
            'date': date,
            'type': 'rem',
            'l1': np.nan,
            'v1': np.nan,
            'l2': rem.project_name,
            'v2': ';'.join(['' + spec[0] + spec[1] for spec in rem._specs]),
            'message': message
        }
        df_dc = df_dc.append(data, ignore_index=True)
    for add in r.adds:
        if add.project_name in common_l or add.project_name is None:
            continue
        data = {
            'repoName': repo,
            'version': version,
            'commit': commit,
            'date': date,
            'type': 'add',
            'l1': add.project_name,
            'v1': ';'.join(['' + spec[0] + spec[1] for spec in add._specs]),
            'l2': np.nan,
            'v2': np.nan,
            'message': message
        }
        df_dc = df_dc.append(data, ignore_index=True)
    return df_dc


def multi_get_depchg_from_tag_diff(write=False):
    df_tdc = parallel(get_depchg_from_tag_diff, 96, df.values)
    print(df_tdc.head(10))
    if write:
        df_tdc.to_csv('data/migration_changes_from_tag_diff.csv', index=False)


def filter_verchg_from_migration_change(filename):
    name, type = filename.split('.')
    new_filename = name + '_without_verchanges.' + type

    if type == 'csv':
        df = pd.read_csv(filename)
        result = df.query('type=="add" | type=="rem"')
        result.to_csv(new_filename, index=False)
        return result
    elif type == 'xlsx':
        df = pd.read_excel(filename)
        result = df.query('type=="add" | type=="rem"')
        result.to_excel(new_filename, index=False)
        return result
    else:
        return None


if __name__ == '__main__':
    # get_commit_message('keras', 'b5cb82c689eac0e50522be9d2f55093dadfba24c')
    # multi_get_depchg_from_tag_diff()
    multi_get_depchg_from_git_log_requirements('data/projects_with_requirements.csv', write=True)
    filter_verchg_from_migration_change('data/migration_changes_from_requirements_git_log.csv')
