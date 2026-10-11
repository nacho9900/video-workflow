# Plan de edición

JSON, ver examples/plan.json. Las rutas se resuelven respecto al JSON, no al cwd. Usar plan editable con rutas relativas; el plan compilado guardado junto al render tiene rutas absolutas y tiempos resueltos para auditar esa ejecución.

Campos globales: profile (`hlg` o `sdr`), width/height pares, fps entero, bitrate, preview_bitrate, audio_overlap en segundos, audio_channels (`mono` o `stereo`), audio_filter (cadena FFmpeg opcional; vacío desactiva filtros de limpieza), scenes, transitions, captions. Audio normalizado por escena a -16 LUFS / -1.5dBTP en dos pasadas; revisar el master porque un crossfade puede cambiar el pico final. Mono es adecuado para una voz mono; mantener stereo cuando la fuente lo requiera.

Escena: file, in/out en segundos del original, title, broll. Se ajustan tiempos a la rejilla de frames. B-roll: file, in (original), at (segundos relativos a la escena editada), duration, fade por cada extremo. No usa audio del B-roll. Si un B-roll necesita seguir sobre varias escenas, partirlo explícitamente o ampliar el renderer: no tratar `at` como un timestamp global.

Una transición por unión: type y duration. Tipos: fadeblack, fade, smoothleft/right, zoomin, rollleft/right. Roll combina giro y zoom para cubrir bordes, con crossfade corto en el centro. El clip breve de apoyo puede entrar con fades de ~0.16s; una unión de lugares puede usar negro de ~0.5s o roll si acompaña el movimiento.

El audio_overlap determina el timeline de voz, independientemente de la duración del efecto visual. Se prolongan handles visuales con frames clonados para efectos mayores. La duración de transición, en frames, debe tener la misma paridad que audio_overlap y ser al menos ese solapamiento. Se rechazan escenas demasiado cortas. Cambiar los trims si se pisan palabras; no aumentar el overlap por estética.

Captions del plan y examples/captions.json: start/end globales del master, text. Deben estar ordenados, sin solapamiento y dentro de duración. El renderer guarda captions en el plan pero no los quema; el comando captions toma una lista JSON independiente. Puede extraerse así:

```sh
python -c 'import json; p=json.load(open("outputs/v1/edit-plan.json")); json.dump(p["captions"],open("outputs/v1/captions.json","w"),ensure_ascii=False,indent=2)'
```

La preview usa ancho 720, misma relación de aspecto y FPS; no es la entrega. El master conserva la resolución configurada. No aumentar resolución/FPS esperando recuperar detalle inexistente: configurar según las fuentes y el destino.
