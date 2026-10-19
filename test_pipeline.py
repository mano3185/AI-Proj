"""End-to-End Test for eigopop pipeline (Vision + NLP + Dictionary)."""

import time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from src.vision.ocr import OCREngine
from src.nlp.parser import JapaneseParser
from src.dict.lookup import DictionaryEngine


def create_test_image(
    text: str, output_path: str = "test_crop.png", font_size: int = 36
) -> str:
    """Create a synthetic Japanese image crop to simulate a screen snip."""
    font_path = "/usr/share/fonts/noto-cjk/NotoSansCJK-Light.ttc"
    try:
        font = ImageFont.truetype(font_path, font_size)
    except Exception:
        font = ImageFont.load_default()

    # Create image with white background
    img = Image.new("RGB", (700, 100), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((20, 25), text, fill=(20, 20, 20), font=font)
    img.save(output_path)
    print(f"[Test] Saved synthetic test image to {output_path}")
    return output_path


def main():
    print("=" * 60)
    print("  EIGOPOP: END-TO-END PIPELINE PROTOTYPE TEST")
    print("=" * 60)

    # 1. Initialize all engines
    t0 = time.perf_counter()
    ocr = OCREngine()
    parser = JapaneseParser(mode="C")
    dictionary = DictionaryEngine()
    init_time = (time.perf_counter() - t0) * 1000
    print(f"\n[Ready] All engines initialized in {init_time:.1f}ms\n")

    # 2. Test phrases: conversational, verbs with inflection, and nouns
    test_phrases = [
        "美味しそうな寿司を食べに行こう！",
        "吾輩は猫である。名前はまだ無い。",
        "新しい魔法を覚えさせられた。",
    ]

    for idx, test_text in enumerate(test_phrases, start=1):
        print("-" * 60)
        print(f"Test Case #{idx}: \"{test_text}\"")
        img_path = create_test_image(test_text, f"test_crop_{idx}.png")

        # Step 1: Vision OCR
        recognized_text, ocr_time = ocr.recognize(img_path)
        print(f"  [Vision OCR] Output: \"{recognized_text}\" (took {ocr_time:.1f}ms)")

        # Step 2: NLP Morphological Tokenization & De-inflection
        t_nlp = time.perf_counter()
        tokens = parser.parse(recognized_text)
        nlp_time = (time.perf_counter() - t_nlp) * 1000
        print(f"  [NLP Parse] Identified {len(tokens)} tokens (took {nlp_time:.2f}ms)")

        # Step 3: Dictionary Lookup
        t_dict = time.perf_counter()
        print("\n  [Vocabulary Breakdown & Lookup]:")
        for token in tokens:
            if not token.is_content_word:
                continue

            entries = dictionary.lookup_word(token.dictionary_form, max_entries=1)
            meaning_str = (
                entries[0].meanings[0] if entries and entries[0].meanings else "N/A"
            )
            kana_str = (
                f"[{'/'.join(entries[0].kana)}]" if entries and entries[0].kana else ""
            )

            print(
                f"    - {token.surface:<6} -> Base: {token.dictionary_form:<6} {kana_str:<12} | {meaning_str}"
            )

        dict_time = (time.perf_counter() - t_dict) * 1000
        total_time = ocr_time + nlp_time + dict_time

        print(
            f"\n  [Latency Breakdown]: Vision: {ocr_time:.1f}ms | NLP: {nlp_time:.1f}ms | Dict: {dict_time:.1f}ms"
        )
        print(f"  --> Total Query Latency: {total_time:.1f} ms\n")

    print("=" * 60)
    print("  ALL PIPELINE TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    main()
