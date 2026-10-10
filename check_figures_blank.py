"""Verify F2a/F2b actually render as visually-meaningful surfaces, not near-blank
monochrome blobs (the exact failure mode run #1's figures had and the user called
out). Check by loading each PNG and measuring per-pixel color variance in the
main data region (excluding the colorbar and margins). If a panel's pixel data
is effectively one solid color, that panel is 'near-blank by bad scaling' and
must be regenerated with a self-normalized colormap range.
"""
import sys
sys.path.insert(0, r"E:\agh-test")
from PIL import Image
import numpy as np
import os

d = r"E:\agh-test\program-design\runtime\figures_2013A_jupiter_flyby_run2"
for f in ["F1_delta_vs_perigee_head_on.png", "F2a_saving_surface_head_on.png",
          "F2b_saving_surface_overtaking.png", "F3_chained_staircase.png"]:
    p = os.path.join(d, f)
    img = np.array(Image.open(p).convert("RGB"))
    h, w, _ = img.shape
    # Take a central crop (avoid margins/axes/labels), just the data area
    crop = img[int(h*0.15):int(h*0.85), int(w*0.05):int(w*0.95)]
    # A near-blank region = very low per-pixel std dev across all channels
    overall_std = crop.std(axis=(0, 1)).max()
    # Count how many distinct colors there are (a real surface/plot has many;
    # a near-blank one has very few)
    flat = crop.reshape(-1, 3)
    distinct = len(np.unique(flat, axis=0))
    print(f"{f}: shape={img.shape}  crop-pixel-std(max channel)={overall_std:.1f}  distinct-colors={distinct}")
    if distinct < 40:
        print(f"  !! WARN: only {distinct} distinct colors - this panel is effectively near-blank "
              f"(solid-color blob), same failure mode as run #1. Needs a self-normalized colormap.")
