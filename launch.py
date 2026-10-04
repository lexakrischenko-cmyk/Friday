import os
import subprocess

os.chdir(r"C:\FridayAI")
subprocess.Popen(
    "python main.py",
    creationflags=subprocess.CREATE_NO_WINDOW,
    shell=True
)