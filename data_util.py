import logging
import pymongo
import pandas as pd
from github import Github
import numpy as np
MONGO_URL = "mongodb://127.0.0.1:27017"

# 项目
def select_projects_from_libraries_io() -> pd.DataFrame:
    """Select a project dataframe as our research subject"""
    db = pymongo.MongoClient(MONGO_URL)

    projects = pd.DataFrame(list(db.libraries.repositories.find({
        "Host Type": "GitHub",
        "Fork": "false",
        "Language": "Python",
        "Stars Count": {"$gt": 10},
    })))

    projects = projects.drop(columns=['_id', 'Description', 'Issues enabled', 'Wiki enabled', 'Pages enabled', 'Forks Count', 'Mirror URL',
                                      'Default branch', 'Watchers Count', 'UUID', 'Fork Source Name with Owner', 'SCM type', 'Pull requests enabled', 'Logo URL'])
    print(projects.head(5))
    print(list(projects))
    db.migration_helper_py.lioProject.insert_many(
        projects.to_dict(orient='records'))
    logging.debug(
        f"{len(projects)} non-fork GitHub Python projects with stars > 10")
    return projects


# 库
def select_libraries_from_libraries_io() -> pd.DataFrame:
    """Select a library dataframe as our research subject"""
    db = pymongo.MongoClient(MONGO_URL)
    libraries = pd.DataFrame(list(db.libraries.projects.find({
        "Platform": "Pypi",
        "Dependent Repositories Count": {"$gt": 10}
    })))

#     print(libraries.head(5))
    libraries = libraries.drop(columns=["_id", "Description", "Keywords", "Dependent Projects Count",
                                        "Last synced Timestamp", "Homepage URL", "Repository URL", "Status", "Package Manager ID"])
    print(list(libraries))
    print(libraries.head(5))
    db.migration_helper_py.lioRepository.insert_many(
        libraries.to_dict(orient='records'))
    logging.debug(
        f"{len(libraries)} libraries with dependent repository count > 10")
    return libraries


def get_star_num(repo):
    db = pymongo.MongoClient(MONGO_URL).migration_helper_py
    project = db.ProjectwithRequirements.find_one(
        {"Name with Owner": {'$regex': f'.*{repo}$'}})
    return project['Stars Count']


def type_count(type, filename):
    count_df = pd.read_excel(filename)
    counts = dict(zip(*np.unique(count_df[type].values, return_counts=True)))
    return counts


if __name__ == "__main__":
    #     logging.basicConfig(level=logging.DEBUG)
    #     select_libraries_from_libraries_io()
    #     select_projects_from_libraries_io()
    #     print(select_libraries_from_libraries_io())
    #     print(select_projects_from_libraries_io())
    print(type_count('type', 'data/migration_changes_without_verchanges_filtered_by_stars.xlsx'))