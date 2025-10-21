# Plan de trabajo — InfinityMaze

Propósito: mantener un registro vivo de las mejoras, correcciones y prioridades del proyecto. Actualizar este archivo cada vez que se realice un cambio relevante.

## Resumen rápido
Proyecto en Ursina con generador de laberintos, minimapa, trampas y sistema de pisos. Recomendado priorizar correcciones críticas, separación de responsabilidades y optimizaciones de rendimiento.

## Fase 0 — Preparación rápida (30–90 minutos)
1. Añadir `requirements.txt` y `README.md` (instrucciones de ejecución, dependencias y cómo contribuir).
2. Ejecutar linters y formateador para detectar problemas rápidos (qué es y cómo hacerlo):
   - ¿Qué es? Linters (p. ej. flake8/pylint) detectan errores de estilo y posibles bugs; Black formatea el código automáticamente.
   - Instalar (recomendado en un entorno virtual):
     - pip install flake8 black
   - Comandos:
     - flake8 .          # lista problemas de estilo y errores simples
     - black .           # formatea el código automáticamente
   - Opcional: configurar VSCode/IDE para ejecutar linters y formato al guardar.
   - Archivos de configuración sugeridos: `.flake8`, `pyproject.toml` (para black).
3. Resultado esperado: lista de advertencias/errores a corregir y código formateado.

## Fase 1 — Corrección de bugs críticos y hardening (2–6 horas)
- Mover inicialización de `Ursina()` y configuración de ventana fuera de entidades.
- Proteger llamadas a `destroy()` comprobando existencia.
- Eliminar duplicaciones de configuración.
- Revisar uso correcto de APIs (taskMgr/accept).

## Fase 2 — Refactor y separación de responsabilidades (6–12 horas)
- Separar en módulos: app/entrypoint, ui, player, generator.
- `MazeGame` como controlador del estado, no como Entity si no es necesario.
- Añadir typing y docstrings.

## Fase 3 — Optimización de rendimiento (6–20 horas)
- Precarga en background (hilos o coroutines seguras).
- Reutilizar entidades (object pooling) en vez de destruir/crear.
- Reducción de LOD y uso de instancing para muros repetidos.
- Profiling (cProfile) para identificar cuellos de botella.

## Fase 4 — Calidad de código y tests (4–12 horas)
- Tests unitarios para generador y utilidades.
- CI (GitHub Actions) que ejecute linters y tests.

## Fase 5 — UX, accesibilidad y mejoras de juego (6–20 horas)
- Guardado de settings persistentes (JSON).
- Mejoras de controles (crouch, head-bob, suavizado).
- Audio y opciones de volumen.
- Indicadores opcionales de rendimiento.

## Fase 6 — Empaquetado y distribución (4–8 horas)
- Scripts de build (PyInstaller) y documentación de empaquetado.
- README y CONTRIBUTING actualizados.

## Tareas opcionales / Investigación
- Procedural difficulty scaling.
- Multijugador ligero.
- Shaders avanzados y optimizaciones GPU.
- Soporte de gamepad.

## Prioridades recomendadas (inmediatas)
1. requirements.txt + README.
2. Ejecutar linters y aplicar Black.
3. Mover creación de `Ursina()` al entrypoint.
4. Añadir checks seguros antes de `destroy()`.
5. Implementar precarga sin bloquear (si hay lag).

## Estimaciones
- MVP (correcciones críticas + refactor mínimo + requirements/tests básicos): 1–3 días.
- Optimización y UX completo: 1–2 semanas.

## Siguientes pasos sugeridos
- Proveer archivos faltantes importantes (`mazegenerator.py` ya presente, subir assets si faltan).
- Decidir prioridad: ¿Performance, UX o nuevas features?
- ¿Quieres que implemente ahora la Fase 0 (crear `requirements.txt`, `README.md` y ejecutar cambios básicos) o que empiece moviendo la inicialización de Ursina al entrypoint?

---

Mantener este archivo actualizado: cada PR o cambio mayor debe añadir una línea en "Historial de cambios" con fecha y brevedad.
