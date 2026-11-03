"""Construye el ejecutable de Rumbo con PyInstaller.
Uso (dentro del entorno con las dependencias instaladas):   python construir.py
Genera:  dist/Rumbo  (Linux/Mac)  o  dist/Rumbo.exe  (Windows)
"""
import os
import PyInstaller.__main__ as pyinstaller

sep = os.pathsep  # ';' en Windows, ':' en Linux/Mac

pyinstaller.run([
    "app.py",
    "--name", "Rumbo",
    "--onefile",
    "--noconfirm",
    "--clean",
    "--add-data", f"templates{sep}templates",
    "--add-data", f"schema_sqlite.sql{sep}.",
])
