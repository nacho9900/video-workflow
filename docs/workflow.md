# Editing criteria

## Before rendering

Understand the objective, what is being promoted, the audience, format, and duration. Confirm the order and required opening/closing if they have not been defined. Inspect actual examples to assess text, margins, placement, pacing, transitions, and proportions. If the user wants the entire sequence, preserve the story in the first version before trying to shorten it.

Use ffprobe to inventory actual resolution, orientation/rotation, variable frame rates, duration, audio, color tags, and bit depth. Listen to the speech and inspect each clip's beginning/end. Trim camera noise, waiting, and setup without cutting consonants, natural breaths, or the final gesture. Silencedetect can help, but traffic, music, and noisy rooms can confuse its threshold.

Whisper provides a starting transcript; correct punctuation, names, food/place references, and the speaker's words. Its timestamps/DTW alignment are not absolute truth. Keep the spoken opening/closing when requested; choose relevant B-roll that does not obscure the final personal introduction.

## Montage and narration

Group narration by scene. Use B-roll to illustrate what is being said, with quick entries for details; allow more time when the location or person needs to be understood. The useful audio remains the speaker's track. Do not add B-roll audio or music unless explicitly requested.

Transitions should follow movement and composition. Use a brief dip to black between locations, rotation/zoom where the movement supports it, a slide during movement through a location, or a dissolve for continuity. Vary transitions thoughtfully rather than applying every effect uniformly. Check that rotation does not reveal black corners or crop the face. The scripts clone visual handles; if the freeze is noticeable, obtain real handles or change the transition.

Separate visual pacing from narration: a half-second effect does not require overlapping two phrases for that long. Use a short crossfade and trims that avoid overlapping words. Pad each scene's audio to its duration before concatenation (apad + atrim) to prevent small differences from accumulating and desynchronizing captions. The suggested cleanup is restrained, but listen for metallic artifacts.

## Captions

Use short phrases aligned with speech, bright yellow text, and a solid black box. Start with a regular font equivalent to 144 px at a width of 2160, placed near 75% of the frame height; adjust to the reference and the destination's UI safe areas. Use a brief entrance with scale and opacity, avoiding distracting animation. Split long phrases rather than reducing the font until it is unreadable. The Pillow engine replaces the AppKit/Swift rasterizer used in local prototypes: the same RGBA layer approach, with portability and an explicit font file.

Burn the layer after color balancing. For HDR, convert the SDR text's primaries/transfer before compositing. A yellow box that looks dull in a PNG without tone mapping does not prove the master is wrong: inspect it in an HDR player and use a correctly converted SDR preview for comparisons.

## Delivery and revisions

Deliver a preview first, followed by a high-quality clean master, a captioned master, and an SRT file. Preserve each approved version and change only the requested part during a revision. Save the plan, logs, metrics, source inventory, and hashes. Communicate versions and specific limitations. A high bitrate helps, but visual review and the color profile matter more than file size.
