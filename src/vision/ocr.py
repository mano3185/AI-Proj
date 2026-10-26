"""High-performance OCR engine with MeikiOCR (D-FINE detector + ONNX) and Manga-OCR fallback."""

import time
from pathlib import Path
import numpy as np
from PIL import Image


class OCREngine:
    def __init__(self, engine: str = "meiki", force_cpu: bool = False):
        self.engine_name = engine
        self.force_cpu = force_cpu
        self.meiki = None
        self.mocr = None

        if self.engine_name == "meiki":
            try:
                from meikiocr import MeikiOCR

                print("[OCREngine] Initializing MeikiOCR (D-FINE Text Detector + ONNX Recognizer)...")
                t0 = time.perf_counter()
                self.meiki = MeikiOCR()
                print(f"[OCREngine] MeikiOCR ready in {(time.perf_counter() - t0)*1000:.1f}ms")
            except Exception as e:
                print(f"[OCREngine] Could not load MeikiOCR ({e}), falling back to Manga-OCR")
                self.engine_name = "manga"

        if self.engine_name == "manga":
            from manga_ocr import MangaOcr

            print("[OCREngine] Initializing Manga-OCR (Vision Transformer)...")
            t0 = time.perf_counter()
            self.mocr = MangaOcr(force_cpu=self.force_cpu)
            print(f"[OCREngine] Manga-OCR ready in {(time.perf_counter() - t0)*1000:.1f}ms")

    def recognize(self, image: Image.Image | str | Path) -> tuple[str, float]:
        """Recognize Japanese text from arbitrary rectangular regions.
        Returns: (recognized_text, latency_ms)
        """
        if isinstance(image, (str, Path)):
            image = Image.open(image).convert("RGB")

        start = time.perf_counter()

        if self.engine_name == "meiki" and self.meiki is not None:
            # MeikiOCR expects OpenCV BGR numpy array
            arr = np.array(image.convert("RGB"))
            bgr = arr[:, :, ::-1]

            results = self.meiki.run_ocr(bgr)
            lines = []
            for r in results:
                line_text = r.get("text", "").strip()
                if line_text:
                    lines.append(line_text)

            full_text = "\n".join(lines)
            latency_ms = (time.perf_counter() - start) * 1000
            return full_text.strip(), latency_ms

        # Fallback to Manga-OCR
        from src.vision.preprocess import extract_text_lines

        lines = extract_text_lines(image)
        results = [self.mocr(line_img).strip() for line_img in lines]
        full_text = "\n".join([r for r in results if r])
        latency_ms = (time.perf_counter() - start) * 1000
        return full_text.strip(), latency_ms
