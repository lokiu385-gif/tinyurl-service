import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # folder that contains main.py
sys.path.insert(0, str(ROOT))