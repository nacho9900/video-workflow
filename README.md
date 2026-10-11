# Video Workflow

Flujo local de edición para producir videos con voz, planos de apoyo, transiciones, subtítulos y balance de color. Incluye herramientas Python y una guía para que un agente pueda continuar el trabajo en otro proyecto. Los ejemplos son ficticios: no contienen clips, textos ni tiempos de una producción real.

## Estructura

- `inputs/`: originales y videos de referencia. Ignorado por Git. Nunca modificar.
- `outputs/`: entregas, versiones, previews, planes, logs e intermediarios. Ignorado por Git.
- `src/video_workflow/`: herramientas reutilizables.
- `examples/`: planes de edición y subtítulos ficticios.
- `docs/`: instalación, criterios de edición y límites técnicos.
- `AGENTS.md`: instrucciones para el agente que arme el próximo video.

Los directorios ignorados se crean al instalar; no se guardan en Git aunque estén vacíos. No hace falta Git LFS porque no se versiona media.

## Preparación

Python 3.11 o superior (recomendado 3.12), FFmpeg/ffprobe 9+ con libx264/libx265 y conversión de color de `scale`. Whisper.cpp es opcional para transcripción. Consultar [instalación](docs/setup.md) para comandos por plataforma, fuentes, modelos y comprobaciones.

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install -e .
mkdir -p inputs outputs models
video-workflow doctor
```

`requirements.txt` fija las versiones de las bibliotecas usadas para verificar este proyecto; `pyproject.toml` declara rangos compatibles. No hay rutas de Python, FFmpeg, modelos o fuentes atadas a una computadora. Usar `FFMPEG`, `FFPROBE` y `WHISPER_CLI` para especificar binarios fuera de PATH.

## Crear un video

1. Poner los clips y ejemplos visuales en `inputs/`. Pedir objetivo, orden, inicio/cierre obligatorios, música y estilo solamente si faltan.
2. Inspeccionar los archivos y escuchar la voz. Transcribir para ayudar a recortar y subtitular; corregir manualmente el texto.
3. Copiar `examples/plan.json` y adaptarlo. Las rutas son relativas al directorio del plan. Cada escena conserva su voz; el audio del B-roll se descarta.
4. Renderizar y revisar una preview antes del 4K. Cada ejecución necesita una carpeta de salida nueva.
5. Aplicar color al master limpio si corresponde, después quemar los subtítulos. Entregar master limpio, subtitulado y SRT.

```sh
video-workflow inventory inputs --output outputs/inventory.json
video-workflow transcribe inputs/opening.mov \
  --model models/ggml-small.bin --output-dir outputs/transcript-opening
video-workflow render examples/plan.json --preview --output-dir outputs/preview-v1
video-workflow render examples/plan.json --output-dir outputs/v1
video-workflow captions outputs/v1/clean.mov examples/captions.json \
  --font /ruta/a/una/fuente.ttf --output outputs/v1/captioned.mp4
video-workflow validate outputs/v1/captioned.mp4 --decode
```

En Apple Silicon agregar `--encoder videotoolbox` a `render`, `grade` y `captions` si la prueba real de codificación funciona. El modo por defecto usa CPU y no exige macOS. HDR se exporta como HEVC Main10, BT.2020/HLG; SDR como H.264/BT.709. Se rechazan mezclas de espacios de color sin conversión previa explícita.

Leer [flujo editorial](docs/workflow.md), [formato del plan](docs/plan.md), [color](docs/color.md) y [validación](docs/validation.md). El código prepara los archivos; mirar y escuchar la entrega sigue siendo parte obligatoria del trabajo.

## Pruebas

```sh
python -m unittest discover -s tests -v
python tests/smoke.py --profile sdr --font /ruta/a/fuente.ttf
python tests/smoke.py --profile hlg --font /ruta/a/fuente.ttf
```

Las pruebas de integración generan clips sintéticos, editan, subtitulan, decodifican el resultado y comprueban que los originales no cambien. HLG también recorre el balance de color. No usan material de una producción real. Ver [matriz verificada](docs/validation.md).

## Pendiente

Mejorar el selector interactivo de referencia de color: video con búsqueda precisa, comparación real y exportación de selección/ROI. No se incluye el selector anterior. El flujo actual acepta un timestamp y regiones explícitas; el diseño pendiente está en [color](docs/color.md).
