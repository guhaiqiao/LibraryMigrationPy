import re
import pkg_resources
from typing import List
import requirements
'''
处理依赖版本信息
'''


class Dependency:

    def __init__(self, project_name, specifiers):
        self.project_name = project_name
        self._specs = specifiers
        self.specs = []
        for specifier in self._specs:
            self.specs.append(
                (specifier[0], pkg_resources.parse_version(specifier[1])))

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
        for requirement in requirements.parse(str):
            project_name = requirement.name
            dependencies.append(Dependency(project_name, requirement.specs))
        return dependencies

    #TODO get the latest version satisfy the specifiers
    # def get_latest_version() 
    # @staticmethod
    # def parse_requirement(str):
    #     requirement = requirements.parse(str)
    #     project_name = requirement.name
    #     return Dependency(project_name, requirement.specs)

if __name__ == '__main__':
    with open("requirements.txt") as f:
        content = f.read()
        a = Dependency.parse_requirements(content)
        print(a)
