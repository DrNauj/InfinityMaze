import sys
import os
from cx_Freeze import setup, Executable

base = "Win32GUI" if sys.platform == "win32" else None

# Asegúrate de que el directorio Scripts esté en sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), 'Scripts'))

build_exe_options = {
    "packages": ["ursina", "panda3d.core", "panda3d.direct"],
    "includes": ["mazegenerator"],  # Incluye el módulo mazegenerator
    "include_files": [
        ("assets", "assets"),
        ("venv/Lib/site-packages/panda3d/etc/Config.prc", "Config.prc"),
        ("venv/Lib/site-packages/ursina/fonts/OpenSans-Regular.ttf", "OpenSans-Regular.ttf"),
        ("Scripts/mazegenerator.py", "Scripts/mazegenerator.py")  # Incluye el archivo mazegenerator.py
    ],
}

setup(
    name="InfinityMaze",
    version="1.0",
    description="Juego Infinity Maze con Ursina y Panda3D",
    options={"build_exe": build_exe_options},
    executables=[Executable("Scripts/main.py", base=base, target_name="InfinityMaze.exe")]
)

# Para compilar el script ejecuta el siguiente comando
#python setup.py build_exe
