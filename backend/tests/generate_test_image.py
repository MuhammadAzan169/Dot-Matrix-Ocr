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


# ---------------------------------------------------------------------------
# Photo-realistic samples for the frontend "try one of these" strip.
#
# The plates above are deliberately clean test fixtures. These add the things a
# phone camera actually introduces — perspective, vignetting, surface curvature,
# scratches, JPEG softness — so a first-time visitor sees the tool handle a
# picture that looks like one they would have taken themselves.
# ---------------------------------------------------------------------------


def add_scratches(img: np.ndarray, count: int = 40) -> np.ndarray:
    """Fine tool marks across the surface, the way machined metal really looks.

    Drawn onto their own layer and blended back at low opacity. Painting them
    straight onto the plate produced bright hairlines that cut across the digits
    and looked like a graphics bug rather than brushed steel.
    """
    h, w = img.shape[:2]
    layer = img.copy()
    for _ in range(count):
        x1 = np.random.randint(-w // 6, w)
        y1 = np.random.randint(0, h)
        length = np.random.randint(w // 12, w // 4)
        drift = np.random.randint(-2, 3)
        # Stay close to the surface tone: real brush marks are a shade lighter
        # or darker than the metal, never a bright white line.
        shade = int(np.clip(np.random.normal(0, 1) * 10 + 100, 70, 135))
        cv2.line(layer, (x1, y1), (x1 + length, y1 + drift), shade, 1, cv2.LINE_AA)

    out = cv2.addWeighted(img, 0.78, layer, 0.22, 0)
    # Never let a scratch dim an engraved dot — the dots are the signal.
    return np.maximum(out, np.where(img > 150, img, 0))


def add_vignette(img: np.ndarray, strength: float = 0.45) -> np.ndarray:
    """Darken the corners the way a phone lens does."""
    h, w = img.shape[:2]
    kx = cv2.getGaussianKernel(w, w * 0.65)
    ky = cv2.getGaussianKernel(h, h * 0.65)
    mask = (ky @ kx.T)
    mask = mask / mask.max()
    return np.clip(img.astype(np.float32) * ((1 - strength) + strength * mask), 0, 255).astype(np.uint8)


def add_curvature(img: np.ndarray, amount: float = 0.35) -> np.ndarray:
    """Brighten a vertical band so the surface reads as a cylinder, like the
    gas-bottle necks this project was trained on."""
    h, w = img.shape[:2]
    xs = np.linspace(-1, 1, w, dtype=np.float32)
    band = np.exp(-(xs ** 2) / 0.25)
    gain = 1.0 + amount * band
    return np.clip(img.astype(np.float32) * gain[None, :], 0, 255).astype(np.uint8)


def add_perspective(img: np.ndarray, tilt: float = 0.06) -> np.ndarray:
    """Mild off-axis angle — a photo taken by hand is never square to the part.
    Kept mild on purpose: the pipeline deskews rotation, not perspective."""
    h, w = img.shape[:2]
    dx, dy = w * tilt, h * tilt
    src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    dst = np.float32([[dx, dy * 0.5], [w - dx * 0.3, 0], [w, h - dy * 0.4], [dx * 0.4, h]])
    M = cv2.getPerspectiveTransform(src, dst)
    return cv2.warpPerspective(img, M, (w, h), flags=cv2.INTER_CUBIC,
                               borderMode=cv2.BORDER_REPLICATE)


def make_photo(text: str, style: str) -> np.ndarray:
    """A plate, weathered and photographed."""
    plate = cv2.cvtColor(make_plate(text, **PHOTO_STYLES[style]["plate"]), cv2.COLOR_BGR2GRAY)
    opts = PHOTO_STYLES[style]

    plate = add_scratches(plate, opts["scratches"])
    if opts["curvature"]:
        plate = add_curvature(plate, opts["curvature"])
    if opts["tilt"]:
        plate = add_perspective(plate, opts["tilt"])
    plate = add_vignette(plate, opts["vignette"])

    # Upscale then re-soften: a phone photo is high resolution but never sharp
    # at the pixel level, and the pipeline should cope with that.
    #
    # 1.3 is deliberate, not arbitrary. ImageProcessor clusters dots with
    # DBSCAN at a fixed eps=50 / min_samples=8, so dot pitch cannot grow without
    # bound: at 1.6 the pitch reached ~19 px, every dot fell below min_samples
    # and the steel-plate sample was rejected as noise. Anything up to ~1.3
    # clears it comfortably on all three styles.
    plate = cv2.resize(plate, None, fx=1.3, fy=1.3, interpolation=cv2.INTER_CUBIC)
    plate = cv2.GaussianBlur(plate, (3, 3), 0)

    colour = cv2.cvtColor(plate, cv2.COLOR_GRAY2BGR)
    # Faint colour cast — raw steel is never neutral grey under real light.
    b, g, r = cv2.split(colour.astype(np.float32))
    colour = cv2.merge([b * opts["cast"][0], g * opts["cast"][1], r * opts["cast"][2]])
    return np.clip(colour, 0, 255).astype(np.uint8)


PHOTO_STYLES = {
    "steel-plate": {
        "digits": "3184627",
        "label": "Steel plate",
        "plate": dict(angle=2.5, lighting=0.50, noise=7.0, blur=3),
        "scratches": 70, "curvature": 0.0, "tilt": 0.05, "vignette": 0.28,
        "cast": (1.02, 1.00, 0.97),
    },
    "gas-cylinder": {
        "digits": "7295140",
        "label": "Gas cylinder",
        "plate": dict(angle=-3.0, lighting=0.60, noise=8.0, blur=3),
        "scratches": 45, "curvature": 0.20, "tilt": 0.03, "vignette": 0.32,
        "cast": (1.05, 0.99, 0.95),
    },
    "worn-part": {
        "digits": "5063918",
        "label": "Worn part",
        "plate": dict(angle=4.5, lighting=0.72, noise=11.0, blur=5),
        "scratches": 95, "curvature": 0.0, "tilt": 0.07, "vignette": 0.36,
        "cast": (0.96, 0.99, 1.04),
    },
}


def write_frontend_samples() -> None:
    """Write the samples the UI offers when a visitor has no photo of their own."""
    dest = HERE.parent.parent / "frontend" / "samples"
    dest.mkdir(parents=True, exist_ok=True)
    for style, opts in PHOTO_STYLES.items():
        img = make_photo(opts["digits"], style)
        out = dest / f"{style}.jpg"
        cv2.imwrite(str(out), img, [cv2.IMWRITE_JPEG_QUALITY, 82])
        kb = out.stat().st_size / 1024
        print(f"  {out.name:20} {opts['label']:14} reads {opts['digits']}  "
              f"{img.shape[1]}x{img.shape[0]}  {kb:.0f} KB")


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
    ap.add_argument("--frontend-samples", action="store_true",
                    help="write the photo-realistic samples the UI offers")
    ap.add_argument("--seed", type=int, default=7, help="RNG seed (default: 7)")
    args = ap.parse_args()

    np.random.seed(args.seed)

    if args.frontend_samples:
        write_frontend_samples()
        return

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
