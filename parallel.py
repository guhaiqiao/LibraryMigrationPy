from pathos.pools import ProcessPool
from tqdm import tqdm
import time
import pandas as pd

# 并行框架

def parallel(func, core_num, return_df=True, *args):
    pool = ProcessPool(core_num)
    try:
        start = time.time()
        # imap方法
        with tqdm(total=len(args[0]), desc="计算进度") as t:  # 进度条设置
            if return_df:
                r = pd.DataFrame()
                for i in pool.imap(func, *args):
                    r = r.append(i, ignore_index=True)
                    t.set_postfix({'并行函数': func.__name__, "计算花销": "%ds" % (time.time() - start)})
                    t.update()
            else:
                r = []
                for i in pool.imap(func, *args):
                    r.append(i)
                    t.set_postfix({'并行函数': func.__name__, "计算花销": "%ds" % (time.time() - start)})
                    t.update()
        return r
    except Exception as e:
        print(e)
    finally:
        # 关闭池
        pool.close()  # close the pool to any new jobs
        pool.join()  # cleanup the closed worker processes
        pool.clear()  # Remove server with matching state


def parallel_metric(func, core_num, *args):
    pool = ProcessPool(core_num)
    try:
        # start = time.time()
        # imap方法
        # with tqdm(total=len(args[0]), desc="计算进度") as t:  # 进度条设置
        RC = {}
        MC = {}
        DC = {}
        for i in pool.imap(func, *args):
            add_lib = i['add_lib']
            # commit间隔大于50，舍弃
            if i['RC'] != 0:
                if add_lib not in RC.keys():
                    RC[add_lib] = 0
                    MC[add_lib] = 0
                    DC[add_lib] = 0
                RC[add_lib] += i['RC']
                MC[add_lib] += i['MC']
                DC[add_lib] += i['DC']
                # t.set_postfix({'并行函数': func.__name__, "计算花销": "%ds" % (time.time() - start)})
                # t.update()
        return RC, MC, DC
    except Exception as e:
        print(e)
    finally:
        # 关闭池
        pool.close()  # close the pool to any new jobs
        pool.join()  # cleanup the closed worker processes
        pool.clear()  # Remove server with matching state


def parallel_metric_show(func, core_num, *args):
    pool = ProcessPool(core_num)
    try:
        start = time.time()
        # imap方法
        with tqdm(total=len(args[0]), desc="计算进度") as t:  # 进度条设置
            RC = {}
            MC = {}
            DC = {}
            for i in pool.imap(func, *args):
                add_lib = i['add_lib']
                # commit间隔大于50，舍弃
                if i['RC'] != 0:
                    if add_lib not in RC.keys():
                        RC[add_lib] = 0
                        MC[add_lib] = 0
                        DC[add_lib] = 0
                    RC[add_lib] += i['RC']
                    MC[add_lib] += i['MC']
                    DC[add_lib] += i['DC']
                t.set_postfix({'并行函数': func.__name__, "计算花销": "%ds" % (time.time() - start)})
                t.update()
            return RC, MC, DC
    except Exception as e:
        print(e)
    finally:
        # 关闭池
        pool.close()  # close the pool to any new jobs
        pool.join()  # cleanup the closed worker processes
        pool.clear()  # Remove server with matching state