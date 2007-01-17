# setup.py
from distutils.core import setup
import py2exe

setup(windows=["kloadManager.py"],
        data_files=[
            (".",[
                "logo.png",
                "dllinfo.txt"]),
            #("docs",[
            #    "docs/README.txt"])
        ]
)
