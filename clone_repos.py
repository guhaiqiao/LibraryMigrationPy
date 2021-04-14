import os
import numpy as np
import pandas as pd
from parallel import parallel


projects = pd.read_csv('data/projects.csv')['Name with Owner']
print(len(projects))


def clone_repo(name_with_owner):
    cmd = "cd repos && git clone https://github.com/{}.git".format(
        name_with_owner)
    print("Starting to clone {}".format(name_with_owner))
    os.system(cmd)
    print("Finshed cloning {}".format(name_with_owner))
    print("")

# clone失败的仓库考虑重新clone


def get_fail_repo(filename):
    with open(filename) as f:
        f.read


parallel(clone_repo, 96, projects)
