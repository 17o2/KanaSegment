# -*- coding: utf-8 -*-
from collections import namedtuple
from pathlib import Path
from PIL import Image, ImageDraw, ImageColor
from ruamel.yaml import YAML

Kana = namedtuple("Kana", "romaji kana position supported segments")

# User config --------------------------------------------------------------------------
source = "designs/v0/v0.chars.txt"  # also requires *.seg.txt and *.seg.png

# Initialization -----------------------------------------------------------------------
kanalist = []
segment_coords = []
segment_stats = []

fn = Path(source)
fn = fn.parent / fn.stem.split(".")[0]  # https://stackoverflow.com/a/31890400/13739103
file_charlist = fn.parent / (fn.stem + ".chars.txt")
file_seglist = fn.parent / (fn.stem + ".seg.txt")
file_segimg = fn.parent / (fn.stem + ".seg.png")
file_config = fn.parent / (fn.stem + ".cfg.yml")
dir_out = Path(fn.parent / "output")
dir_out.mkdir(parents=True, exist_ok=True)

# Read list of kana and corresponding segments -----------------------------------------
with open(file_charlist, "r", encoding="utf-8") as f:
    for idx, line in enumerate(f):
        line = line.strip()
        if line == "":
            continue
        lineitems = [l for l in line.split(" ") if l]
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

# Load segment description file --------------------------------------------------------
with open(file_seglist, "r", encoding="utf-8") as f:
    for line in f:
        _coords = line.split(",")
        coords = tuple([int(c.strip()) for c in _coords])
        segment_coords.append(coords)
segment_stats = [0 for _ in segment_coords]

# Load color config --------------------------------------------------------------------
yaml = YAML(typ="safe")
with open(file_config, "r", encoding="utf-8") as f:
    config = yaml.load(f)
color_bg_in = (255, 255, 255)  # hardcoded
color_annotation = (0, 0, 0)  # hardcoded

if isinstance(config["colors"], dict):
    print("one color config")
    variants = [config["colors"]]
    variants[0]["name"] = ""  # empty name if only one color config found
elif isinstance(config["colors"], list):
    variants = config["colors"]


# Prepare for image generation ---------------------------------------------------------
img_template = Image.open(file_segimg).convert("RGB")
tile_size = Image.open(file_segimg).convert("RGB").size
num_tiles = (5, (max([k.position for k in kanalist_supported]) - 1) // 5 + 1)
overview_size = tuple([n * m for n, m in zip(tile_size, num_tiles)])

for variant in variants:
    variant["img_tile"] = Image.new("RGB", overview_size)
    img_tile = variant["img_tile"]
    ImageDraw.floodfill(img_tile, (0, 0), tuple(variant["background"]))

# Generate segment images for each kana ------------------------------------------------
print("Supported:   ", end="")
for kana in kanalist_supported:
    print(kana.kana, end="")
    img_kana = img_template.copy()
    pixdata = img_kana.load()
    # remove annotations
    for y in range(tile_size[1]):
        for x in range(tile_size[0]):
            if pixdata[x, y] == color_annotation:
                pixdata[x, y] = color_bg_in
    # color segments accordingly
    for i_var, variant in enumerate(variants):
        img_tile = variant["img_tile"]

        for _i, seg in enumerate(segment_coords):
            idx = _i + 1
            if idx in kana.segments:
                ImageDraw.floodfill(img_kana, seg, tuple(variant["active"]))
                if i_var == 0:
                    segment_stats[_i] = segment_stats[_i] + 1
            else:
                ImageDraw.floodfill(img_kana, seg, tuple(variant["inactive"]))
        # color background
        for y in range(tile_size[1]):
            for x in range(tile_size[0]):
                if pixdata[x, y] == color_bg_in:
                    pixdata[x, y] = tuple(variant["background"])

        if variant["name"] == "":
            variant_name = ""
        else:
            variant_name = "." + variant["name"]
        img_kana.save(
            dir_out / f"{kana.position:02d}_{kana.romaji}{variant_name}.png", "PNG"
        )

        tile_coords = (
            tile_size[0] * ((kana.position - 1) % num_tiles[0]),
            tile_size[1] * ((kana.position - 1) // num_tiles[0]),
        )
        img_tile.paste(img_kana, tile_coords)
print()
print("Unsupported: ", end="")
for kana in kanalist:
    if not kana.supported:
        print(kana.kana, end="")
print()

# Generate overview image --------------------------------------------------------------
for variant in variants:
    img_tile = variant["img_tile"]

    if variant["name"] == "":
        variant_name = ""
    else:
        variant_name = "." + variant["name"]

    img_tile.save(dir_out / f"00_overview{variant_name}.png", "PNG")
