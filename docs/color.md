# Color balance and reference

The reference defines a visual intention; it does not require a pizzeria, a street, and an airport to have identical lighting. Analyze the original frame from the clean master. A compressed SDR thumbnail can help select a frame, but cannot measure HDR. Ask for a precise timestamp and a region known to be neutral (a white van, a gray shirt, etc.). Do not assume that skin, sky, or pavement is neutral gray.

The grade command uses HLG/BT.2020, decodes a 16-bit RGB sample, selects low-chroma pixels within explicit ROIs, and inverts the HLG curve. It calculates bounded RGB gains and restrained exposure adjustments, generates monotonic 33-point curves with PCHIP, and preserves black/white endpoints. The reference receives zero adjustment parameters. This is an approximate technical correction rather than a cinematic look model; it can be wrong if the ROIs are not actually neutral.

```sh
video-workflow grade outputs/v1/clean.mov examples/color-samples.json \
  --output outputs/v1/balanced.mov
```

ROI: `[x0,y0,x1,y1]`, normalized to 0..1. Sample timestamps use global master seconds. The optional `exposure_stops` field allows an explicit conservative adjustment; do not provide a sample at the same timestamp as the reference.

For production, include `edit_plan` (a path relative to the color JSON file) and assign `scene` (a zero-based index) to the reference and each sample. Add `broll` (a zero-based index) when the target is a B-roll shot. Provide one sample per scene and per B-roll shot, except for the target chosen as the reference. The command uses the compiled plan to keep adjustments constant within each shot, blending parameters only during transitions and B-roll fades. The reference must fall within a stable shot, away from fades.

Without edit_plan, exploratory mode interpolates smoothly between anchors; this can change the color within a shot. Use it only for exploration or synthetic tests. Inspect the reference after export: it is recompressed and will not be pixel-identical.

Do not apply this matcher to PQ, dynamic Dolby Vision, or SDR/HDR mixtures. Do not retain previous dynamic metadata after changing the image without a dedicated workflow. This workflow exports standard 10-bit HLG.

## Pending selector improvement

The previous selector is not reused. The improved selector should support:

- Video or suitable SDR/HDR proxies with accurate frame seeking, playback, and keyboard controls.
- Identification of the file, timestamp, and frame, including FPS; selection must not be limited to one image per second.
- Large candidates viewed side by side to compare skin, whites, and highlights.
- Selection of a neutral ROI and saving timestamp/ROI JSON with clear confirmation.
- Separate reference selection and correction approval, using a before/after comparison.

Until it is implemented, ask for a timestamp from a player and confirm it with a large frame image. Do not install an app or build a new selector unless the edit requires it.
