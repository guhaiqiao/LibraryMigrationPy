from github import Github
import pkg_resources
import github
import pymongo
import re
from dependency import Dependency
access_token = "06bf70084bea39f1c23cf2f0a9f89045f5c27d72"
def getRequirements(namewithowner)->str:
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
    return  dependencies

MONGO_URL = "mongodb://127.0.0.1:27017"
db = pymongo.MongoClient(MONGO_URL).migration_helper_py
projects = list(db.ProjectwithRequirements.find({}, sort=[{"Stars Count", pymongo.DESCENDING}]))
# projects = list(db.lioProject.find({}, sort=[{"Stars Count", pymongo.DESCENDING}]))
print(len(projects))
i = 0
for project in projects:
    name_with_owner = project['Name with Owner']
    dependencies = getRequirements(name_with_owner)
    db.lioProject.update_one({'Name with Owner': name_with_owner},{'$set':{'Dependencies': dependencies}})
    i += 1
    break
    if i % 100 == 0:
        print(i)