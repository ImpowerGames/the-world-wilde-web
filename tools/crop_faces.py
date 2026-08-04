#!/usr/bin/env python3
"""Re-fetch each portrait larger and crop it to the sitter's face.

Node portraits are shown at about 40px, so a full-plate photograph reduces the face to a smudge.
This pulls a 900px version from Commons, finds the face with OpenCV's Haar cascades, and crops a
square around it.

    python tools/crop_faces.py            crop anything not already done
    python tools/crop_faces.py --force    redo everything
    python tools/crop_faces.py --report   just say what was detected, change nothing

Detection uses YuNet, the small DNN face detector OpenCV ships with (OpenCV 5 dropped the old Haar
cascade API). The model is ~340 KB and is downloaded on first run into tools/models/, which is
gitignored — you only need it if you are re-cropping.

It still misses some: a profile, a heavy shadow, a painted portrait rather than a photograph. A
miss falls back to a top-biased square, which is a fair guess for a studio portrait, and is
recorded in portraits/credits.json as face_detected=false so those can be checked by eye.

Requires: opencv-python, pillow, numpy.
"""
import argparse
import json
import sys
import time
import urllib.request
from pathlib import Path

try:
    import cv2
    import numpy as np
    from PIL import Image
except ImportError as e:
    sys.exit(f"missing a dependency ({e}). pip install opencv-python pillow numpy")

ROOT = Path(__file__).resolve().parent.parent
POR = ROOT / "portraits"
OUT_PX = 256          # stored size; nodes render at ~40px, retina and zoom want the headroom
FETCH_PX = 800        # Commons only serves a fixed set of thumbnail widths; 800 is one
PAD = 1.55            # of the detected face box: >1 keeps hair, chin and some shoulder
UA = {"User-Agent": "WildeCircleWeb/0.1 (scholarly relationship map; "
                    "https://github.com/lovelle-cardoso; non-commercial research use)"}


def big_url(commons_file: str):
    """Ask Commons for a large thumbnail URL.

    Rewriting the width inside an existing thumbnail URL does not work — the server only serves a
    fixed set of sizes and answers anything else with HTTP 400 — so let the API mint the URL.
    """
    import urllib.parse
    api = ("https://commons.wikimedia.org/w/api.php?action=query&format=json&prop=imageinfo"
           f"&iiprop=url&iiurlwidth={FETCH_PX}&titles="
           + urllib.parse.quote("File:" + commons_file))
    try:
        r = json.loads(urllib.request.urlopen(
            urllib.request.Request(api, headers=UA), timeout=45).read().decode("utf-8"))
        for _, pg in r.get("query", {}).get("pages", {}).items():
            ii = pg.get("imageinfo")
            if ii:
                return ii[0].get("thumburl") or ii[0].get("url")
    except Exception as e:
        print(f"    (could not ask Commons for a larger copy: {e})")
    return None


MODEL_URL = ("https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/"
             "face_detection_yunet_2023mar.onnx")
MODEL = ROOT / "tools" / "models" / "face_detection_yunet_2023mar.onnx"
_det = None


def detector(w, h):
    """YuNet, fetched once. Threshold is deliberately low: these are soft, low-contrast
    photographs and a weak hit still beats a blind centre crop."""
    global _det
    if not MODEL.exists():
        MODEL.parent.mkdir(parents=True, exist_ok=True)
        print(f"fetching the face model once ({MODEL.name}) …")
        MODEL.write_bytes(urllib.request.urlopen(
            urllib.request.Request(MODEL_URL, headers=UA), timeout=120).read())
    if _det is None:
        _det = cv2.FaceDetectorYN.create(str(MODEL), "", (w, h), 0.5, 0.3, 5000)
    _det.setInputSize((w, h))
    return _det


def detect(img_bgr):
    """Best face box as (x, y, w, h), or None."""
    h, w = img_bgr.shape[:2]
    try:
        _, faces = detector(w, h).detect(img_bgr)
    except Exception as e:
        print(f"    (detector error: {e})")
        return None
    if faces is None or not len(faces):
        return None
    # largest first; among equals prefer the higher one, since group plates put the sitter big
    best = sorted(faces, key=lambda f: (f[2] * f[3], -f[1]))[-1]
    x, y, fw, fh = (int(v) for v in best[:4])
    return (x, y, fw, fh)


def square(img, box):
    """A square crop around the face, clamped to the image."""
    H, W = img.shape[:2]
    if box is None:
        side = min(W, H)
        x = (W - side) // 2
        y = int((H - side) * 0.12)          # bias up: heads sit above centre in a portrait
        return img[y:y + side, x:x + side], False
    x, y, w, h = box
    side = int(max(w, h) * PAD)
    cx, cy = x + w // 2, y + int(h * 0.46)  # a little above the box centre, to keep hair
    side = min(side, W, H)
    x0 = max(0, min(W - side, cx - side // 2))
    y0 = max(0, min(H - side, cy - side // 2))
    return img[y0:y0 + side, x0:x0 + side], True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()

    credits = json.loads((POR / "credits.json").read_text(encoding="utf-8"))
    hits = misses = skipped = 0
    for pid, c in sorted(credits.items()):
        dest = POR / Path(c["file"]).name
        if c.get("cropped") and not args.force and not args.report:
            skipped += 1
            continue
        url = big_url(c.get("source_file") or "")
        raw = None
        if url:
            try:
                raw = urllib.request.urlopen(
                    urllib.request.Request(url, headers=UA), timeout=60).read()
                time.sleep(0.8)
            except Exception as e:
                print(f"  {pid}: fetch failed ({e}); using the copy on disk")
        data = raw if raw else (dest.read_bytes() if dest.exists() else None)
        if not data:
            print(f"  {pid}: nothing to work from")
            continue
        arr = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
        if arr is None:
            print(f"  {pid}: could not decode")
            continue
        box = detect(arr)
        if args.report:
            print(f"  {pid:20} {'face found' if box is not None else 'NO FACE - will centre-crop'}")
            hits += box is not None
            misses += box is None
            continue
        crop, found = square(arr, box)
        crop = cv2.resize(crop, (OUT_PX, OUT_PX), interpolation=cv2.INTER_AREA)
        Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)).save(dest, quality=88, optimize=True)
        c["cropped"] = True
        c["face_detected"] = bool(found)
        hits += found
        misses += not found
    if not args.report:
        (POR / "credits.json").write_text(json.dumps(credits, ensure_ascii=False, indent=1) + "\n",
                                          encoding="utf-8")
    total = sum(p.stat().st_size for p in POR.glob("*") if p.suffix in (".jpg", ".png"))
    print(f"\nface found: {hits} · centre-cropped fallback: {misses}"
          + (f" · already done: {skipped}" if skipped else "")
          + (f"\nportraits now {total/1024:.0f} KB" if not args.report else ""))


main()
