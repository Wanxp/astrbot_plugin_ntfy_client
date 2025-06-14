import os

try:
    import python_ntfy
except ImportError:
    os.system("pip install python-ntfy")