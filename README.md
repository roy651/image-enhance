# image-enhance

Local AI image upscaling and face restoration. Runs on Apple Metal (MPS), CUDA, or CPU.

## Setup

```bash
cd ~/Development/private/image-enhance
uv sync
source .venv/bin/activate
```

## Usage

```bash
python upscale.py <input> [output] [--scale 2|4] [--texture-strength N] [--face-enhance]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--scale` | `2` | Upscale factor — `2` (2x) or `4` (4x) |
| `--texture-strength` | `0.0` | Re-injects original high-frequency detail (wrinkles, fine texture) lost to AI smoothing. `1.0` = original texture as-is, `<1.0` = softer, `>1.0` = sharper. Start at `1.0`–`1.5`, back off if too harsh |
| `--face-enhance` | off | Run GFPGAN face restoration on top of upscale. Sharpens eyes/features but may over-smooth skin — combine with `--texture-strength` to compensate |
| `--face-weight` | `0.5` | GFPGAN blend strength 0.0–1.0. Lower = more original texture, higher = more AI restoration |
| `--model` | auto | Override model: `realesrgan-x4plus` or `realesrgan-x2plus` |

**Recommended (portraits, 4K output):**
```bash
python upscale.py input.png output.png --scale 4 --texture-strength 1.0
```
Real-ESRGAN alone with texture blending gives the best results for portraits — faces stay sharp without over-smoothing skin and wrinkles. `--face-enhance` (GFPGAN) tends to over-smooth and isn't recommended unless faces are heavily degraded.

**Examples:**
```bash
# 2x upscale, preserving original skin/wrinkle texture
python upscale.py input.png output.png --scale 2 --texture-strength 1.2

# Too sharp? Tone it down
python upscale.py input.png output.png --scale 2 --texture-strength 0.8

# Face image: upscale + face sharpening + texture preservation
# Note: GFPGAN may over-smooth fine detail; lower --face-weight or skip if unwanted
python upscale.py input.png output.png --scale 4 --face-enhance --face-weight 0.3 --texture-strength 1.0
```

Output defaults to `<input>_upscaled.png` in the same directory.

## Models

All `.pth` files live in `models/`. Required files:

| File | Used for |
|------|----------|
| `RealESRGAN_x2plus.pth` | `--scale 2` (default) |
| `RealESRGAN_x4plus.pth` | `--scale 4` |
| `GFPGANv1.4.pth` | `--face-enhance` |

On first `--face-enhance` run, two face-detection auxiliary models (~185MB total) are auto-downloaded to `gfpgan/weights/`.

## Notes

- No CUDA needed — runs natively on Apple Silicon via Metal (MPS)
- Dependency pinning is critical: `torch==2.0.1`, `torchvision==0.15.2`, `numpy<2` — do not upgrade these
- The AI upscaler (Real-ESRGAN) tends to smooth fine skin texture. Use `--texture-strength` to recover it
