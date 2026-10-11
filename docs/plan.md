# Edit plan

The plan is JSON; see examples/plan.json. Paths resolve relative to the JSON file, not the working directory. Use relative paths in the editable plan. The compiled plan saved alongside the render contains absolute paths and resolved timings to audit that run.

Global fields: profile (`hlg` or `sdr`), even width/height, integer fps, bitrate, preview_bitrate, audio_overlap in seconds, audio_channels (`mono` or `stereo`), audio_filter (an optional FFmpeg filter string; an empty string disables cleanup filters), scenes, transitions, and captions. Audio is normalized per scene to -16 LUFS / -1.5 dBTP in two passes; inspect the master because a crossfade can change the final peak. Mono is appropriate for a mono voice recording; preserve stereo when the source requires it.

Scene fields: file, in/out in seconds of the original, title, and broll. Timings are snapped to the frame grid. B-roll fields: file, in (original source), at (seconds relative to the edited scene), duration, and fade at each end. B-roll audio is not used. If B-roll needs to continue across multiple scenes, split it explicitly or extend the renderer; do not treat `at` as a global timestamp.

Provide one transition per join: type and duration. Types: fadeblack, fade, smoothleft/right, zoomin, and rollleft/right. Roll combines rotation and zoom to cover the edges, with a short crossfade at the center. A brief supporting shot can enter with fades of approximately 0.16 seconds; a location change can use a dip to black of approximately 0.5 seconds or a roll that follows the movement.

The audio_overlap field determines the narration timeline independently of the visual effect's duration. Visual handles are extended with cloned frames for longer effects. The transition duration, in frames, must have the same parity as audio_overlap and be at least as long as that overlap. Scenes that are too short are rejected. Change trims if words overlap; do not increase the overlap for visual styling.

Captions in the plan and examples/captions.json use global master start/end timestamps and text. They must be ordered, non-overlapping, and within the video duration. The renderer saves captions in the plan but does not burn them in; the captions command takes a separate JSON list. Extract it as follows:

```sh
python -c 'import json; p=json.load(open("outputs/v1/edit-plan.json")); json.dump(p["captions"],open("outputs/v1/captions.json","w"),ensure_ascii=False,indent=2)'
```

The preview uses a width of 720 with the same aspect ratio and FPS; it is not the deliverable. The master preserves the configured resolution. Do not increase resolution/FPS expecting to recover detail that does not exist; configure these according to the sources and destination.
