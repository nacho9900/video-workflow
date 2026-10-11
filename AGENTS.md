# Agent guide

This repository provides a reusable workflow. Read README.md and docs/workflow.md; consult the setup, plan, color, and validation documents before running those stages. The user's instructions in the current session take priority.

## Expected result

Produce a complete, reviewable video with clear speech, trims that remove setup and unwanted noise at the beginning and end without cutting words, relevant B-roll, transitions chosen to suit movement, and readable captions. Preserve resolution, frame rate, and dynamic range when the sources and destination support them. Never add music unless requested; the user may add it later.

## Files and versions

- Keep originals and reference videos in inputs/, read-only. Do not move, replace, edit, or rewrite the metadata of originals.
- Store all derivatives, downloaded models, transcripts, previews, logs, and deliverables in outputs/ or models/ (both ignored by Git).
- Create a new version for each revision; preserve approved versions. Commands reject existing outputs. If a run fails, use another directory or repair only its intermediate files after inspecting them; never delete approved deliverables to retry.
- Do not commit media, actual production transcripts, models, licensed font files, secrets, or virtual environments. Review git status and git diff --cached before publishing changes.
- Save the compiled edit plan, source SHA-256 manifest, doctor report, measurements, and validation results alongside the deliverables.

## Tools

- Python >=3.11, with NumPy and Pillow declared in requirements.txt and pyproject.toml. Create a virtual environment; do not depend on private host runtimes.
- FFmpeg + ffprobe: inventory, trimming, audio, montage, transitions, color, encoding, and verification. Run doctor first. FFmpeg 9+ is the baseline because the scale filter must support color primaries and transfer conversion.
- Whisper.cpp + an explicitly selected model: optional local transcription. Do not install openai-whisper/PyTorch by habit. Verify the CLI and DTW preset when used. Timestamps require listening and editorial correction.
- Pillow + an explicitly selected font file: portable animated captions. Use bright yellow text on a black box, a large font, and short phrases. Check margins on a phone; split a long phrase before shrinking the font.
- VideoToolbox accelerates encoding on Apple Silicon; use software encoding on other hosts or if it fails. An encoder appearing in doctor does not prove the sandbox allows GPU access. Do not switch to 8-bit to work around an HDR problem.

## Required process

1. Clarify only missing information that affects the result. Then continue through delivery. Analyze the user's examples rather than inventing their style.
2. Inventory the media and watch/listen to the clips. Choose in/out points around useful speech; preserve natural breaths and short tails. Do not rely solely on silencedetect.
3. Build a plan with an explicit order, required opening/closing when specified, and B-roll over the original narration. Do not transcribe B-roll sound as narration.
4. Correct the transcript and align timestamps with words. Create captions using global timeline timestamps, without overlaps, preserving each phrase's meaning.
5. Test a preview. Review transitions in motion and audio joins with headphones. Keep audio crossfades short and independent of visual effects. If words overlap, adjust trims/handles; do not conceal the issue with an effect.
6. Render a clean master. If color correction is requested, analyze the original HDR frame and a neutral ROI. Apply restrained corrections per shot; inspect skin, whites, and highlights. Use grade with edit_plan to keep parameters constant within shots and smooth changes only during transitions (docs/color.md).
7. Burn captions after color correction to preserve their yellow. Deliver both masters and an SRT file, without changing an approved montage during a color revision.
8. Validate dimensions, profile, primaries, transfer, bit depth, FPS, frame count, A/V timing, and decoding. Compare the audio bitstream hash when a stage promises to copy it. Inspect frames and listen to the final file, not just the preview.
9. Deliver clear links, the version, and relevant limitations. Do not claim that HDR metadata or a high bitrate guarantees visual fidelity.

## Limitations to disclose

These scripts support CFR masters with integer frame rates and homogeneous HLG/BT.2020 or SDR/BT.709 sources. PQ, dynamic Dolby Vision, untagged media, and SDR/HDR mixtures require a separately designed and verified conversion. Do not retag a source to pass it off as HDR. Framing uses center-fill cropping: check the subject and text positions, and adapt the crop if the subject falls outside the frame. The current color sampler requires a vertical 9:16 master and explicit neutral ROIs. The visual reference selector is a pending improvement, not a completed feature.
