import re
import pandas as pd
import numpy as np
import math
from data_util import type_count
import pkg_resources
from git import Repo
from parallel import parallel_metric, parallel_metric_show
import time
import os
def get_all_add_lib(df):
    libs = set(df['l1'].values)
    libs.remove(np.nan)
    return libs


# df_tag_diff = pd.read_csv('data/migration_changes_from_tag_diff_without_verchanges.csv')
df_requirements_log = pd.read_csv('data/migration_changes_from_requirements_git_log_without_verchanges.csv')
# print(df_requirements_log.head(10))
# libs = get_all_add_lib(df_requirements_log)



# 实现精细一点，考虑库名
def h(add_message, rem_message, add_lib, rem_lib):
    migrate_key_words = ["migrat", "switch", "replac", "instead", "move", "swap",
                         "unify", "convert", "chang", "迁移", "替换", "修改"]
    add_key_words = ["use", "adopt", "introduc", "upgrad", "updat", "采用", "升级"]
    rem_key_words = ["remov", "delet", "abandon", "删除", "移除"]
    add_message = add_message.lower()
    rem_message = rem_message.lower()
    add_lib_part = split_lib_name(add_lib)
    rem_lib_part = split_lib_name(rem_lib)
    if add_message == rem_message:
        if contain_any_part(add_message, add_lib_part):
            if contain_any_part(add_message, rem_lib_part) or contain_any_part(add_message, add_key_words) or contain_any_part(add_message, migrate_key_words):
                return True
            else:
                return False
        elif contain_any_part(add_message, rem_lib_part) and (contain_any_part(add_message, migrate_key_words) or contain_any_part(add_message, rem_key_words)):
            return True
        else:
            return False
    else:
        if contain_any_part(add_message, add_lib_part) and contain_any_part(add_message, add_key_words) and contain_any_part(rem_message, rem_lib_part) and contain_any_part(rem_message, rem_key_words):
            return True
        elif contain_any_part(add_message, rem_lib_part) and contain_any_part(add_message, migrate_key_words):
            return True
        else:
            return False

def split_lib_name(lib: str):
    lib_part = set(re.split("_|-|[0-8]", lib.lower()))
    if '' in lib_part:
        lib_part.remove('')
    return lib_part


def contain_any_part(message, parts) -> bool:
    for part in parts:
        if part in message:
            return True
    return False

def get_distance(name_with_owner, commit1, commit2, depth=0):
    ''' 默认commit1在commit2之后，寻找commit的parent直到找到commit2或找不到返回-1
        因为计算DC的时候要计算add之后的commit，所以直接向前找
    '''    
    if commit1 == commit2:
        return 0
    
    REPO_DIR = '/data/hrz/LibraryMigrationPy/repos_50/{}/master'
    r = Repo(path=REPO_DIR.format(name_with_owner))
    c = r.commit(commit1)

    if c.parents != ():
        # print(len(c.parents), depth)

        for pc in c.parents:
            if pc.hexsha == commit2:
                return 1
            elif depth > 20:
                return -1
            else:
                d = get_distance(name_with_owner, pc.hexsha, commit2, depth+1)
                if d != -1:
                    return d + 1
                else:
                    return -1
    else:
        return -1

# DC计算方法有待研究：不同分支同时维护
def calculate_query_lib_from_version(lib):
    RC = {}
    DC = {}
    MC = {}
    RS = {}
    MS = {}
    DS = {}
    CONF = {}
    rem_repo = None         # rem该lib的repo
    last_repo = None

    rem_version = None      # repo rem该lib的version
    last_version = None     # 上一行对应的version
    rem_commit = None       # rem对应的commit
    last_commit = None
    distance = 0            # version间距离
    find_flag = False       # 是否找到add该lib的row
    lib = lib.lower()
    for r in df_tag_diff.values:
        # 找到rem该lib的row
        if not find_flag:
            if r[6] != lib:
                continue
            else:
                find_flag = True
                rem_repo = r[0]
                last_repo = rem_repo

                rem_version = r[1]
                last_version = rem_version

                rem_commit = r[8]
                last_commit = rem_commit
                distance = 0
                continue

        now_repo = r[0]
        # 如果repo发生变化则重新找rem该lib的行
        if now_repo != last_repo:
            if r[6] != lib:
                find_flag = False
                continue
            else:
                rem_repo = r[0]
                last_repo = rem_repo

                rem_version = r[1]
                last_version = rem_version

                rem_commit = r[8]
                last_commit = rem_commit
                distance = 0
                continue

        # 该lib再次被删除，重新计算距离
        if lib == r[6]:
            rem_repo = r[0]
            last_repo = rem_repo

            rem_version = r[1]
            last_version = rem_version

            rem_commit = r[8]
            distance = 0
            continue

        # 找rem之后的add行
        type = r[4]
        if type != 'add':
            continue
        else:
            now_version = r[1]
            # 如果当前版本大于rem时的版本则跳过
            if pkg_resources.parse_version(now_version) > pkg_resources.parse_version(rem_version):
                continue
            else:
                add_lib = r[5].lower()
                # 该lib又被添加，重新找rem该repo的行
                if add_lib == lib:
                    find_flag = False
                    continue
                else:
                    add_commit = r[8]
                    # 当前版本与上一版本不同，更新上一版本，distance加一
                    if now_version != last_version:
                        last_version = now_version
                        distance += 1
                    # 计算(a, b)的三个指标
                    if add_lib not in RC.keys():
                        RC[add_lib] = 0
                        MC[add_lib] = 0
                        DC[add_lib] = 0
                    RC[add_lib] += 1
                    MC[add_lib] += h(add_commit, rem_commit, lib, add_lib)
                    DC[add_lib] += 1 / (distance + 1) ** 2
    # 不存在可能的迁移规则
    if not RC:
        return None
    else:
        # 最大rc
        max_rc = max(RC.values())
        for key in RC.keys():
            RS[key] = RC[key] / max_rc
            MS[key] = math.log2(MC[key] + 1)
            DS[key] = DC[key] / RC[key]
            # CONF[key] = RS[key] * DS[key]
            CONF[key] = RS[key] * MS[key] * DS[key]

        # 筛选出不为零的前20个候选规则
        CONF = {k: v for k, v in CONF.items() if v > 0}
        possible_rule = sorted(
            CONF.items(), key=lambda kv: kv[1], reverse=True)[:20]
        # return RS, MS, DS, CONF, possible_rule
        return possible_rule

