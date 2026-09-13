# Test plates

Synthetic dot-matrix plates with the answer in the filename
(`sample_<variant>_<digits>.jpg`). Real sample photos are scarce and
unlabelled, which makes it impossible to tell a pipeline regression from a bad
photo — these are labelled by construction.

| Variant   | Digits    | What it stresses                                   |
| --------- | --------- | -------------------------------------------------- |
| `easy`    | 123456    | Flat lighting, no skew — the sanity baseline        |
| `default` | 8675309   | 3.5° skew, strong diagonal falloff — the normal case |
| `skewed`  | 4090217   | -7° rotation — the deskew stage                     |
| `dim`     | 5551234   | Heavy falloff + blur — illumination correction      |
| `noisy`   | 9081726   | Coarse surface grain — the area/DBSCAN filters      |

## Use

```bash
python generate_test_image.py --all        # regenerate (seeded, reproducible)
python generate_test_image.py --frontend-samples   # the UI's demo plates
python generate_test_image.py --text 4815162342
python run_pipeline.py                     # dump all 7 stages per plate
```

`run_pipeline.py` needs no API key and makes no network calls: it stops at
`7_final.png`, the reconstructed image that would be sent to the vision model.
That is the one to look at — if the digits are not legible there, no model will
read them. Output lands in `_pipeline_out/` (git-ignored).

To test the OCR step too, upload a plate through the running app.

## The frontend's demo plates

`--frontend-samples` writes three photo-realistic plates into
`frontend/samples/`, which the UI offers to visitors who have no image of their
own. They add what a phone camera really introduces — perspective, vignetting,
surface curvature, scratches — on top of the same dot rendering.

They are upscaled 1.3x and no more, for a concrete reason: `ImageProcessor`
clusters dots with a fixed `eps=50, min_samples=8`, so dot pitch cannot grow
without bound. At 1.6x the pitch reached ~19 px, every dot fell below
`min_samples`, and the steel-plate sample was rejected as pure noise. Worth
remembering if a real high-resolution photo ever returns "no clusters" —
downscaling it is the fix.

## Why the dots are sized the way they are

`generate_test_image.py` matches the thresholds in `ImageProcessor`: a
radius-4 dot has a bbox area of ~81 (the filter accepts 20–650), and the 12 px
pitch keeps neighbouring dots inside `connection_radius=22` so the tapered-line
step can join them. Change those constants in `app.py` and these plates stop
being representative.

## Found with these

The deskew passed `np.where` output — `(row, col)` — straight into
`cv2.minAreaRect`, which expects `(x, y)`. The transposition measured the text
box on its side, so `sample_skewed` came out rotated 90°. Small skews happened
to survive it, which is why it went unnoticed. The `angle < -45` branch was
also dead code: OpenCV ≥ 4.5 returns an angle in `(0, 90]`.
