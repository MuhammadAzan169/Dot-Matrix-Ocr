"""
Generates synthetic dot-matrix test plates with known ground truth.

Real sample images are scarce and unlabelled, which makes it hard to tell a
pipeline regression from a bad photo. These plates are built to exercise every
stage of backend/app.py deliberately:

  * dots, not strokes          -> the connected-components + DBSCAN stages
  * uneven lighting            -> adaptive_illumination_correction
  * a few degrees of rotation  -> the minAreaRect deskew
  * wide gaps between digits   -> find_vertical_separation_lines
  * brushed-metal noise        -> the area filters that reject speckle

Dot geometry is chosen to sit inside the thresholds ImageProcessor uses:
a radius-4 dot has a bbox area of ~81 (limits are 20..650) and a 12 px pitch
keeps neighbours inside connection_radius=22.

    python generate_test_image.py                  # the default plate
    python generate_test_image.py --text 8675309
    python generate_test_image.py --all            # the full difficulty set
"""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent

# Classic 5x7 dot-matrix font, the kind used by industrial dot-peen markers.
FONT_5X7 = {
    "0": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
    "3": ["11111", "00010", "00100", "00010", "00001", "10001", "01110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
    "6": ["00110", "01000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00010", "01100"],
}

PITCH = 12       # centre-to-centre spacing of dots
DOT_RADIUS = 4   # bbox area ~81, inside the 20..650 filter
GAP_COLS = 2     # blank dot-columns between characters -> ~24 px gap


def render_dots(text: str) -> tuple[np.ndarray, tuple[int, int]]:
    """Draw the text as a clean white-on-black dot mask."""
    for ch in text:
        if ch not in FONT_5X7:
            raise SystemExit(f"error: no glyph for {ch!r} — digits 0-9 only")

    cols = len(text) * 5 + (len(text) - 1) * GAP_COLS
    margin = PITCH * 3
    w = cols * PITCH + margin * 2
    h = 7 * PITCH + margin * 2

    mask = np.zeros((h, w), np.uint8)
    x_col = 0
    for ch in text:
        for row, bits in enumerate(FONT_5X7[ch]):
            for col, bit in enumerate(bits):
                if bit != "1":
                    continue
                cx = margin + (x_col + col) * PITCH + PITCH // 2
                cy = margin + row * PITCH + PITCH // 2
                # Jitter each dot slightly: a real marker never lands perfectly
                # on the grid, and a perfect grid would be an unfairly easy test.
                cx += np.random.randint(-1, 2)
                cy += np.random.randint(-1, 2)
                radius = DOT_RADIUS + np.random.randint(-1, 1)
                cv2.circle(mask, (cx, cy), radius, 255, -1)
        x_col += 5 + GAP_COLS

    return mask, (w, h)


def make_plate(
    text: str,
    angle: float = 3.5,
    lighting: float = 0.55,
    noise: float = 6.0,
    blur: int = 3,
) -> np.ndarray:
    """Composite the dot mask onto a noisy, unevenly lit metal surface."""
    mask, (w, h) = render_dots(text)

    # Brushed metal: mid-grey with horizontal streaks.
    plate = np.full((h, w), 95, np.float32)
    streaks = np.random.normal(0, 4, (h, 1)).astype(np.float32)
    plate += streaks
    plate += np.random.normal(0, noise, (h, w)).astype(np.float32)

    # Engraved dots catch the light: brighter than the surface, not uniform.
    dot_brightness = np.random.normal(205, 12, (h, w)).astype(np.float32)
    plate = np.where(mask > 0, dot_brightness, plate)

    # A diagonal falloff so one corner is much darker than the other. This is
    # the whole reason adaptive_illumination_correction exists; a flatly lit
    # plate would never test it.
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    ramp = (xs / w) * 0.65 + (ys / h) * 0.35
    plate *= (1.0 - lighting) + lighting * (1.15 - ramp)

    plate = np.clip(plate, 0, 255).astype(np.uint8)
    if blur:
        plate = cv2.GaussianBlur(plate, (blur, blur), 0)

    # Rotate so the deskew stage has something to correct. Border replication
    # avoids black corners, which would skew the illumination estimate.
    if angle:
        centre = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(centre, angle, 1.0)
        plate = cv2.warpAffine(plate, M, (w, h), flags=cv2.INTER_CUBIC,
                               borderMode=cv2.BORDER_REPLICATE)

    return cv2.cvtColor(plate, cv2.COLOR_GRAY2BGR)


# name -> (text, kwargs). Ordered easy to hard.
VARIANTS = {
    "easy":     ("123456", dict(angle=0.0, lighting=0.15, noise=3.0, blur=3)),
    "default":  ("8675309", dict(angle=3.5, lighting=0.55, noise=6.0, blur=3)),
    "skewed":   ("4090217", dict(angle=-7.0, lighting=0.45, noise=6.0, blur=3)),
    "dim":      ("5551234", dict(angle=2.0, lighting=0.80, noise=9.0, blur=5)),
    "noisy":    ("9081726", dict(angle=1.5, lighting=0.50, noise=16.0, blur=3)),
}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--text", help="digits to render (0-9)")
    ap.add_argument("--out", type=Path, help="output path")
    ap.add_argument("--all", action="store_true", help="write the full difficulty set")
    ap.add_argument("--seed", type=int, default=7, help="RNG seed (default: 7)")
    args = ap.parse_args()

    np.random.seed(args.seed)

    if args.all:
        for name, (text, kw) in VARIANTS.items():
            out = HERE / f"sample_{name}_{text}.jpg"
            cv2.imwrite(str(out), make_plate(text, **kw), [cv2.IMWRITE_JPEG_QUALITY, 92])
            print(f"{out.name:32} ground truth: {text}")
        return

    text, kw = VARIANTS["default"]
    text = args.text or text
    out = args.out or HERE / f"sample_default_{text}.jpg"
    cv2.imwrite(str(out), make_plate(text, **kw), [cv2.IMWRITE_JPEG_QUALITY, 92])
    print(f"{out.name:32} ground truth: {text}")


if __name__ == "__main__":
    main()
