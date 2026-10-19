"""Vision Transformer OCR engine using Manga-OCR on CUDA/CPU."""

import time
from pathlib import Path
from PIL import Image
import torch
from manga_ocr import MangaOcr

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
        """Recognize Japanese text from PIL Image or image file path.
        Returns: (recognized_text, latency_ms)
        """
        if isinstance(image, (str, Path)):
            image = Image.open(image).convert("RGB")

        start = time.perf_counter()
        text = self.mocr(image)
        latency_ms = (time.perf_counter() - start) * 1000
        return text.strip(), latency_ms
