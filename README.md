# InfinityMaze

Proyecto de ejemplo creado con Ursina (generador de laberintos, minimapa, trampas y sistema de pisos).

## Requisitos
- Python 3.8+
- Git (opcional)

## Instalación (recomendado en un entorno virtual)
1. Crear y activar un entorno virtual:
   - Windows:
     - python -m venv .venv
     - .venv\Scripts\activate
2. Instalar dependencias:
   - pip install -r requirements.txt

## Ejecutar el juego
- python Scripts\main.py

## Formato y linters (Fase 0, punto 2)
- Instalar herramientas (ya están en requirements.txt):
  - black: formateador de código automático.
  - flake8: linter para detectar problemas de estilo y errores simples.
- Comandos recomendados:
  - pip install -r requirements.txt
  - black .
  - flake8 .
- Sugerencia: configurar tu editor (VSCode, PyCharm) para formatear con Black al guardar y mostrar advertencias de flake8.

## Archivos añadidos en Fase 0
- `requirements.txt` — dependencias del proyecto.
- `README.md` — instrucciones básicas.
- `.flake8` y `pyproject.toml` — configuración recomendada para linters/formateador.

## Nota sobre la carpeta build
La carpeta `build/` en tu copia local corresponde a la versión empaquetada/executable del juego (por ejemplo creada por PyInstaller u otra herramienta). Esa carpeta NO debe subirse al repositorio. Se ha añadido `.gitignore` para excluir `build/`, `dist/` y archivos binarios (`*.exe`) del control de versiones.

## Empaquetado (opcional) — crear un .exe con PyInstaller
Si quieres crear una versión ejecutable para Windows, un método sencillo es usar PyInstaller:

1. Instalar PyInstaller (recomendado en entorno virtual):
   - pip install pyinstaller

2. Crear el ejecutable (ejemplo básico, ejecutar desde la raíz del proyecto):
   - pyinstaller --onefile --add-data "assets;assets" --name InfinityMaze Scripts\main.py

   Notas:
   - `--add-data "assets;assets"` incluye la carpeta `assets` en el ejecutable; en Windows usa `;` como separador, en Linux/macOS usa `:`.
   - Ajusta opciones (icono, icon, paths) según necesidad.
   - Los artefactos se generan en `dist/` y `build/`. Ambos están excluidos en `.gitignore` por defecto.

3. Probar el ejecutable en una máquina limpia y verificar que `assets` y dependencias están accesibles.

## Siguientes pasos recomendados
1. Ejecutar `black .` y `flake8 .` para obtener la lista de advertencias.
2. Revisar y corregir los avisos críticos antes de avanzar al refactor.
3. Actualizar `PLAN_DE_TRABAJO.md` conforme se avance.

