import datetime
import os
import re
import subprocess

import numpy as np
import pandas as pd
import pkg_resources
import pymongo
from dateutil.parser import parse as dateParser

from data_util import get_repos
from parallel import parallel


def get_single_repo_all_version_published_time_from_libraries(repo):
    MONGO_URL = "mongodb://127.0.0.1:27017"
    db = pymongo.MongoClient(MONGO_URL).libraries
    df = pd.DataFrame(columns=['repoName', 'version', 'publishedTime'])
    versions = list(db.versions.find({"Project Name": repo}, sort=[
                    {"Published Timestamp", pymongo.DESCENDING}]))
    for version in versions:
        data = {
            'repoName': repo,
            'version': version['Number'],
            'publishedTime': dateParser(version['Published Timestamp']).strftime('%a %b %d %H:%M:%S %Y %z')
        }
        df = df.append(data, ignore_index=True)
    return df


MONGO_URL = "mongodb://127.0.0.1:27017"
db = pymongo.MongoClient(MONGO_URL)


def get_tag_from_libraries_io(name_with_owner):
    repo = name_with_owner.split('/')[1]
    version_df = pd.DataFrame(
        columns=['repoName', 'version', 'commit', 'date'])
    results = list(db.libraries.tags.find({"Repository Name with Owner": name_with_owner}, sort=[
                   {"Tag Published Timestamp", pymongo.DESCENDING}]))
    for r in results:
        tag = str(r['Tag Name'])
        commit = r['Tag git sha']
        timestamp = str(datetime.datetime.strptime(
            r['Tag Published Timestamp'], '%Y-%m-%d %H:%M:%S %Z').astimezone(tz=None))
        try:
            version = pkg_resources.parse_version(tag)
        except:
            continue

        if version.release is None or version.is_prerelease:
            continue

        version_release = [str(x) for x in (version.release + (0, ))[:3]]
        version_number = '.'.join(version_release)

        data = {
            'repoName': repo,
            'version': version_number,
            'commit': commit,
            'date': timestamp
        }
        version_df = version_df.append(data, ignore_index=True)
    version_df = version_df.sort_values(
        by='date', ascending=False, ignore_index=True)
    return version_df


def get_single_repo_all_version_commit_from_git_tag(repo):
    df = pd.DataFrame(columns=['repoName', 'version', 'commit', 'date'])
    path = f'repos/{repo}'
    cmd = 'cd {} && git tag'.format(path)
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    out, _ = p.communicate()
    tags = sorted(out.decode().split('\n'))
#     print(len(tags))
    for tag in tags:
        version = pkg_resources.parse_version(tag)
        if version.release is None or version.is_prerelease:
            continue

        get_tag_cmd = 'cd {} && git show {}'.format(path, tag)
        pp = subprocess.Popen(get_tag_cmd, shell=True, stdout=subprocess.PIPE)
        out, err = pp.communicate()
        try:
            out = out.decode()
        except UnicodeDecodeError:
            #             print(out)
            continue

        version_release = [str(x) for x in (version.release + (0, ))[:3]]
        version_number = '.'.join(version_release)
        try:
            commit = re.search('commit (\w+)', out).group(1)
            date = re.search('Date: (.*)\n', out).group(1).strip()
            timestamp = str(datetime.datetime.strptime(
                date, '%a %b %d %H:%M:%S %Y %z').astimezone(tz=None))
        except:
            print(out)
            continue
        data = {
            'repoName': repo,
            'version': version_number,
            'commit': commit,
            'date': timestamp
        }
        df = df.append(data, ignore_index=True)
    df = df.sort_values(by='date', ascending=False, ignore_index=True)
    return df


def get_all_repo_all_version_commit():
    repos = get_repos('repos')
    # df = get_single_repo_all_version_commit_from_git('ncbi-genome-download')
    df = parallel(get_single_repo_all_version_commit_from_git_tag, 96, repos)
    df.to_excel('data/project_version_with_commit.xlsx',
                index=False, encoding='utf-8')
    print(df.head(5))
    print(len(df))
