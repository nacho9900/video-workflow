# Validación y límites

## Matriz verificada

Entorno de desarrollo: macOS Apple Silicon, Python 3.12.14, NumPy 2.3.5, Pillow 12.3.0, FFmpeg/ffprobe 9.0.2. La reproducción final depende también del reproductor/pantalla. No se ha certificado Linux/Windows ni todas las versiones aceptadas por los rangos de dependencias.

Checks que deben pasar: tests unitarios (timeline exacto, curvas HLG, captions, protección de salidas), smoke SDR y HLG por CPU a pequeña resolución. Las pruebas sintéticas no prueban gusto editorial, piel humana ni rendimiento 4K; verificar esos puntos en cada producción. Se comprobó también la instalación desde PyPI en un venv vacío con requirements.txt e instalación editable, sin paquetes del runtime anterior. Whisper requiere una comprobación real con el modelo elegido; no se incluye en los smoke tests.

## Por entrega

- Perfil ffprobe: dimensiones, orientación, FPS CFR, frame count, duración, HEVC Main10/yuv420p10le para HDR, primarias BT.2020, transferencia arib-std-b67 (HLG), matriz BT.2020nc y rango limitado.
- Audio 48kHz, canales adecuados, duración igual al video dentro de 50ms, comienzos en cero. Escuchar uniones, consonantes, ruido, colas y sonoridad; normalización por escena no garantiza el pico final.
- Decodificar el archivo entero con `video-workflow validate FILE --decode`; metadata correcta no descarta corrupción de frames.
- Revisar principio, fin, todas las transiciones/B-roll y subtítulos en la entrega final. Abrir en un reproductor HDR; screenshots sin transformación no representan fielmente HLG.
- Comparar SHA-256 de originales con el manifiesto del render. El hash se calcula en streaming para no cargar gigabytes en RAM.
- Para etapas que copian audio, comparar su bitstream: `ffmpeg -v error -i FILE -map 0:a:0 -c:a copy -f hash -`. No comparar el hash de contenedores diferentes como prueba de igualdad de audio.
- Guardar métricas, logs y archivos del plan con la versión. No cambiar una salida antigua con `-y` por conveniencia.

## Soporte actual

Fuentes homogéneas con tags HLG/BT.2020 o SDR/BT.709; FPS destino entero; crop center-fill. Resampling de FPS y escalado no crean detalle. La preview reduce resolución. Grade solo masters portrait 9:16. El texto es una línea por caption; partir frases en varias entradas. El render falla si un caption no cabe en los márgenes. No hay interfaz editorial gráfica ni selector interactivo de referencia implementado.
