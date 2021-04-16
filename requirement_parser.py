import re
'''
处理依赖版本信息，已改用requirements库
'''
def is_canonical(version):
    return re.match(r'^([1-9][0-9]*!)?(0|[1-9][0-9]*)(\.(0|[1-9][0-9]*))*((a|b|rc)(0|[1-9][0-9]*))?(\.post(0|[1-9][0-9]*))?(\.dev(0|[1-9][0-9]*))?$', version) is not None


DEPENDENCY_PATTERN = r"""
    ^\s*
    (?P<package_name>\w+)
    
    \s*
    (?P<specifier>~=|==|!=|>=|<=|<|>|===)
    \s*
    v?
    (
        (?:(?:[0-9]+)!)?                           # epoch
        (?:[0-9]+(?:\.[0-9]+)*)                  # release segment
        (?:                                          # pre-release
            [-_\.]?
            (?:a|b|c|rc|alpha|beta|pre|preview)
            [-_\.]?
            (?:[0-9]+)?
        )?
        (?:                                         # post release
            (?:-(?:[0-9]+))
            |
            (?:
                [-_\.]?
                (?:post|rev|r)
                [-_\.]?
                (?:[0-9]+)?
            )
        )?
        (?:                                          # dev release
            [-_\.]?
            (?:dev)
            [-_\.]?
            (?:[0-9]+)?
        )?
    )
    (?:\+(?:[a-z0-9]+(?:[-_\.][a-z0-9]+)*))?       # local version
    (?:
        \s*,\s*
        (~=|==|!=|>=|<=|<|>|===)
        \s*
        v?
        (
            (?:(?:[0-9]+)!)?                           # epoch
            (?:[0-9]+(?:\.[0-9]+)*)                  # release segment
            (?:                                          # pre-release
                [-_\.]?
                (?:a|b|c|rc|alpha|beta|pre|preview)
                [-_\.]?
                (?:[0-9]+)?
            )?
            (?:                                         # post release
                (?:-(?:[0-9]+))
                |
                (?:
                    [-_\.]?
                    (?:post|rev|r)
                    [-_\.]?
                    (?:[0-9]+)?
                )
            )?
            (?:                                          # dev release
                [-_\.]?
                (?:dev)
                [-_\.]?
                (?:[0-9]+)?
            )?
        )
        (?:\+(?:[a-z0-9]+(?:[-_\.][a-z0-9]+)*))?       # local version
    )?
    (?:
        \s*,\s*
        (~=|==|!=|>=|<=|<|>|===)
        \s*
        v?
        (
            (?:(?:[0-9]+)!)?                           # epoch
            (?:[0-9]+(?:\.[0-9]+)*)                  # release segment
            (?:                                          # pre-release
                [-_\.]?
                (?:a|b|c|rc|alpha|beta|pre|preview)
                [-_\.]?
                (?:[0-9]+)?
            )?
            (?:                                         # post release
                (?:-(?:[0-9]+))
                |
                (?:
                    [-_\.]?
                    (?:post|rev|r)
                    [-_\.]?
                    (?:[0-9]+)?
                )
            )?
            (?:                                          # dev release
                [-_\.]?
                (?:dev)
                [-_\.]?
                (?:[0-9]+)?
            )?
        )
        (?:\+(?:[a-z0-9]+(?:[-_\.][a-z0-9]+)*))?       # local version
    )
    
"""
_regex = re.compile(
    r"^\s*" + DEPENDENCY_PATTERN + r"\s*;.*$",
    re.VERBOSE | re.IGNORECASE,
)
print(_regex.search("project >= 909!1.2.dev1 , <2.0.dev1 , !=1.0;ply").groups())
