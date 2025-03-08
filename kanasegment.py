# -*- coding: utf-8 -*-
from collections import namedtuple
from pathlib import Path
from PIL import Image, ImageDraw, ImageColor

Kana = namedtuple("Kana", "romaji kana position supported segments")

source = "designs/v0/v0.chars.txt"  # also requires *.seg.txt and *.seg.png

color_bg = (255, 255, 255)
color_annotation = (0, 0, 0)
color_on = (255, 0, 0)
color_off = (200, 200, 200)

kanalist = []
segment_coords = []
segment_stats = []

fn = Path(source)
fn = fn.parent / fn.stem.split(".")[0]  # https://stackoverflow.com/a/31890400/13739103
file_charlist = fn.parent / (fn.stem + ".chars.txt")
file_seglist = fn.parent / (fn.stem + ".seg.txt")
file_segimg = fn.parent / (fn.stem + ".seg.png")
dir_out = Path(fn.parent / "output")
dir_out.mkdir(parents=True, exist_ok=True)

with open(file_charlist, "r", encoding="utf-8") as f:
    for idx, line in enumerate(f):
        line = line.strip()
        if line == "":
            continue
        lineitems = line.split("\t")
        romaji = lineitems[0]
        kana = lineitems[1]
        if len(lineitems) > 2:  # kana has coordinates -> kana is supported
            supported = True
            segments = [int(s) for s in lineitems[2].split(",")]
        else:
            supported = False
            segments = []
        kanalist.append(Kana(romaji, kana, idx + 1, supported, segments))
num_total = len(kanalist)
num_supported = len([k for k in kanalist if k.supported])
print(
    f"{num_supported} of {num_total} kana supported: "
    f"{round(num_supported/num_total*100,1)}% coverage"
)
kanalist_supported = [k for k in kanalist if k.supported]

with open(file_seglist, "r", encoding="utf-8") as f:
    for line in f:
        _coords = line.split(",")
        coords = tuple([int(c.strip()) for c in _coords])
        segment_coords.append(coords)
segment_stats = [0 for _ in segment_coords]

for kana in kanalist_supported:
    print(kana.kana, end="")
    img = Image.open(file_segimg).convert("RGB")
    pixdata = img.load()
    # remove annotations
    for y in range(img.size[1]):
        for x in range(img.size[0]):
            if pixdata[x, y] == color_annotation:
                pixdata[x, y] = color_bg
    # color segments accordingly
    for _i, seg in enumerate(segment_coords):
        idx = _i + 1
        if idx in kana.segments:
            ImageDraw.floodfill(img, seg, color_on)
            segment_stats[_i] = segment_stats[_i] + 1
        else:
            ImageDraw.floodfill(img, seg, color_off)

    img.save(dir_out / f"{kana.position:02d}_{kana.romaji}.png", "PNG")
print()

# print(segment_stats)
