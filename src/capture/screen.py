"""Fast screen capture utility using mss."""

from PIL import Image
import mss


class ScreenCapture:
    def __init__(self):
        self.sct = mss.mss()

    def capture_region(self, x: int, y: int, width: int, height: int) -> Image.Image:
        """Capture a bounding box region from the desktop screen."""
        monitor = {
            "top": int(y),
            "left": int(x),
            "width": int(width),
            "height": int(height),
        }
        sct_img = self.sct.grab(monitor)
        # Convert BGRA to RGB PIL Image
        img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
        return img
