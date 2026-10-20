"""Vision Transformer OCR engine using Manga-OCR on CUDA/CPU."""

import time
from pathlib import Path
from PIL import Image
import torch
from manga_ocr import MangaOcr

from src.vision.preprocess import extract_text_lines


class OCREngine:
    def __init__(self, device: str | None = None, force_cpu: bool = False):
        if force_cpu:
            self.device = "cpu"
        elif device:
            self.device = device
        else:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"

        print(f"[OCREngine] Initializing Manga-OCR on device: {self.device}...")
        start = time.perf_counter()
        self.mocr = MangaOcr(force_cpu=(self.device == "cpu"))
        duration = (time.perf_counter() - start) * 1000
        print(f"[OCREngine] Model loaded in {duration:.1f}ms")

    def recognize(self, image: Image.Image | str | Path) -> tuple[str, float]:
        """Recognize Japanese text with adaptive line segmentation & preprocessing.
        Returns: (recognized_text, latency_ms)
        """
        if isinstance(image, (str, Path)):
            image = Image.open(image).convert("RGB")

        start = time.perf_counter()

        # Step 1: Extract individual text lines via horizontal projection profiling
        lines = extract_text_lines(image)

        # Step 2: Run OCR on each line
        results = []
        for line_img in lines:
            line_text = self.mocr(line_img).strip()
            if line_text:
                results.append(line_text)

        full_text = "\n".join(results)
        latency_ms = (time.perf_counter() - start) * 1000
        return full_text.strip(), latency_ms
