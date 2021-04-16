import pandas as pd
import numpy as np
import math
from data_util import type_count
import pkg_resources


def get_all_add_lib(df):
    libs = set(df['l1'].values)
    libs.remove(np.nan)
    return libs


df = pd.read_csv('data/migration_changes_from_tag_diff_without_verchanges.csv')
libs = get_all_add_lib(df)


def h(add_message, rem_message, add_lib, rem_lib):
    for message in [add_message, rem_message]:
        if message is np.nan:
            continue
        else:
            message = message.lower()
            for w in ['migrate', 'replace', 'switch']:
                if w in message:
                    return 1
    return 0

# DC计算方法有待研究：不同分支同时维护，维护一个tag树记录版本开发情况？


def calculate_query_lib(lib):
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
    distance = 0            # version间距离
    find_flag = False       # 是否找到add该lib的row
    lib = lib.lower()
    for r in df.values:
        # 找到rem该lib的row
        if not find_flag:
            if r[7] != lib:
                continue
            else:
                find_flag = True
                rem_repo = r[0]
                last_repo = rem_repo

                rem_version = r[1]
                last_version = rem_version

                rem_commit = r[9]
                distance = 0
                continue

        now_repo = r[0]
        # 如果repo发生变化则重新找add该repo的行
        if now_repo != last_repo:
            if r[7] != lib:
                find_flag = False
                continue
            else:
                rem_repo = r[0]
                last_repo = rem_repo

                rem_version = r[1]
                last_version = rem_version

                rem_commit = r[9]
                distance = 0
                continue

        # 该lib再次被删除，重新计算距离
        if lib == r[7]:
            rem_repo = r[0]
            last_repo = rem_repo

            rem_version = r[1]
            last_version = rem_version

            rem_commit = r[9]
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
                    add_commit = r[9]
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


if __name__ == '__main__':
    # print(df.head(5))
    # print(type_count('l1',df[df['type']=='add']))
    calculate_query_lib('flask')
