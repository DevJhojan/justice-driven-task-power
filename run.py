import sys
import flet as ft
from pathlib import Path
from app.main import main

project_root = Path(__file__).parent
sys.path.append(str(project_root))


if __name__ == "__main__":
    ft.run(main)