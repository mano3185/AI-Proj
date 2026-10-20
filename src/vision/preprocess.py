"""Computer Vision preprocessing & line segmentation for Eigopop."""

import cv2
import numpy as np
from PIL import Image, ImageOps


def normalize_background(img: Image.Image) -> Image.Image:
    """Auto-detect dark mode/inverted text and invert to black-on-white."""
    gray = img.convert("L")
    arr = np.array(gray)
    mean_val = np.mean(arr)
    # If background is dark (mean brightness < 120), invert colors
    if mean_val < 120:
        return ImageOps.invert(img.convert("RGB"))
    return img.convert("RGB")


def extract_text_lines(img: Image.Image) -> list[Image.Image]:
    """Segment a multi-line screenshot crop into individual text line images.
    Uses horizontal projection profile analysis.
    """
    img_clean = normalize_background(img)
    arr = np.array(img_clean)
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)

    # Otsu thresholding or adaptive binary inversion (text becomes white, background black)
    _, binary = cv2.threshold(gray, 210, 255, cv2.THRESH_BINARY_INV)

    # Horizontal projection profile: sum across each row
    proj = np.sum(binary, axis=1)

    # Find row boundaries where text exists
    in_line = False
    start = 0
    line_slices: list[tuple[int, int]] = []

    for idx, val in enumerate(proj):
        # A row is considered text if at least 1% of its pixels are non-background
        if val > 0 and not in_line:
            in_line = True
            start = max(0, idx - 4)
        elif val == 0 and in_line:
            in_line = False
            end = min(len(proj), idx + 4)
            # Minimum line height filter (ignore stray 2px dots)
            if end - start >= 12:
                line_slices.append((start, end))

    # If in_line at the end of the image
    if in_line:
        end = len(proj)
        if end - start >= 12:
            line_slices.append((start, end))

    # If only 1 line or no lines cleanly detected, return trimmed original image
    if len(line_slices) <= 1:
        return [prepare_single_line(img_clean)]

    # Crop each detected line and trim horizontal whitespace
    line_images = []
    for s, e in line_slices:
        line_crop = img_clean.crop((0, s, img_clean.width, e))
        line_images.append(prepare_single_line(line_crop))

    return line_images


def prepare_single_line(line_img: Image.Image) -> Image.Image:
    """Trim empty horizontal whitespace, upscale if tiny, and add clean border padding."""
    gray = np.array(line_img.convert("L"))
    # Invert so text is bright
    inverted = 255 - gray
    # Horizontal projection to find text left/right bounds
    x_proj = np.sum(inverted > 30, axis=0)
    nonzero_x = np.where(x_proj > 0)[0]

    if len(nonzero_x) > 0:
        x_start = max(0, nonzero_x[0] - 8)
        x_end = min(line_img.width, nonzero_x[-1] + 8)
        # Only crop if it removes significant whitespace
        if x_end - x_start > 10:
            line_img = line_img.crop((x_start, 0, x_end, line_img.height))

    # Upscale if character height is too small (< 40px)
    if line_img.height < 40:
        scale = 45.0 / max(1, line_img.height)
        new_w = int(line_img.width * scale)
        new_h = int(line_img.height * scale)
        line_img = line_img.resize((new_w, new_h), Image.Resampling.LANCZOS)

    # Pad with 10px white border for optimal ViT attention
    padded = ImageOps.expand(line_img, border=10, fill="white")
    return padded
