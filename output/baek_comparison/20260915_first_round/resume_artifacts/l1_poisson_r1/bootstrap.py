import sys, resource
sys.path[:] = ['/opt/homebrew/Cellar/python@3.14/3.14.3_1/Frameworks/Python.framework/Versions/3.14/lib/python3.14', '/opt/homebrew/Cellar/python@3.14/3.14.3_1/Frameworks/Python.framework/Versions/3.14/lib/python3.14/lib-dynload', '/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/.venv/lib/python3.14/site-packages']
resource.setrlimit(resource.RLIMIT_FSIZE, (16777216, 16777216))
resource.setrlimit(resource.RLIMIT_NOFILE, (128, 128))
resource.setrlimit(resource.RLIMIT_CPU, (1613, 1613))
exec(compile(open('/private/var/folders/b7/dlsj_scs5pxbrd6_69xztsmr0000gn/T/baek-python-ss8o5364/tool.py').read(), 'tool.py', 'exec'), {'__name__': '__main__'})
