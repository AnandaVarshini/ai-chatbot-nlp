from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

out_dir = Path(__file__).resolve().parent.parent / "docs" / "screenshots"
out_dir.mkdir(parents=True, exist_ok=True)

try:
    title_font = ImageFont.truetype("arial.ttf", 30)
    body_font = ImageFont.truetype("arial.ttf", 22)
    small_font = ImageFont.truetype("arial.ttf", 16)
except Exception:
    title_font = ImageFont.load_default()
    body_font = ImageFont.load_default()
    small_font = ImageFont.load_default()


def add_text_center(draw, image, text, x, y, fill, font):
    draw.text((x, y), text, fill=fill, font=font, anchor="mm")


def make_login():
    width, height = 1280, 800
    image = Image.new("RGB", (width, height), "#f4f7fb")
    draw = ImageDraw.Draw(image)

    draw.rounded_rectangle((250, 120, 1030, 680), radius=22, fill="#ffffff", outline="#dfe7f3", width=2)
    draw.text((640, 170), "AI Study Assistant", fill="#1d3557", font=title_font, anchor="mm")
    draw.text((640, 215), "Sign in to continue", fill="#4a5c7a", font=body_font, anchor="mm")

    draw.rounded_rectangle((360, 290, 920, 350), radius=10, fill="#f6f8fb", outline="#dfe7f3", width=1)
    draw.text((385, 310), "Username", fill="#60708a", font=small_font)

    draw.rounded_rectangle((360, 420, 920, 480), radius=10, fill="#f6f8fb", outline="#dfe7f3", width=1)
    draw.text((385, 440), "Password", fill="#60708a", font=small_font)

    draw.rounded_rectangle((360, 540, 920, 600), radius=12, fill="#4f46e5")
    draw.text((640, 570), "Sign in", fill="white", font=body_font, anchor="mm")
    draw.text((640, 630), "Don’t have an account? Create one", fill="#60708a", font=small_font, anchor="mm")
    image.save(out_dir / "login.png")


def make_chat():
    width, height = 1280, 800
    image = Image.new("RGB", (width, height), "#f4f7fb")
    draw = ImageDraw.Draw(image)

    draw.rounded_rectangle((20, 20, 320, 780), radius=18, fill="#ffffff", outline="#dfe7f3", width=2)
    draw.text((55, 55), "AI Study Assistant", fill="#1d3557", font=body_font)
    draw.rounded_rectangle((40, 120, 260, 175), radius=10, fill="#eef2ff", outline="#dfe7f3", width=1)
    draw.text((55, 138), "+ New chat", fill="#312e81", font=small_font)
    draw.text((40, 220), "Recent", fill="#6b7280", font=small_font)

    for y in [270, 330, 390]:
        draw.rounded_rectangle((40, y, 285, y + 40), radius=8, fill="#f8fafc", outline="#edf2f7", width=1)
        draw.text((60, y + 12), "Study session", fill="#334155", font=small_font)

    draw.rounded_rectangle((340, 20, 1240, 780), radius=18, fill="#ffffff", outline="#dfe7f3", width=2)
    draw.rounded_rectangle((380, 60, 720, 110), radius=10, fill="#eef2ff")
    draw.text((400, 78), "Ask about definitions, examples, and resources", fill="#374151", font=small_font)

    draw.rounded_rectangle((820, 160, 1180, 215), radius=12, fill="#dbeafe")
    draw.text((845, 178), "What is artificial intelligence?", fill="#1e3a8a", font=small_font)

    draw.rounded_rectangle((380, 250, 670, 300), radius=12, fill="#eef2ff")
    draw.text((410, 268), "AI is the simulation of human intelligence...", fill="#374151", font=small_font)

    draw.text((400, 360), "Quick questions", fill="#6b7280", font=small_font)
    quick_questions = ["What is AI?", "What is ML?", "Real-world ML", "AI Images"]
    for i, question in enumerate(quick_questions):
        x = 400 + (i % 2) * 200
        y = 395 + (i // 2) * 52
        draw.rounded_rectangle((x, y, x + 170, y + 36), radius=8, fill="#f8fafc", outline="#dfe7f3", width=1)
        draw.text((x + 16, y + 9), question, fill="#334155", font=small_font)

    draw.rounded_rectangle((380, 650, 1120, 720), radius=14, fill="#f8fafc", outline="#dfe7f3", width=1)
    draw.text((405, 673), "Ask me anything about AI, ML, NLP...", fill="#64748b", font=small_font)
    draw.rounded_rectangle((1160, 650, 1230, 720), radius=10, fill="#4f46e5")
    draw.text((1195, 684), "Send", fill="white", font=small_font, anchor="mm")
    image.save(out_dir / "chat.png")


def make_dashboard():
    width, height = 1280, 800
    image = Image.new("RGB", (width, height), "#f4f7fb")
    draw = ImageDraw.Draw(image)

    draw.rounded_rectangle((20, 20, 320, 780), radius=18, fill="#ffffff", outline="#dfe7f3", width=2)
    draw.text((55, 55), "AI Study Assistant", fill="#1d3557", font=body_font)
    draw.rounded_rectangle((40, 120, 260, 175), radius=10, fill="#eef2ff", outline="#dfe7f3", width=1)
    draw.text((55, 138), "+ New chat", fill="#312e81", font=small_font)
    draw.text((40, 280), "Dashboard", fill="#6b7280", font=small_font)

    draw.rounded_rectangle((340, 20, 1240, 780), radius=18, fill="#ffffff", outline="#dfe7f3", width=2)
    draw.text((390, 60), "Dashboard", fill="#1d3557", font=title_font)

    cards = [
        (390, 110, 560, 180, "Total\nQueries", "183"),
        (590, 110, 760, 180, "Answered", "142"),
        (780, 110, 950, 180, "Unanswered", "41"),
        (980, 110, 1150, 180, "Answer\nRate", "78%"),
    ]

    for x1, y1, x2, y2, label, value in cards:
        draw.rounded_rectangle((x1, y1, x2, y2), radius=16, fill="#f8fafc", outline="#dfe7f3", width=1)
        draw.text((x1 + 20, y1 + 20), label, fill="#64748b", font=small_font)
        draw.text((x1 + 20, y1 + 70), value, fill="#111827", font=title_font)

    draw.rounded_rectangle((390, 220, 1145, 620), radius=16, fill="#f8fafc", outline="#dfe7f3", width=1)
    draw.text((415, 245), "Top Intent Categories", fill="#1d3557", font=body_font)

    categories = ["Definitions", "Examples", "Images", "Math", "Research"]
    values = [70, 90, 60, 45, 80]

    for i, (label, value) in enumerate(zip(categories, values)):
        y = 290 + i * 55
        draw.text((420, y), label, fill="#334155", font=small_font)
        draw.rounded_rectangle((580, y + 6, 1090, y + 20), radius=6, fill="#e2e8f0")
        draw.rounded_rectangle((580, y + 6, 580 + value * 4.5, y + 20), radius=6, fill="#4f46e5")
        draw.text((1110, y), f"{value}%", fill="#475569", font=small_font)

    image.save(out_dir / "dashboard.png")


make_login()
make_chat()
make_dashboard()
print(f"Generated screenshots in {out_dir}")
