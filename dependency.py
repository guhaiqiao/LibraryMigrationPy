import re
import pkg_resources
from typing import List
import requirements
import pymongo
'''
处理依赖版本信息
'''

cop_repo = []

class Dependency:

    def __init__(self, project_name, specifiers):
        self.project_name = project_name
        self._specs = specifiers
        self.specs = []
        for specifier in self._specs:
            self.specs.append(
                (specifier[0], pkg_resources.parse_version(specifier[1])))
        self.spec = ';'.join(['' + spec[0] + spec[1] for spec in self._specs])

    def __str__(self):
        return f"{self.project_name} {self._specs} {self.specs}"

    def to_dict(self):
        specs = []
        for spec in self._specs:
            specs.append({'specifier': spec[0], 'version': spec[1]})
        return {'project_name': self.project_name, 'specs': specs}

    @staticmethod
    def load_dict(self, dict):
        project_name = dict['project_name']
        specs = []
        for spec in dict['specs']:
            specs.append((spec['specifier'], spec['version']))
        return Dependency(project_name, specs)

    @staticmethod
    def parse_requirements(str):
        dependencies = []
        # raw_str = str
        
        if str == '' or '--hash' in str or str.find('git+') == 0:
            return dependencies
        
        bad_suffix = ['\\', '--', '#', '=py3', '+cpu', ' -f ', '=h']
        for s in bad_suffix:
            if s in str:
                str = str[:str.find(s)].strip()

        str = str.split(';')[0].strip() # exclude python_version, sys_platform
        
        if str == '':
            return dependencies
        
        if str[-1] == ',':
            str = str[:-1].strip()
        if str.find('- ') == 0:
            str = str[1:].strip()
        str = str.replace('=>', '>=')
        str = str.replace('=<', '<=')
        str = str.replace('<<', '<')
        str = str.replace('"', '')
        str = str.replace('(', '')
        str = str.replace(')', '')
        str = str.replace('[security]', '')  # delete [security]
        str = re.sub("(\w+)\s=\s([0-9]+(?:\.[0-9]+)*.*)", r'\1==\2',str)  # replace '=' with '=='
        str = re.sub("(\w+)=([0-9]+(?:\.[0-9]+)*.*)", r'\1==\2',str)  # replace ' = ' with '=='
        str = re.sub("(\w+)\s([0-9]+(?:\.[0-9]+)*.*)", r'\1==\2',str)  # replace ' ' with '=='

        try:
            for requirement in requirements.parse(str):
                project_name = requirement.name
                dependencies.append(Dependency(project_name, requirement.specs))
        except:
            pass
        return dependencies

    #TODO get the latest version satisfy the specifiers
    # def get_latest_version() 

def get_dependency_from_libraries_io(name_with_owner, tag):
    MONGO_URL = "mongodb://127.0.0.1:27017"
    db = pymongo.MongoClient(MONGO_URL)
    project = name_with_owner.split('/')[1]
    results = list(db.libraries.dependencies.find({"Project Name": project, "Version Number": tag}))
    deps = []
    for r in results:
        dep_name = r["Dependency Name"]
        dep_requirement = r["Dependency Requirements"]
        if dep_requirement != '*':
            dep = dep_name + ' ' + dep_requirement
        else:
            dep = dep_name
        d = Dependency.parse_requirements(dep)[0]
        # print(d.project_name, d.spec)
        deps.append(d)
    return deps
    
if __name__ == '__main__':
    with open("requirements.txt") as f:
        content = f.read()
        a = Dependency.parse_requirements(content)
        print(a)
