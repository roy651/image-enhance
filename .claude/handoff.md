# image-enhance — Session Handoff

## What this project is

Local AI image upscaling infrastructure for Mac (Apple Silicon, MPS). No CUDA needed.
Stack: Real-ESRGAN (upscale) + GFPGAN (face restoration) + frequency blending (texture preservation).

## Current state

`upscale.py` is the main script. Working end-to-end for 2x/4x upscaling with texture preservation.

**Last known issue:** User ran the script and hit an error — unknown at handoff time. Likely related to the `--scale` / `outscale` value being passed to `RealESRGANer.enhance()`. The `choices=[2, 4]` restriction was removed/discussed but may not have been implemented yet.

## Pending work

Two things were agreed on but not yet implemented:

1. **Lift the `--scale` restriction** — remove `choices=[2, 4]` from argparse so arbitrary values (e.g. `--scale 8`) work. `RealESRGANer.enhance(outscale=N)` already supports any float internally (does 4x AI + Lanczos resize to hit target).

2. **`--passes` flag** — for true multi-pass AI upscaling (e.g. `--scale 4 --passes 2` = 4x AI → 4x AI = 16x total, or `--scale 2 --passes 3` = 8x). Default `1`. Feed the output of each pass back as input to the next.

## Key files

```
~/Development/private/image-enhance/
├── upscale.py           # main script
├── pyproject.toml       # pinned deps
├── README.md            # usage docs (keep in sync with script changes)
├── .venv/               # Python 3.11 uv venv
└── models/
    ├── RealESRGAN_x2plus.pth   # 2x model
    ├── RealESRGAN_x4plus.pth   # 4x model
    └── GFPGANv1.4.pth          # face restoration
```

`gfpgan/weights/` (auto-created on first `--face-enhance` run) holds aux detection models.

## Dependency pins — DO NOT change

```
torch==2.0.1
torchvision==0.15.2
numpy<2
```
These are pinned due to `basicsr` compatibility. Upgrading any of them breaks the import chain.

## CLI flags (current)

| Flag | Default | Notes |
|------|---------|-------|
| `--scale` | `2` | Currently restricted to `2\|4` — pending: lift restriction |
| `--texture-strength` | `0.0` | 1.0=original texture, <1 softer, >1 sharper. Use 1.0–1.5 for photos with fine skin detail |
| `--face-enhance` | off | GFPGAN on top of Real-ESRGAN |
| `--face-weight` | `0.5` | GFPGAN blend. Lower = more original skin texture |
| `--model` | auto | `realesrgan-x4plus` (4x) or `realesrgan-x2plus` (2x) |

## Context on texture-strength

Real-ESRGAN over-smooths fine texture (wrinkles, skin detail) — it treats them as noise.
`--texture-strength` fixes this by: Lanczos-upscaling the original → extracting high-frequency detail via Gaussian high-pass → adding it back onto the AI output at the given strength.
`1.5` was too sharp for the test image (surgeon portrait); `1.0`–`1.2` was the sweet spot.

## Run command (activate venv first)

```bash
cd ~/Development/private/image-enhance
source .venv/bin/activate
python upscale.py ~/Downloads/input.png ~/Downloads/output.png --scale 2 --texture-strength 1.2
```
