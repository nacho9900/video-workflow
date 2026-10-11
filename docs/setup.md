# Installation and portability

## Python dependencies

Python >=3.11; 3.12 is recommended. `requirements.txt` pins NumPy 2.3.5 and Pillow 12.3.0, the versions used for verification. `pyproject.toml` declares version ranges bounded below the next major release to avoid incompatible upgrades. Install both inside a virtual environment; `pip install -e .` installs the video-workflow command. SciPy, MoviePy, PyTorch, and Python FFmpeg packages are not used. Tests use Python's built-in unittest module.

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
mkdir -p inputs outputs models
video-workflow doctor
```

If the host has no internet access, use a wheelhouse prepared for its OS, architecture, and Python version. Do not copy a virtual environment from another computer. Inspect installer errors; do not assume the system Python includes NumPy or Pillow.

## FFmpeg and ffprobe

Verified baseline: FFmpeg 9.0.2. Require 9+ with a `scale` filter exposing in/out_primaries and in/out_transfer, and the filters listed by doctor. This workflow does not depend on zscale, libass, or drawtext; some builds omit them. Encoders: libx264 for SDR and libx265 for HLG. Apple Silicon can use h264_videotoolbox/hevc_videotoolbox. The doctor command checks declared availability; the integration test checks actual operation.

macOS with Homebrew:

```sh
brew install python@3.12 ffmpeg
# Only if transcription is needed:
brew install whisper-cpp
```

Linux: install Python/venv, FFmpeg 9+, and DejaVu fonts from your package provider or a trusted build. A distribution's bundled FFmpeg may be older; check `ffmpeg -version` and doctor. For compilation, consult the official [FFmpeg documentation](https://ffmpeg.org/documentation.html). Windows: put Python and FFmpeg 9+ on PATH, activate `.venv\Scripts\Activate.ps1`, and use valid font paths. Windows/Linux have not yet been certified; run the smoke tests before promising a deliverable.

## Whisper.cpp (optional)

Use the external `whisper-cli` executable, not a pip package. See the [official project](https://github.com/ggml-org/whisper.cpp) and its `models/download-ggml-model.sh` script for models. Download only from trusted sources; keep models under models/, outside Git. `ggml-small.bin` is suitable for an initial pass; a larger multilingual model may improve names and Spanish transcription at the cost of memory and processing time.

```sh
whisper-cli --help
video-workflow transcribe inputs/clip.mov --model models/ggml-small.bin \
  --language es --output-dir outputs/transcript-clip
```

The wrapper extracts a mono 16 kHz WAV file and requests SRT/full JSON output. Optionally use `--dtw-preset small` or the preset matching your model's exact architecture (consult the help output). Do not assign a preset based solely on the filename without checking it. Transcription timestamps are local to the clip; translate them to the edited timeline and correct them by listening. Models are not downloaded automatically.

## Fonts

Pass an explicit .ttf/.otf file to captions. For a similar appearance, use regular Arial where it is licensed and installed, or Liberation Sans / DejaVu Sans. macOS fonts are not distributed, and their paths are not hardcoded. Font metrics differ: check phrase lengths and margins. Example local paths: `/System/Library/Fonts/Supplemental/Arial.ttf` on macOS, `/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf` on Linux, and `C:\Windows\Fonts\arial.ttf` on Windows. Check that the path exists; these locations are not guaranteed.

## Binaries and GPU

FFMPEG, FFPROBE, and WHISPER_CLI allow explicit binary paths. Commands are passed as subprocess arguments without a shell. VideoToolbox requires access to OS hardware services; if the sandbox blocks it, use the environment's approval mechanism or encode on the CPU. Do not request GPU permissions before confirming an actual failure.
