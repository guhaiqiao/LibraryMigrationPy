import os
import pymongo
MONGO_URL = "mongodb://127.0.0.1:27017"
db = pymongo.MongoClient(MONGO_URL).migration_helper_py
projects = list(db.ProjectwithRequirements.find({}, sort=[{"Stars Count", pymongo.DESCENDING}]))
print(len(projects))
i = 0

def clone_repo(project):
    name_with_owner = project['Name with Owner']
    cmd = "cd repos && git clone https://github.com/{}.git".format(name_with_owner)
    print("Starting to clone {}".format(name_with_owner))
    print("Running command '{}'".format(cmd))
    os.system(cmd)
    print("Finshed cloning {}".format(name_with_owner))
    print("#####################################")
    print("")

def get_fail_repo(filename):
    with open(filename) as f:
        f.read
# parallel(clone_repo, projects[0:5])
for project in projects:
    clone_repo(project)
