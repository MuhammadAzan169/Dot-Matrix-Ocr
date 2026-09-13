"""
Renders the pipeline stages as documentation images for the README.

Every stage the API returns is written to docs/pipeline/ at a fixed width, so
the README can show what each step actually does rather than describe it.

    python make_pipeline_docs.py                      # uses the gas-cylinder sample
    python make_pipeline_docs.py --source ../../frontend/samples/worn-part.jpg
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
ROOT = BACKEND.parent
DOCS = ROOT / "docs" / "pipeline"

# (file the pipeline writes, name in docs/, what it shows)
STAGES = [
    ("1_original.png",     "1-original.png",     "the photo as uploaded"),
    ("2_illumination.png", "2-illumination.png", "illumination corrected"),
    ("3_thresholded.png",  "3-threshold.png",    "binary threshold"),
    ("4_clustered.png",    "4-clusters.png",     "connected components kept"),
    ("5_dbscan.png",       "5-dbscan.png",       "DBSCAN, speckle dropped"),
    ("6_deskewed.png",     "6-deskewed.png",     "deskewed and cropped"),
    ("7_final.png",        "7-final.png",        "dots joined, sent to the model"),
]

DOC_WIDTH = 720  # wide enough to read, small enough to keep the repo light


def load_backend():
    spec = importlib.util.spec_from_file_location("backend_app", BACKEND / "app.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path,
                    default=ROOT / "frontend" / "samples" / "gas-cylinder.jpg")
    args = ap.parse_args()

    logging.disable(logging.CRITICAL)
    app = load_backend()

    work = HERE / "_pipeline_out" / "_docs"
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    shutil.copy(args.source, work / "1_original.png")

    app.AdaptiveDotMatrixOCR().process_illumination(
        work / "1_original.png", work / "2_illumination.png"
    )
    if app.ImageProcessor().process_image(work / "2_illumination.png", work)[0] is None:
        raise SystemExit(f"pipeline produced nothing for {args.source}")

    DOCS.mkdir(parents=True, exist_ok=True)
    for src_name, doc_name, caption in STAGES:
        img = cv2.imread(str(work / src_name))
        if img is None:
            raise SystemExit(f"missing stage output: {src_name}")
        h, w = img.shape[:2]
        if w != DOC_WIDTH:
            img = cv2.resize(img, (DOC_WIDTH, max(1, round(h * DOC_WIDTH / w))),
                             interpolation=cv2.INTER_AREA)
        out = DOCS / doc_name
        cv2.imwrite(str(out), img, [cv2.IMWRITE_PNG_COMPRESSION, 9])
        print(f"  {doc_name:22} {img.shape[1]}x{img.shape[0]:<4} "
              f"{out.stat().st_size / 1024:5.0f} KB  {caption}")

    shutil.rmtree(work, ignore_errors=True)
    print(f"\nWrote {len(STAGES)} stages to {DOCS.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
