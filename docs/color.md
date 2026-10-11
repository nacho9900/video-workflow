# Balance de color y referencia

La referencia define una intención visual, no obliga a que una pizzería, una calle y un aeropuerto tengan idéntica luz. Analizar el frame original del master limpio; una miniatura SDR comprimida sirve para elegir, no para medir HDR. Pedir timestamp preciso y una región que se sepa neutra (camioneta blanca, camisa gris, etc.). No asumir que piel, cielo o pavimento son gris neutro.

El comando grade usa HLG/BT.2020, decodifica una muestra RGB16bit, selecciona píxeles de baja cromaticidad dentro de ROIs explícitas e invierte la curva HLG. Calcula ganancias RGB acotadas y una exposición moderada, genera curvas monotónicas de 33 puntos con PCHIP y preserva extremos negro/blanco. La referencia recibe parámetros cero. Es una corrección técnica aproximada, no un modelo de look cinematográfico; puede equivocarse si las ROIs no son realmente neutras.

```sh
video-workflow grade outputs/v1/clean.mov examples/color-samples.json \
  --output outputs/v1/balanced.mov
```

ROI: `[x0,y0,x1,y1]` normalizada 0..1. Samples seconds globales del master. `exposure_stops` opcional permite una corrección conservadora explícita; no pasar un sample en el mismo tiempo que reference.

Para producción, incluir `edit_plan` (ruta relativa al JSON de color) y asignar `scene` (índice desde cero) a reference y cada sample. Agregar `broll` (índice desde cero) si el target es un plano de apoyo. Proveer una muestra por cada escena y cada B-roll, excepto el target elegido como referencia. El comando usa el plan compilado para mantener constantes los ajustes dentro de cada toma, y mezcla parámetros solamente en transiciones y fades de planos de apoyo. La referencia debe estar dentro de una toma estable, lejos de fades.

Sin edit_plan, el modo exploratorio interpola suavemente entre anchors; puede hacer variar el color dentro de una toma. Usarlo solo para explorar o en pruebas sintéticas. Revisar la referencia tras exportar: se recomprime, no es pixel idéntica.

No aplicar este matcher a PQ, Dolby Vision dinámico o mezclas SDR/HDR. No conservar metadata dinámica anterior después de alterar imagen sin un flujo específico. Esta entrega es HLG estándar de 10 bits.

## Selector pendiente

No se reutiliza el selector anterior. La mejora debe permitir:

- Video o proxies adecuados para SDR/HDR con búsqueda precisa por frame, reproducción y teclado.
- Identificar archivo, timestamp y frame, incluyendo FPS; no limitar a imágenes cada un segundo.
- Ver varios candidatos grandes lado a lado y comparar piel/blancos/altas luces.
- Seleccionar una ROI neutra y guardar JSON de timestamp/ROI con confirmación clara.
- Separar selección de referencia de aprobación de la corrección con comparación antes/después.

Hasta implementarlo: pedir timestamp usando un reproductor y confirmar con un frame grande. No instalar una app o crear un nuevo selector sin necesidad para la edición.
