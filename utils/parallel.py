# @author: hehao98

from pathos.pools import ProcessPool
from tqdm import tqdm
import time
import pandas as pd

# 并行框架

def parallel(func, core_num, *args):
    pool = ProcessPool(core_num)
    try:
        start = time.time()
        # imap方法
        with tqdm(total=len(args[0]), desc="计算进度") as t:  # 进度条设置
            r = pd.DataFrame()
            for i in pool.imap(func, *args):
                r = r.append(i, ignore_index=True)
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