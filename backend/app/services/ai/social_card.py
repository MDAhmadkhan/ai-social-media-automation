from __future__ import annotations

from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image, ImageDraw, ImageFont

from app.core.config import get_settings
from app.models.domain import ContentItem
from app.services.storage.adapters import get_storage_adapter

settings = get_settings()


class SocialCardGenerator:
    width = 1200
    height = 630
    version = "v3"

    def generate(self, content: ContentItem, summary: str | None = None, logo_url: str | None = None) -> str:
        category, palette = self._category(content)
        image = Image.new("RGB", (self.width, self.height), "#ffffff")
        draw = ImageDraw.Draw(image)

        self._draw_promo_background(draw)
        self._draw_logo(image, draw, logo_url)
        self._draw_category_icons(draw)

        headline_font = self._font(66, bold=True)
        headline_accent_font = self._font(62, bold=True)
        title_font = self._font(34, bold=True)
        body_font = self._font(24)
        micro_font = self._font(20)

        draw.text((58, 157), "POWERFUL", font=headline_font, fill="#101124")
        draw.text((58, 225), "ONLINE TOOLS", font=headline_font, fill="#101124")
        draw.text((58, 293), "IN ONE PLACE", font=headline_accent_font, fill="#a0003b")
        draw.line((58, 367, 510, 367), fill="#d8d8df", width=2)

        clean_title = self._clean_title(content.title)
        draw.rounded_rectangle((58, 392, 540, 475), radius=18, fill="#fff4f7")
        draw.rectangle((58, 392, 66, 475), fill=palette["accent"])
        self._draw_multiline(draw, clean_title, (82, 410), title_font, "#101124", max_width=430, max_lines=2, line_gap=5)

        description = summary or content.meta_description or "Fast, secure, and free browser-side tool for everyday work."
        self._draw_multiline(draw, description, (62, 486), self._font(19), "#30384a", max_width=480, max_lines=1, line_gap=7)

        self._draw_laptop(draw, clean_title, category, palette)
        self._draw_tool_badge(draw)
        self._draw_feature_strip(draw)

        domain = urlparse(str(content.canonical_url)).netloc or "ilovetoolxyz.com"
        draw.rounded_rectangle((58, 556, 340, 602), radius=23, fill="#8a0030")
        self._center_text(draw, f"www.{domain.replace('www.', '')}", (58, 556, 340, 602), micro_font, "white")
        draw.text((732, 574), "Fast  |  Easy  |  Secure  |  Always Free", font=self._font(24, bold=True), fill="#101124")

        buffer = BytesIO()
        image.save(buffer, format="PNG", optimize=True)
        saved = get_storage_adapter().save_bytes(buffer.getvalue(), "image/png", "png")
        return self._absolute_url(saved)

    def _absolute_url(self, url: str) -> str:
        if url.startswith(("http://", "https://")):
            return url
        return settings.public_base_url.rstrip("/") + url

    def _category(self, content: ContentItem) -> tuple[str, dict[str, str]]:
        text = f"{content.title} {' '.join(content.keywords)}".lower()
        if any(word in text for word in ["pdf", "merge", "split", "compress"]):
            return "PDF Tool", {"bg": "#fff1f2", "accent": "#e11d48", "dark": "#881337", "soft": "#ffe4e6"}
        if any(word in text for word in ["image", "photo", "convert", "resize"]):
            return "Image Tool", {"bg": "#eff6ff", "accent": "#2563eb", "dark": "#1e3a8a", "soft": "#dbeafe"}
        if any(word in text for word in ["seo", "keyword", "meta", "schema", "robots"]):
            return "SEO Tool", {"bg": "#ecfdf5", "accent": "#059669", "dark": "#064e3b", "soft": "#d1fae5"}
        if any(word in text for word in ["code", "json", "html", "css", "developer"]):
            return "Developer Tool", {"bg": "#f5f3ff", "accent": "#7c3aed", "dark": "#4c1d95", "soft": "#ede9fe"}
        return "Free Tool", {"bg": "#f8fafc", "accent": "#0f766e", "dark": "#134e4a", "soft": "#ccfbf1"}

    def _icon(self, category: str) -> str:
        return {
            "PDF Tool": "PDF",
            "Image Tool": "IMG",
            "SEO Tool": "SEO",
            "Developer Tool": "</>",
            "Free Tool": "TOOL",
        }.get(category, "TOOL")

    def _clean_title(self, title: str) -> str:
        return title.split("|")[0].split("-")[0].strip() or title

    def _font(self, size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        candidates = [
            "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        ]
        for path in candidates:
            try:
                return ImageFont.truetype(path, size=size)
            except OSError:
                continue
        return ImageFont.load_default()

    def _draw_background(self, draw: ImageDraw.ImageDraw, palette: dict[str, str]) -> None:
        draw.rectangle((0, 0, self.width, self.height), fill=palette["bg"])
        draw.ellipse((-120, -160, 260, 220), fill=palette["soft"])
        draw.ellipse((990, 430, 1320, 760), fill=palette["soft"])

    def _draw_promo_background(self, draw: ImageDraw.ImageDraw) -> None:
        draw.rectangle((0, 0, self.width, self.height), fill="#ffffff")
        draw.pieslice((760, -210, 1370, 400), 92, 270, fill="#8a0030")
        draw.pieslice((860, -130, 1360, 370), 92, 268, fill="#b50045")
        draw.pieslice((965, 330, 1370, 735), 170, 280, fill="#8a0030")
        draw.ellipse((180, -120, 470, 170), outline="#f3d5df", width=2)
        for x in range(18, 140, 18):
            for y in range(16, 92, 18):
                draw.ellipse((x, y, x + 3, y + 3), fill="#b8bac4")
        for x in range(1000, 1142, 18):
            for y in range(26, 104, 18):
                draw.ellipse((x, y, x + 3, y + 3), fill="#f7c8d8")
        for offset in range(0, 5):
            draw.arc((935 + offset * 23, 90 + offset * 20, 1290 + offset * 26, 420 + offset * 28), 190, 285, fill="#d85d86", width=1)
        draw.line((948, 122, 1188, 12), fill="#ffffff", width=2)
        draw.line((1068, 280, 1200, 198), fill="#ffffff", width=2)

    def _draw_logo(self, image: Image.Image, draw: ImageDraw.ImageDraw, logo_url: str | None) -> None:
        logo = self._load_logo(logo_url)
        if logo:
            logo.thumbnail((255, 82), Image.Resampling.LANCZOS)
            image.paste(logo, (58, 70), logo if logo.mode == "RGBA" else None)
            draw.line((58, 160, 286, 160), fill="#f0d2dc", width=3)
            return
        logo_color = "#8a0030"
        draw.text((58, 64), "I LOVE", font=self._font(17, bold=True), fill="#101124")
        draw.text((58, 86), "TOOL XYZ", font=self._font(52, bold=True), fill=logo_color)
        draw.line((58, 145, 286, 145), fill="#f0d2dc", width=3)

    def _load_logo(self, logo_url: str | None) -> Image.Image | None:
        if not logo_url:
            return None
        path: Path | None = None
        storage_prefix = settings.public_base_url.rstrip("/") + "/storage/"
        if logo_url.startswith(storage_prefix):
            path = Path(settings.local_storage_path) / logo_url.removeprefix(storage_prefix)
        elif logo_url.startswith("/storage/"):
            path = Path(settings.local_storage_path) / logo_url.removeprefix("/storage/")
        if not path or not path.exists():
            return None
        try:
            with Image.open(path) as logo:
                return logo.convert("RGBA")
        except OSError:
            return None

    def _draw_category_icons(self, draw: ImageDraw.ImageDraw) -> None:
        items = [
            ("PDF", "PDF", "#e11d48"),
            ("IMG", "Image", "#2563eb"),
            ("SEO", "SEO", "#16a34a"),
            ("</>", "Code", "#f97316"),
            ("TXT", "Text", "#7c3aed"),
            ("123", "Calc", "#9333ea"),
        ]
        x = 555
        for icon, label, color in items:
            draw.ellipse((x, 46, x + 56, 102), fill=color)
            self._center_text(draw, icon, (x, 46, x + 56, 102), self._font(18, bold=True), "white")
            self._center_text(draw, label, (x - 18, 108, x + 74, 132), self._font(14, bold=True), "#101124")
            x += 103

    def _draw_laptop(self, draw: ImageDraw.ImageDraw, title: str, category: str, palette: dict[str, str]) -> None:
        draw.rounded_rectangle((565, 162, 1115, 468), radius=28, fill="#111827")
        draw.rounded_rectangle((582, 181, 1098, 441), radius=12, fill="#fff7fa")
        draw.rectangle((545, 462, 1135, 488), fill="#242937")
        draw.rounded_rectangle((515, 488, 1168, 512), radius=12, fill="#7c7f88")
        draw.rounded_rectangle((665, 488, 1018, 501), radius=7, fill="#c8c9cf")

        draw.text((612, 206), "I LOVE TOOL XYZ", font=self._font(22, bold=True), fill="#8a0030")
        nav_items = ["PDF", "Image", "SEO", "Code", "Text"]
        nav_x = 835
        for item in nav_items:
            draw.text((nav_x, 214), item, font=self._font(12, bold=True), fill="#101124")
            nav_x += 48

        self._draw_multiline(draw, title, (660, 268), self._font(35, bold=True), "#101124", max_width=365, max_lines=2, line_gap=4)
        draw.text((708, 350), f"{category} - fast, private and free", font=self._font(18), fill="#475569")
        chip_labels = ["No Upload", "Fast", "Secure"]
        chip_x = 690
        for label in chip_labels:
            draw.rounded_rectangle((chip_x, 383, chip_x + 92, 414), radius=15, fill="#ffffff", outline="#d6d9e2")
            self._center_text(draw, label, (chip_x, 383, chip_x + 92, 414), self._font(13, bold=True), "#101124")
            chip_x += 105

        card_x = 622
        for label in ["Create", "Convert", "Optimize"]:
            draw.rounded_rectangle((card_x, 426, card_x + 122, 486), radius=12, fill="#ffffff", outline="#ececf2")
            draw.rounded_rectangle((card_x + 14, 440, card_x + 44, 470), radius=7, fill=palette["accent"])
            self._center_text(draw, self._icon(category), (card_x + 14, 440, card_x + 44, 470), self._font(10, bold=True), "white")
            draw.text((card_x + 53, 443), label, font=self._font(15, bold=True), fill="#101124")
            draw.text((card_x + 53, 463), "Instant", font=self._font(12), fill="#64748b")
            card_x += 138

    def _draw_tool_badge(self, draw: ImageDraw.ImageDraw) -> None:
        draw.ellipse((1000, 275, 1156, 431), fill="#710027", outline="#ffffff", width=5)
        draw.ellipse((1011, 286, 1145, 420), outline="#eab4c7", width=2)
        self._center_text(draw, "100+", (1000, 302, 1156, 356), self._font(42, bold=True), "white")
        self._center_text(draw, "TOOLS", (1000, 352, 1156, 386), self._font(26, bold=True), "white")
        draw.rounded_rectangle((1016, 390, 1140, 425), radius=17, fill="#d41457")
        self._center_text(draw, "FREE", (1016, 390, 1140, 425), self._font(22, bold=True), "white")

    def _draw_feature_strip(self, draw: ImageDraw.ImageDraw) -> None:
        draw.rectangle((0, 522, 1200, 558), fill="#760029")
        features = [
            ("CONVERT", "Files instantly"),
            ("COMPRESS", "Reduce file size"),
            ("EDIT", "Work with ease"),
            ("OPTIMIZE", "Boost SEO"),
            ("GENERATE", "Text and code"),
        ]
        x = 70
        for heading, detail in features:
            draw.ellipse((x, 530, x + 18, 548), outline="white", width=3)
            draw.text((x + 31, 523), heading, font=self._font(17, bold=True), fill="white")
            draw.text((x + 31, 542), detail, font=self._font(13), fill="#ffd8e6")
            x += 215

    def _draw_multiline(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        origin: tuple[int, int],
        font: ImageFont.ImageFont,
        fill: str,
        max_width: int,
        max_lines: int,
        line_gap: int,
    ) -> None:
        lines = self._wrap_pixels(draw, text, font, max_width, max_lines)
        line_height = self._line_height(draw, font)
        x, y = origin
        for index, line in enumerate(lines):
            draw.text((x, y + index * (line_height + line_gap)), line, font=font, fill=fill)

    def _wrap_pixels(self, draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int, max_lines: int) -> list[str]:
        words = text.replace("\n", " ").split()
        lines: list[str] = []
        current = ""
        for word in words:
            candidate = word if not current else f"{current} {word}"
            if self._text_width(draw, candidate, font) <= max_width:
                current = candidate
                continue
            if current:
                lines.append(current)
            current = word
            if len(lines) == max_lines:
                break
        if current and len(lines) < max_lines:
            lines.append(current)
        if len(lines) == max_lines and len(" ".join(lines).split()) < len(words):
            lines[-1] = self._ellipsize(draw, lines[-1], font, max_width)
        return lines

    def _ellipsize(self, draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> str:
        suffix = "..."
        while text and self._text_width(draw, text + suffix, font) > max_width:
            text = text.rsplit(" ", 1)[0] if " " in text else text[:-1]
        return (text.strip() + suffix) if text else suffix

    def _line_height(self, draw: ImageDraw.ImageDraw, font: ImageFont.ImageFont) -> int:
        bbox = draw.textbbox((0, 0), "Ag", font=font)
        return bbox[3] - bbox[1]

    def _text_width(self, draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> int:
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0]

    def _center_text(self, draw: ImageDraw.ImageDraw, text: str, box: tuple[int, int, int, int], font: ImageFont.ImageFont, fill: str) -> None:
        left, top, right, bottom = box
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        draw.text((left + (right - left - text_width) / 2, top + (bottom - top - text_height) / 2 - 2), text, font=font, fill=fill)
