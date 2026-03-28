#!/usr/bin/env python3
"""
AI image upscaler using Real-ESRGAN + optional GFPGAN face restoration.
Supports texture preservation via frequency blending.
Runs on Apple Metal (MPS), CUDA, or CPU.
Usage: python upscale.py <input> [output] [--scale 2|4] [--face-enhance] [--texture-strength 0.0-2.0]
"""
import argparse
from pathlib import Path

import numpy as np
import torch
import cv2
from basicsr.archs.rrdbnet_arch import RRDBNet
from realesrgan import RealESRGANer

MODELS_DIR = Path(__file__).parent / "models"

MODEL_CONFIGS = {
    "realesrgan-x4plus": {"filename": "RealESRGAN_x4plus.pth", "num_block": 23, "scale": 4},
    "realesrgan-x2plus": {"filename": "RealESRGAN_x2plus.pth", "num_block": 23, "scale": 2},
}


def get_model_path(filename: str) -> Path:
    path = MODELS_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Model not found: {path}\nPlace the .pth file in models/")
    return path


def get_device() -> str:
    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def build_upsampler(config: dict, device: str) -> RealESRGANer:
    model = RRDBNet(
        num_in_ch=3, num_out_ch=3, num_feat=64,
        num_block=config["num_block"], num_grow_ch=32, scale=config["scale"],
    )
    return RealESRGANer(
        scale=config["scale"],
        model_path=str(get_model_path(config["filename"])),
        model=model,
        tile=512, tile_pad=10, pre_pad=0, half=False,
        device=device,
    )


def build_face_enhancer(upsampler: RealESRGANer, device: str):
    from gfpgan import GFPGANer
    return GFPGANer(
        model_path=str(get_model_path("GFPGANv1.4.pth")),
        upscale=upsampler.scale,
        arch="clean",
        channel_multiplier=2,
        bg_upsampler=upsampler,
        device=device,
    )


def blend_texture(ai_output: np.ndarray, original_upscaled: np.ndarray,
                  strength: float, blur_sigma: float = 2.0) -> np.ndarray:
    """Add high-frequency texture from the original (Lanczos-upscaled) onto the AI output.
    Extracts fine detail (wrinkles, grain) from original and injects it at given strength."""
    ai_f = ai_output.astype(np.float32)
    orig_f = original_upscaled.astype(np.float32)
    orig_blur = cv2.GaussianBlur(orig_f, (0, 0), blur_sigma)
    high_freq = orig_f - orig_blur
    return np.clip(ai_f + high_freq * strength, 0, 255).astype(np.uint8)


def upscale(input_path: str, output_path: str, scale: int = 2, model_name: str = None,
            face_enhance: bool = False, face_weight: float = 0.5,
            texture_strength: float = 0.0):
    if model_name is None:
        model_name = "realesrgan-x4plus" if scale == 4 else "realesrgan-x2plus"

    config = MODEL_CONFIGS[model_name]
    device = get_device()
    print(f"Device: {device} | Scale: {scale}x | Face enhance: {face_enhance}"
          + (f" (weight={face_weight})" if face_enhance else "")
          + (f" | Texture blend: {texture_strength}" if texture_strength > 0 else ""))

    upsampler = build_upsampler(config, device)

    img = cv2.imread(input_path, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ValueError(f"Could not read image: {input_path}")

    h, w = img.shape[:2]
    print(f"Input:  {w}x{h}")

    if face_enhance:
        enhancer = build_face_enhancer(upsampler, device)
        _, _, output = enhancer.enhance(
            img, has_aligned=False, only_center_face=False,
            paste_back=True, weight=face_weight,
        )
    else:
        output, _ = upsampler.enhance(img, outscale=scale)

    if texture_strength > 0:
        target_h, target_w = output.shape[:2]
        original_upscaled = cv2.resize(img, (target_w, target_h), interpolation=cv2.INTER_LANCZOS4)
        output = blend_texture(output, original_upscaled, strength=texture_strength)
        print(f"Texture blended at strength={texture_strength}")

    oh, ow = output.shape[:2]
    print(f"Output: {ow}x{oh}")

    cv2.imwrite(output_path, output)
    print(f"Saved:  {output_path}")


def main():
    parser = argparse.ArgumentParser(description="AI image upscaler (Real-ESRGAN + optional GFPGAN)")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", help="Output path (default: <input>_upscaled.png)")
    parser.add_argument("--scale", type=int, default=2, choices=[2, 4], help="Upscale factor (default: 2)")
    parser.add_argument("--model", choices=list(MODEL_CONFIGS.keys()), help="Override model selection")
    parser.add_argument("--face-enhance", action="store_true", help="Run GFPGAN face restoration on top of upscale")
    parser.add_argument("--face-weight", type=float, default=0.5,
                        help="GFPGAN blend strength 0.0–1.0 (default: 0.5). Lower = more original texture")
    parser.add_argument("--texture-strength", type=float, default=0.0,
                        help="Inject original high-frequency texture back (0.0=off, 1.0=normal, 1.5–2.0=strong). "
                             "Fixes wrinkle/detail loss caused by AI over-smoothing")
    args = parser.parse_args()

    if args.output:
        output_path = args.output
    else:
        p = Path(args.input)
        output_path = str(p.parent / f"{p.stem}_upscaled{p.suffix}")

    upscale(args.input, output_path, scale=args.scale, model_name=args.model,
            face_enhance=args.face_enhance, face_weight=args.face_weight,
            texture_strength=args.texture_strength)


if __name__ == "__main__":
    main()
