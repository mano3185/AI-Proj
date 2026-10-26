# Eigopop (英語ポップ)

> **Real-Time On-Screen Japanese Character Recognition & Morphological Popup Reading Assistant**

A lightweight, local AI application designed for language learners, researchers, and readers. Eigopop captures unselectable Japanese text from desktop screens (manga, anime subtitles, visual novels, video games, scanned documents), runs neural Vision-Language character recognition, parses morphological sentence boundaries, de-inflects verbs and adjectives, and displays instant lexical definitions in a sleek floating desktop card.

---

## ⚡ Performance Highlights (Tested on NVIDIA RTX 4060 Laptop GPU)

| Component | Architecture / Engine | Latency |
| :--- | :--- | :---: |
| **Vision OCR** | Vision Transformer (`kha-white/manga-ocr-base`) with PyTorch CUDA FP16 | **~50 ms** |
| **NLP Tokenization** | SudachiPy morphological lattice boundary parser | **< 1 ms** |
| **Dictionary Query** | Offline JMdict & KANJIDIC SQLite backend (`jamdict`) | **~40 ms** |
| **Total Query Latency** | **End-to-End Snip to Definition** | **< 100 ms** ⚡ |
| **VRAM Footprint** | Fits comfortably alongside 3D games | **< 450 MB** |

---

## 🚀 Key Features

* **Vision Transformer OCR:** Highly resilient against vertical right-to-left layouts, stylized comic/display fonts, low resolutions, and furigana (ruby annotations).
* **Morphological Sentence Tokenization:** Japanese has no spaces between words. Eigopop uses SudachiPy lattice state-space search to accurately segment sentences into dictionary headwords.
* **Intelligent De-Inflection:** Automatically resolves complex grammatical conjugations (e.g., causative-passive `覚えさせられた` $\rightarrow$ `覚える`, volitional `行こう` $\rightarrow$ `行く`, te-form `食べて` $\rightarrow$ `食べる`).
* **Rich Lexical Lookup:** Fully offline English meanings, Kana readings, JLPT levels, and part-of-speech metadata from JMdict.
* **Interactive Desktop Snipping Overlay:** Smooth PyQt6 borderless snipping canvas (Alt+S) with floating dark-mode definition cards.

---

## 📁 Repository Structure

```text
eigopop/
├── app.py                  # Main desktop GUI application & CLI runner
├── test_pipeline.py        # End-to-end benchmark test script
├── pyproject.toml          # Project configuration & dependencies
├── README.md               # Documentation
└── src/
    ├── vision/
    │   └── ocr.py          # Manga-OCR Vision Transformer wrapper on CUDA
    ├── nlp/
    │   └── parser.py       # SudachiPy morphological analyzer & de-inflector
    ├── dict/
    │   └── lookup.py       # JMdict & KANJIDIC query manager
    ├── capture/
    │   └── screen.py       # High-performance screen grabber (mss)
    └── ui/
        ├── snipper.py      # PyQt6 full-screen selection canvas
        └── popup.py        # PyQt6 floating dictionary card
```

---

## 🛠️ Getting Started

### 1. Prerequisites

* Python 3.10+
* NVIDIA GPU with CUDA drivers (optional, falls back to CPU automatically)

### 2. Installation

```bash
# Clone the repository
git clone https://github.com/your-username/eigopop.git
cd eigopop

# Install dependencies into your virtual environment
pip install -e .
```

### 3. Usage

#### Interactive Desktop GUI

```bash
python app.py
```

* Click **"✂ Snip Japanese Text"** or press **`Alt + S`**.
* Click and drag a box over any Japanese text on your screen (manga bubble, game dialogue, or video).
* Release your mouse button — the floating dictionary card will pop up instantaneously!
* Press **`Esc`** or click **`✕`** to dismiss.

#### CLI Test Mode (Single Image)

```bash
python app.py --image test_crop_1.png
```

#### Run Comprehensive Pipeline Benchmarks

```bash
python test_pipeline.py
```
