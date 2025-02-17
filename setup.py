import sys
import os
from cx_Freeze import setup, Executable

base = "Win32GUI" if sys.platform == "win32" else None

build_exe_options = {
    "packages": ["os", "ursina", "panda3d.core", "panda3d.direct"],
    "include_files": [
        ("assets", "assets"),
        ("venv/Lib/site-packages/panda3d/etc/Config.prc", os.path.join("etc", "Config.prc")),
        ("venv/Lib/site-packages/panda3d", "panda3d"),
        ("venv/Lib/site-packages/ursina/fonts/OpenSans-Regular.ttf", os.path.join("fonts", "OpenSans-Regular.ttf"))
    ],
}

setup(
    name="InfinityMaze",
    version="1.0",
    description="Juego Infinity Maze con Ursina y Panda3D",
    options={"build_exe": build_exe_options},
    executables=[Executable("Scripts/mazegenerator.py", base=base, target_name="InfinityMaze.exe")]
    )
