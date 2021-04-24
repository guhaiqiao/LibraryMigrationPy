from data_util import type_count
from metric import calculate_query_lib_from_commit
import os
import pandas as pd
def get_sample_lib():
    # 根据删除次数排序取前一百个
    df_re = pd.read_csv('data/migration_changes_from_requirements_git_log_without_verchanges.csv')
    df_rem = df_re[df_re['type'] == 'rem']
    rem_count = type_count('l2', df_rem)
    lib_count = sorted(rem_count.items(),  key=lambda d: d[1], reverse=True)[:100]
    return [x[0] for x in lib_count]


top_rem_libs = get_sample_lib()
for lib in top_rem_libs:
    rule_path = f'possible_rules_MC/{lib}.txt'
    if os.path.exists(rule_path):
        continue
    print(f'calculating {lib}...')
    possible_rules = calculate_query_lib_from_commit(lib, 96)
    print(f'writing rules into {rule_path}')
    with open(rule_path, 'w') as f:
        f.write('\n'.join([x[0] + ': ' + str(x[1]) for x in possible_rules]))
    print('Done!')