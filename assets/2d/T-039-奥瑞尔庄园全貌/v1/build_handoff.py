"""Compatibility entry point. Use the current review builder; PDF is opt-in."""
from pathlib import Path
import subprocess
import sys

if __name__ == '__main__':
    subprocess.run([sys.executable, str(Path(__file__).with_name('build_review.py')), *sys.argv[1:]], check=True)