def calculate_query_lib_from_commit(lib, core_num, show=False):
    RS = {}
    MS = {}
    DS = {}
    CONF = {}
    cache = f'cache/{lib}.xlsx'
    if not os.path.exists(cache):
        rem_repo = None         # rem该lib的repo
        last_repo = None

        rem_commit = None       # rem对应的commit SHA
        rem_message = None
        find_flag = False       # 是否找到add该lib的row

        df_possible_migration = pd.DataFrame(columns=['rem_repo', 'add_lib', 'rem_lib', 'add_commit', 'add_message', 'rem_commit', 'rem_message'])
        lib = lib.lower()
        for r in df_requirements_log.values:
            # 找到rem该lib的row
            if not find_flag:
                if r[6] is np.nan or r[6].lower() != lib:
                    continue
                else:
                    find_flag = True
                    rem_repo = r[0]
                    last_repo = rem_repo
                    # print('find!')
                    rem_commit = r[1]
                    rem_message = r[8]
                    continue

            now_repo = r[0]
            # 如果repo发生变化则重新找rem该lib的行
            if now_repo != last_repo:
                if r[6] is np.nan or r[6].lower() != lib:
                    find_flag = False
                    continue
                else:
                    rem_repo = r[0]
                    last_repo = rem_repo

                    rem_commit = r[1]
                    rem_message = r[8]
                    continue

            # 该lib再次被删除，重新计算距离
            if r[6] is not np.nan and r[6].lower() == lib:
                rem_repo = r[0]
                last_repo = rem_repo

                rem_commit = r[8]
                continue

            # 找rem之后的add行
            type = r[3]
            if type != 'add':
                continue
            else:
                # 不知道什么bug，需要判断nan
                if r[4] is np.nan:
                    continue
                add_lib = r[4].lower()
                # 该lib又被添加，重新找rem该repo的行
                if add_lib == lib:
                    find_flag = False
                    continue

                add_commit = r[1]
                add_message = r[8]
                
                data = {
                    'rem_repo': rem_repo,
                    'add_lib': add_lib,
                    'rem_lib': lib,
                    'add_commit': add_commit,
                    'rem_commit': rem_commit,
                    'add_message': add_message,
                    'rem_message': rem_message
                }
                df_possible_migration = df_possible_migration.append(data, ignore_index=True)
        df_possible_migration.to_excel(cache, index=False)
    else:
        df_possible_migration = pd.read_excel(cache)
    if show:
        RC, MC, DC = parallel_metric_show(cal_metric, core_num, df_possible_migration.values)
    else:
        RC, MC, DC = parallel_metric(cal_metric, core_num, df_possible_migration.values)
    # 不存在可能的迁移规则
    if not RC:
        return None
    else:
        # 最大rc
        max_rc = max(RC.values())
        for key in RC.keys():
            RS[key] = RC[key] / max_rc
            MS[key] = math.log2(MC[key] + 1)
            DS[key] = DC[key] / RC[key]
            # CONF[key] = RS[key] * DS[key]
            CONF[key] = RS[key] * MS[key] * DS[key]

        # 筛选出不为零的前20个候选规则
        CONF = {k: v for k, v in CONF.items() if v > 0}
        possible_rule = sorted(
            CONF.items(), key=lambda kv: kv[1], reverse=True)[:20]
        # return RS, MS, DS, CONF, possible_rule
        return possible_rule

def cal_metric(s):
    rem_repo = s[0]
    add_lib = s[1]
    rem_lib = s[2]
    add_commit = s[3]
    add_message = s[4]
    rem_commit = s[5]
    rem_message = s[6]
    distance = get_distance(rem_repo, add_commit, rem_commit)
    data = {
        'add_lib': add_lib,
        'RC': 0,
        'MC': 0,
        'DC': 0
    }
    if distance == -1:
        return data
    else:
        data['RC'] = 1
        data['MC'] = h(add_message, rem_message, add_lib, rem_lib)
        data['DC'] = 1 / (distance + 1) ** 2
        return data

if __name__ == '__main__':
    # print(df.head(5))
    # print(type_count('l1',df[df['type']=='add']))
    calculate_query_lib('flask')
