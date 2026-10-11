# Criterios de edición

## Antes de renderizar

Entender el objetivo y qué se promociona, audiencia, formato y duración. Confirmar orden e inicio/cierre obligatorios si no están definidos. Mirar los ejemplos reales para medir texto, márgenes, posición, ritmo, transiciones y proporción. Si el usuario quiere todo el recorrido, la primera versión conserva la historia antes de intentar resumir.

Inventariar con ffprobe resolución real, orientación/rotación, FPS variable, duración, audio, tags de color y profundidad. Escuchar la voz y mirar comienzo/final de cada clip. Recortar ruido de cámara, espera y preparación sin cortar consonantes, respiraciones naturales ni el gesto final. Silencedetect puede ayudar pero tráfico, música y habitaciones ruidosas confunden el umbral.

Whisper entrega una transcripción de partida; corregir puntuación, nombres, comida/lugares y palabras del hablante. Sus timestamps/DTW no son verdad absoluta. Mantener inicio/cierre hablados si fueron pedidos; elegir B-roll relevante que no tape la presentación personal final.

## Montaje y voz

Agrupar la voz por escena. Usar planos de apoyo para ilustrar lo que se dice, con entradas rápidas cuando son detalles; conservar más tiempo cuando el lugar o persona necesita leerse. El audio útil sigue siendo el del hablante. No añadir audio de apoyo o música salvo pedido explícito.

Las transiciones deben acompañar movimiento y composición. Negro breve entre lugares, giro/zoom donde el movimiento lo permite, deslizamiento en recorridos o disolvencia para continuidad. Variar con criterio, no aplicar todos los efectos por igual. Revisar que el giro no revele esquinas negras ni corte el rostro. Los scripts clonan handles visuales; si se nota congelado, conseguir handles reales o cambiar la transición.

Separar ritmo visual de la voz: un efecto de medio segundo no exige solapar dos frases ese tiempo. Crossfade corto, con recortes que eviten superponer palabras. Rellenar audio de cada escena hasta su duración antes de concatenar (apad + atrim): evitar que diferencias pequeñas se acumulen y desincronicen subtítulos. La limpieza sugerida es moderada, pero hay que escuchar que no suene metálica.

## Subtítulos

Frases cortas alineadas con las palabras, amarillo brillante y caja negra sólida. Tamaño inicial equivalente a 144px en ancho 2160, regular, posición cerca de 75% de altura; ajustar a referencia y zonas de UI del destino. Entrada breve con escala y opacidad, sin animación que distraiga. Dividir frases largas, no reducir el tamaño hasta que sea ilegible. El motor Pillow reemplaza el rasterizador AppKit/Swift de prototipos locales: misma estrategia de capa RGBA, portable y con fuente explícita.

Quemar la capa después del balance de color. En HDR convertir primarias/transferencia del texto SDR antes de componer. Una caja amarilla que se ve apagada en un PNG sin tonemap no prueba que el master esté mal: inspeccionar en un reproductor HDR y usar una preview SDR convertida correctamente para comparaciones.

## Entrega y revisiones

Preview primero, después master limpio de alta calidad, master con captions y SRT. Mantener cada versión aprobada, y cambiar solamente la parte solicitada en una corrección. Guardar plan, logs, métricas, inventario de fuentes y hashes. Comunicar versiones y limitaciones concretas. El bitrate alto ayuda, pero la revisión visual y el perfil de color importan más que el tamaño de archivo.
