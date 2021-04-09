from github import Github
import pkg_resources
import github
import pymongo
import numpy as np
import re
import pandas as pd
from dependency import Dependency

# 根据github api判断是否含有requirements.txt
access_token = "06bf70084bea39f1c23cf2f0a9f89045f5c27d72"
def get_requirements(namewithowner)->str:
    g = Github(access_token)
    try:
        repo = g.get_repo(namewithowner)
    except github.GithubException:
        print(namewithowner)
        return None
    dependencies = []
    try:
        contents_byte = repo.get_contents("requirements.txt").decoded_content
        contents_str = str(contents_byte, 'utf8')
        dependencies = [x.to_dict() for x in Dependency.parse_requirements(contents_str)]
    except github.GithubException:
        return dependencies
    except pkg_resources.packaging.requirements.InvalidRequirement:
        return None
    except:
        print(namewithowner)
        raise IndexError
    return  dependencies

MONGO_URL = "mongodb://127.0.0.1:27017"
db = pymongo.MongoClient(MONGO_URL).migration_helper_py
projects = list(db.lioProject.find({}, sort=[{"Stars Count", pymongo.DESCENDING}]))
print(len(projects))
i = 0
    
# 更新数据库中的dependency
for project in projects:
    name_with_owner = project['Name with Owner']
    dependencies = get_requirements(name_with_owner)
    db.lioProject.update_one({'Name with Owner': name_with_owner},{'$set':{'Dependencies': dependencies}})
    i += 1
    break
    if i % 100 == 0:
        print(i)

# 统计具有requirements.txt的项目
total = len(projects)
no_github_repo = 0
no_requirements = 0
with_requirements = 0
i = 0
for project in projects:
    i += 1
    dependencies = project['Dependencies']
    if dependencies is None:
        no_github_repo += 1
    elif len(dependencies) == 0:
        no_requirements += 1
    else:
        with_requirements += 1
        db.ProjectwithRequirements.insert_one(project)
    if i % 10000 == 0:
        print(i)

print(f"total: {total}")
print(f'no_github_repo: {no_github_repo}')
print(f'no_requirements: {no_requirements}')

# 具有requirements.txt的项目存入projects.csv
projects = list(db.ProjectwithRequirements.find({}, sort=[{"Stars Count", pymongo.DESCENDING}]))
pName = pd.DataFrame(columns=['Name with Owner'])
for project in projects:
    pName = pName.append({'Name with Owner':project['Name with Owner']}, ignore_index=True)
pName.to_csv('projects.csv', index=False)
print(pName)