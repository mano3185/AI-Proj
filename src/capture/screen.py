"""Screen capture utility supporting both Wayland (grim+slurp) and X11 (mss)."""

import os
import io
import shutil
import subprocess
from PIL import Image
import mss


class ScreenCapture:
    def __init__(self):
        self.is_wayland = bool(os.environ.get("WAYLAND_DISPLAY"))
        self.has_grim = shutil.which("grim") is not None
        self.has_slurp = shutil.which("slurp") is not None
        self.sct = None
        if not (self.is_wayland and self.has_grim):
            self.sct = mss.mss()

    def select_and_capture_wayland(self) -> tuple[Image.Image | None, tuple[int, int] | None]:
        """Use native Wayland slurp + grim for seamless layer-shell snipping."""
        if not (self.has_slurp and self.has_grim):
            return None, None

        # Run slurp for interactive box selection
        p_slurp = subprocess.run(
            ["slurp", "-b", "00000066", "-c", "89b4faff", "-s", "00000000", "-w", "2"],
            capture_output=True,
            text=True
        )
        if p_slurp.returncode != 0 or not p_slurp.stdout.strip():
            return None, None  # User pressed Escape or canceled

        geom = p_slurp.stdout.strip()

        # Run grim to capture the selected region to stdout
        p_grim = subprocess.run(
            ["grim", "-g", geom, "-t", "ppm", "-"],
            capture_output=True
        )
        if p_grim.returncode != 0 or not p_grim.stdout:
            return None, None

        img = Image.open(io.BytesIO(p_grim.stdout)).convert("RGB")

        # Parse position (e.g. "120,340 500x200") for tooltip popup placement
        try:
            parts = geom.split()
            coords = parts[0].split(",")
            pos = (int(coords[0]), int(coords[1]))
        except Exception:
            pos = None

        return img, pos

    def capture_region(self, x: int, y: int, width: int, height: int) -> Image.Image:
        """Capture a bounding box region."""
        if self.is_wayland and self.has_grim:
            geom = f"{int(x)},{int(y)} {int(width)}x{int(height)}"
            p_grim = subprocess.run(
                ["grim", "-g", geom, "-t", "ppm", "-"],
                capture_output=True
            )
            if p_grim.returncode == 0 and p_grim.stdout:
                return Image.open(io.BytesIO(p_grim.stdout)).convert("RGB")

        # Fallback to mss
        if self.sct is None:
            self.sct = mss.mss()
        monitor = {
            "top": int(y),
            "left": int(x),
            "width": int(width),
            "height": int(height),
        }
        sct_img = self.sct.grab(monitor)
        return Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
