# Validation and limitations

## Verified environment and checks

Development environment: macOS on Apple Silicon, Python 3.12.14, NumPy 2.3.5, Pillow 12.3.0, and FFmpeg/ffprobe 9.0.2. Final playback also depends on the player and display. Linux/Windows and all versions allowed by the dependency ranges have not been certified.

Required checks: unit tests (exact timeline, HLG curves, captions, and output protection), plus low-resolution SDR and HLG smoke tests using CPU encoding. Synthetic tests do not verify editorial taste, human skin tones, or 4K performance; check these for each production. Installation from PyPI was also verified in an empty virtual environment using requirements.txt and editable installation, without packages from the previous runtime. Whisper requires a real check with the selected model; it is not included in the smoke tests.

## For each deliverable

- Inspect the ffprobe profile: dimensions, orientation, CFR frame rate, frame count, duration, HEVC Main10/yuv420p10le for HDR, BT.2020 primaries, arib-std-b67 transfer (HLG), BT.2020nc matrix, and limited range.
- Check 48 kHz audio, appropriate channels, duration matching the video within 50 ms, and zero start times. Listen to joins, consonants, noise, tails, and loudness; normalization per scene does not guarantee the final peak.
- Decode the entire file with `video-workflow validate FILE --decode`; correct metadata does not rule out corrupted frames.
- Inspect the beginning, end, all transitions/B-roll, and captions in the final deliverable. Open it in an HDR player; screenshots without a color transformation do not faithfully represent HLG.
- Compare original-file SHA-256 hashes with the render manifest. Hashes are computed in streaming chunks to avoid loading gigabytes into RAM.
- For stages that copy audio, compare its bitstream: `ffmpeg -v error -i FILE -map 0:a:0 -c:a copy -f hash -`. Do not compare hashes of different containers as proof of identical audio.
- Save metrics, logs, and plan files with the version. Do not overwrite an old output with `-y` for convenience.

## Current support

Homogeneous sources tagged HLG/BT.2020 or SDR/BT.709; integer destination FPS; center-fill cropping. Frame-rate resampling and scaling do not create detail. The preview reduces resolution. Grade supports only portrait 9:16 masters. Text uses one line per caption; split phrases into multiple entries. Rendering fails if a caption does not fit within the margins. No graphical editing interface or interactive reference selector has been implemented.
