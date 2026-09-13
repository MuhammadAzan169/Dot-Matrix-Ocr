"""
Runs the sample plates through the image pipeline and dumps every stage.

No API key and no network: this stops at stage 7, the reconstructed image that
would be sent to the vision model. That is the part worth eyeballing — if the
digits are not legible in 7_final.png, no model will read them correctly.

    python run_pipeline.py                 # every sample_*.jpg here
    python run_pipeline.py --keep sample_noisy_9081726.jpg
"""

from __future__ import annotations

import argparse
import importlib.util
import logging
import shutil
from pathlib import Path

import cv2

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent
OUT = HERE / "_pipeline_out"


def load_backend():
    """Import backend/app.py by path — it is not an installed package."""
    spec = importlib.util.spec_from_file_location("backend_app", BACKEND / "app.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("samples", nargs="*", help="specific files (default: all sample_*.jpg)")
    ap.add_argument("--verbose", action="store_true", help="show the backend's own logging")
    args = ap.parse_args()

    if not args.verbose:
        logging.disable(logging.CRITICAL)

    app = load_backend()
    files = [Path(s) for s in args.samples] or sorted(HERE.glob("sample_*.jpg"))
    if not files:
        raise SystemExit("no samples found — run: python generate_test_image.py --all")

    failures = 0
    for src in files:
        session = OUT / src.stem
        shutil.rmtree(session, ignore_errors=True)
        session.mkdir(parents=True)
        shutil.copy(src, session / "1_original.png")

        app.AdaptiveDotMatrixOCR().process_illumination(
            session / "1_original.png", session / "2_illumination.png"
        )
        result = app.ImageProcessor().process_image(session / "2_illumination.png", session)

        final = session / "7_final.png"
        if result[0] is None or not final.exists():
            print(f"  FAIL  {src.name} — pipeline returned nothing")
            failures += 1
            continue

        h, w = cv2.imread(str(final)).shape[:2]
        # A row of digits must come out wider than it is tall. Anything else
        # means the deskew tipped the plate onto its side.
        orientation = "ok" if w > h else "SIDEWAYS"
        if orientation != "ok":
            failures += 1
        # Ground truth is encoded in the filename: sample_<variant>_<digits>.jpg
        truth = src.stem.rsplit("_", 1)[-1]
        print(f"  {orientation:8} {src.name:30} expect {truth:8} -> {final.relative_to(HERE)} ({w}x{h})")

    print(f"\n{len(files) - failures}/{len(files)} plates reconstructed. "
          f"Open the 7_final.png files to check the digits are legible.")
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
