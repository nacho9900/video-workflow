# Guía para agentes

Este repositorio es un sistema de trabajo reutilizable. Leer README.md y docs/workflow.md; consultar setup, plan, color y validation antes de ejecutar esas etapas. Las instrucciones del usuario de la sesión tienen prioridad.

## Resultado esperado

Producir un video completo y revisable, con voz clara, recortes que quiten preparación/ruidos del inicio y final sin comer palabras, planos de apoyo pertinentes, transiciones elegidas según el movimiento y subtítulos legibles. Mantener la resolución, los FPS y el rango dinámico cuando la fuente y el destino lo permitan. Nunca agregar música sin pedido; puede quedar para el usuario.

## Archivos y versiones

- Originals/referencias en inputs/, solo lectura. No mover, reemplazar, editar ni reescribir metadatos de originales.
- Todo derivado, modelo descargado, transcripción, preview, log y entrega va en outputs/ o models/ (ignorados).
- Cada corrección crea una versión nueva; conservar versiones aprobadas. Los comandos rechazan salidas existentes. Si una ejecución falla, usar otra carpeta o reparar solo sus intermediarios después de inspeccionarlos; nunca borrar entregas aprobadas para reintentar.
- No subir media, transcripciones reales, modelos, fuentes con licencia, secretos ni entornos virtuales al repo. Revisar git status y git diff --cached antes de publicar cambios.
- Guardar plan compilado, manifiesto SHA-256 de fuentes, doctor, mediciones y validación junto a la entrega.

## Herramientas

- Python >=3.11, NumPy y Pillow declarados en requirements/pyproject. Crear un venv; no depender de runtimes privados del host.
- FFmpeg + ffprobe: inventario, recortes, audio, montaje, transiciones, color, codificación y verificación. Ejecutar doctor primero. FFmpeg 9+ es la base por la conversión de primarias/transferencia de scale.
- Whisper.cpp + un modelo explícito: transcripción local opcional; no instalar openai-whisper/PyTorch por inercia. Verificar su CLI y el preset DTW si se usa. Los timestamps necesitan escucha y corrección editorial.
- Pillow + una fuente explícita: subtítulos animados portables. Texto amarillo brillante sobre caja negra; tamaño grande y frases cortas. Verificar márgenes en un teléfono; dividir una frase larga antes de achicarla.
- VideoToolbox acelera Apple Silicon; usar software en otro host o si falla. Que un encoder aparezca en doctor no prueba que el sandbox permita acceder a la GPU. No cambiar a 8 bits para sortear un problema HDR.

## Proceso obligatorio

1. Aclarar únicamente información faltante que cambie el resultado. Después de eso avanzar hasta entregar. Analizar ejemplos del usuario, no inventar su estilo.
2. Hacer inventario y escuchar/ver clips. Elegir in/out alrededor de voz útil; conservar respiraciones naturales y pequeñas colas. No decidir solo con silencedetect.
3. Construir plan con orden explícito, inicio/cierre si son obligatorios y B-roll sobre voz original. No transcribir sonido de B-roll como narración.
4. Corregir transcripción; ajustar timestamps a palabras. Crear captions globales, sin solapamiento, conservando el sentido de la frase.
5. Probar en preview. Revisar transiciones en movimiento y uniones de audio con auriculares. Crossfade de audio corto e independiente del efecto visual. Si se solapan palabras, ajustar recortes/handles; no taparlo con un efecto.
6. Renderizar master limpio. Si se pide color, analizar el frame HDR original y neutral ROI. Corregir moderadamente por toma; inspeccionar piel, blancos y altas luces. Usar grade con edit_plan para mantener parámetros por toma y suavizar solo en transiciones (docs/color.md).
7. Quemar subtítulos después del color para no alterar su amarillo. Entregar ambos masters y SRT, sin cambiar montajes aprobados durante una corrección de color.
8. Validar dimensiones, perfil, primarias, transferencia, profundidad, FPS, frame count, A/V y decodificación. Comparar hash del audio si una etapa promete copiarlo. Revisar frames y escuchar el archivo final, no solo el preview.
9. Entregar links claros, versión y límites relevantes. No afirmar que una metadata HDR o un bitrate alto garantizan fidelidad visual.

## Limitaciones que no hay que ocultar

Estos scripts soportan masters CFR con FPS enteros y fuentes homogéneas HLG/BT.2020 o SDR/BT.709. PQ, Dolby Vision dinámico, material sin tags y mezclas SDR/HDR necesitan una conversión diseñada y verificada aparte. No retaggear una fuente para hacerla pasar por HDR. El recorte de encuadre es center-fill: revisar posición de persona/textos, adaptar si el sujeto queda fuera. El color sampler actual exige master vertical 9:16 y neutral ROIs explícitas. El selector visual de referencia es una mejora pendiente, no una función terminada.
