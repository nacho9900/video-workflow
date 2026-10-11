# Instalación y portabilidad

## Dependencias Python

Python >=3.11, recomendado 3.12. `requirements.txt`: NumPy 2.3.5 y Pillow 12.3.0, versiones usadas en la verificación. `pyproject.toml`: rangos mayores acotados para evitar saltos incompatibles. Instalar ambas cosas dentro de un venv; `pip install -e .` instala el comando video-workflow. No se usa SciPy, MoviePy, PyTorch ni una dependencia Python de FFmpeg. Los tests usan unittest incluido en Python.

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
mkdir -p inputs outputs models
video-workflow doctor
```

Si el host no tiene internet, usar un wheelhouse preparado para su OS/arquitectura/Python. No copiar un venv de otra computadora. Consultar los errores del instalador; no asumir que un Python del sistema trae NumPy o Pillow.

## FFmpeg y ffprobe

Base verificada: FFmpeg 9.0.2. Exigir 9+ con `scale` que exponga in/out_primaries y in/out_transfer, y los filtros listados por doctor. No depende de zscale, libass ni drawtext: algunas builds no los traen. Encoders: libx264 para SDR, libx265 para HLG. Apple Silicon puede usar h264_videotoolbox/hevc_videotoolbox. El comando doctor comprueba disponibilidad declarada; la prueba de integración comprueba funcionamiento real.

macOS con Homebrew:

```sh
brew install python@3.12 ffmpeg
# Solo si hace falta transcribir:
brew install whisper-cpp
```

Linux: instalar Python/venv, FFmpeg 9+ y fuentes DejaVu desde el proveedor de paquetes o una build de confianza. El FFmpeg incluido en una distribución puede ser más antiguo; revisar `ffmpeg -version` y doctor. Para compilación consultar documentación oficial de [FFmpeg](https://ffmpeg.org/documentation.html). Windows: Python y FFmpeg 9+ en PATH, activar `.venv\Scripts\Activate.ps1`; usar rutas de fuente válidas. Windows/Linux no están certificados todavía: ejecutar los smoke tests antes de prometer una entrega.

## Whisper.cpp (opcional)

CLI externa `whisper-cli`, no paquete pip. [Proyecto oficial](https://github.com/ggml-org/whisper.cpp) y su `models/download-ggml-model.sh` para modelos. Descargar solo desde fuentes confiables; guardar el modelo bajo models/, fuera de Git. `ggml-small.bin` sirve para una primera pasada; un modelo multilingüe mayor puede mejorar nombres y español, a costo de RAM/tiempo.

```sh
whisper-cli --help
video-workflow transcribe inputs/clip.mov --model models/ggml-small.bin \
  --language es --output-dir outputs/transcript-clip
```

El wrapper extrae WAV mono de 16kHz y solicita SRT/JSON completo. Opcional: `--dtw-preset small` o el preset que corresponda a la arquitectura exacta de tu modelo (consultar help). No asignar un preset por el nombre de archivo sin verificarlo. Las coordenadas de transcripción son locales al clip; trasladarlas al timeline editado y corregir a oído. Los modelos no se descargan automáticamente.

## Fuentes

Pasar un archivo .ttf/.otf explícito a captions. Para un aspecto similar usar Arial regular donde esté licenciada/instalada, o Liberation Sans / DejaVu Sans. No se distribuyen fuentes de macOS ni se hardcodea su ruta. La métrica cambia entre fuentes: revisar largo de frases y márgenes. Ejemplos de rutas locales: `/System/Library/Fonts/Supplemental/Arial.ttf` en macOS, `/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf` en Linux, `C:\Windows\Fonts\arial.ttf` en Windows. No garantizar que existan: comprobarlas.

## Binarios y GPU

FFMPEG, FFPROBE y WHISPER_CLI permiten rutas explícitas. Los comandos se pasan como argumentos de subprocess, sin shell. VideoToolbox necesita acceso a servicios de hardware del OS; si el sandbox lo bloquea, usar el mecanismo de aprobación del entorno o codificar por CPU. No solicitar permisos de GPU antes de haber comprobado un fallo real.
