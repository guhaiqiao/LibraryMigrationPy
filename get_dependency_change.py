# 根据git log -p requirements.txt构造时间顺序的依赖变化，这个逻辑不太对，已经不用了
import os
from pathos.pools import ProcessPool
from tqdm import tqdm
import time
import re
import subprocess
import datetime
from dependency import Dependency
import pandas as pd
import warnings
import numpy as np
from parallel import parallel

# warnings.filterwarnings("ignore")
cope_repos = set()


class Diff:
    def __init__(self, repo, text):
        self.repo = repo
        self.text = text
        self.date = None
        self.commit = ''
        self.adds = []
        self.rems = []
    
    def analyse(self):
        for line in self.text:
            if line.find('commit') == 0:
                self.commit = line[7:]

            if line.find('Date:') == 0:
                time_str = line[5:].strip()
                self.date = time_str
#                 self.date = datetime.datetime.strptime(time_str, '%a %b %d %H:%M:%S %Y %z')

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
        self.log = log.decode().split('\n')
        self.diffs = []
        self.results = []

    def split_log(self):
        start = -1
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

    def analyse(self):
        self.split_log()
        for diff in self.diffs:
            d = Diff(self.repo, diff)
            d.analyse()
            self.results.append(d)
        return self.results



def get_repos(path):
    for root, dirs, files in os.walk(path):
        array = dirs
        if array:
            return array

def get_dependency_change(project:str):
    df = pd.DataFrame(columns = ['repoName', 'commit', 'date', 'type', 'l1', 'v1', 'l2', 'v2'])
    cmd = 'cd repos/{} && git log -p requirements.txt  '.format(project)
    p = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE)  
    out,err = p.communicate() 
    l = Log(project, out)
    for r in l.analyse():
        common_l = set([x.project_name for x in r.adds]) & set([x.project_name for x in r.rems])
        for l in common_l:
            data = {
                'repoName': project,
                'commit': r.commit,
                'date': r.date,
                'type': 'verchange', 
                'l1': l, 
                'v1': [';'.join(['' + spec[0] + spec[1] for spec in x._specs]) for x in r.adds if x.project_name == l][0],
                'l2': l, 
                'v2': [';'.join(['' + spec[0] + spec[1] for spec in x._specs]) for x in r.rems if x.project_name == l][0]
            }
            df = df.append(data, ignore_index=True)
        for add in r.adds:
            if add.project_name in common_l or add.project_name is None:
                continue
            data = {
                'repoName': project,
                'commit': r.commit,
                'date': r.date,
                'type': 'add', 
                'l1': add.project_name, 
                'v1': ';'.join(['' + spec[0] + spec[1] for spec in add._specs]),
                'l2': np.nan, 
                'v2': np.nan
            }
            df = df.append(data, ignore_index=True)
        for rem in r.rems:
            if rem.project_name in common_l or rem.project_name is None:
                continue
            data = {
                'repoName': str(project),
                'commit': r.commit,
                'date': r.date,
                'type': 'rem', 
                'l1': np.nan, 
                'v1': np.nan,
                'l2': rem.project_name, 
                'v2': ';'.join(['' + spec[0] + spec[1] for spec in rem._specs])
            }
            df = df.append(data, ignore_index=True)
    return df

repos = get_repos('repos')
total_df = parallel(get_requirements_log, repos)
total_df.to_excel('data/migration_changes.xlsx', index=False, encoding='UTF-8')
total_df.query('type=="add" | type=="rem"').to_excel('data/migration_changes_without_verchanges.xlsx', index=False)
cope_repos = np.array(list(cope_repos))
np.savetxt('data/cope_repos.csv', cope_repos)
print(total_df.head(5))