from distutils.core import run_setup

result = None
try:
    result = run_setup('setup.py', stop_after="init")
except Exception as e:
    pass

if result:
    print(result.install_requires)
