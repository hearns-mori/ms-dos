from pathlib import Path
import subprocess
import sys


# Directory where this main.py is located
BASE_DIR = Path(__file__).resolve().parent

# Persistent directories
PROJECTS_DIR = Path.home() / "ms-dos" / "projects"
DOS_DIR = Path.home() / "ms-dos" / "dos"


# Create required directories
for directory in (PROJECTS_DIR, DOS_DIR):
    directory.mkdir(parents=True, exist_ok=True)
    print(f"Directory ready: {directory}")


# Locate the two Python programs relative to main.py
ms_py = BASE_DIR / "ms.py"
dos_py = BASE_DIR / "dos.py"


# Make sure they exist
for script in (ms_py, dos_py):
    if not script.exists():
        print(f"Error: {script} not found.")
        sys.exit(1)


# Use the same Python interpreter running main.py
python = sys.executable


# Start both programs
processes = [
    subprocess.Popen([python, str(ms_py)]),
    subprocess.Popen([python, str(dos_py)]),
]


try:
    # Keep main.py alive while both processes are running
    for process in processes:
        process.wait()

except KeyboardInterrupt:
    print("\nStopping ms.py and dos.py...")

    for process in processes:
        if process.poll() is None:
            process.terminate()

    for process in processes:
        process.wait()

    print("Stopped.")
