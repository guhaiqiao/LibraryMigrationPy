import pandas as pd
import numpy as np
import math
from data_util import type_count
import pkg_resources


def get_all_add_lib(filename):
    df = pd.read_csv(filename)
    libs = set(df['l1'].values)
    libs.remove(np.nan)
    return libs


libs = get_all_add_lib('data/new_migration_changes_without_verchanges.csv')
df = pd.read_csv('data/new_migration_changes_without_verchanges.csv')


def h(message):
    return 1


def calculate_query_lib(lib):
    RC = {}
    DC = {}
    MC = {}
    RS = {}
    MS = {}
    DS = {}
    CONF = {}
    add_repo = None         # add该lib的repo
    add_version = None      # repo add该lib的version
    last_version = None     # 上一行对应的version
    distance = 0            # version间距离
    find_flag = False       # 是否找到add该lib的row
    lib = lib.lower()
    for r in df.values:
        # 找到add该lib的row
        if not find_flag:
            if r[5] != lib:
                continue
            else:
                find_flag = True
                add_repo = r[0]
                last_repo = add_repo

                add_version = r[1]
                last_version = add_version

                distance = 0
                continue

        now_repo = r[0]
        # 如果repo发生变化则重新找add该repo的行
        if now_repo != last_repo:
            if r[5] != lib:
                find_flag = False
                continue
            else:
                add_repo = r[0]
                add_version = r[1]
                last_version = add_version
                distance = 0
                continue

        # 该lib再次被添加，重新计算距离
        if lib == r[5]:
            add_repo = r[0]
            add_version = r[1]
            last_version = add_version
            distance = 0
            continue

        # 找add之后的rem行
        type = r[4]
        if type != 'rem':
            continue
        else:
            now_version = r[1]
            # 如果当前版本小于add时的版本则跳过
            if pkg_resources.parse_version(now_version) < pkg_resources.parse_version(add_version):
                continue
            else:
                rem_lib = r[7].lower()
                # 该lib被删除，重新找add该repo的行
                if rem_lib == lib:
                    find_flag = False
                    continue
                else:
                    commit_message = r[9]
                    # 当前版本与上一版本不同，更新上一版本，distance加一
                    if now_version != last_version:
                        last_version = now_version
                        distance += 1
                    # 计算(a, b)的三个指标
                    if rem_lib not in RC.keys():
                        RC[rem_lib] = 0
                        MC[rem_lib] = 0
                        DC[rem_lib] = 0
                    RC[rem_lib] += 1
                    MC[rem_lib] += h(commit_message)
                    DC[rem_lib] += 1 / (distance + 1) ** 2
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

        possible_rule = sorted(
            CONF.items(), key=lambda kv: kv[1], reverse=True)[:20]
        # return RS, MS, DS, CONF, possible_rule
        return possible_rule

if __name__ == '__main__':
    # print(df.head(5))
    # print(type_count('l1',df[df['type']=='add']))
    calculate_query_lib('flask')
