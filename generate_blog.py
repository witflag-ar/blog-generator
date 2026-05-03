import os
import json
import re
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

# ════════════════════════════════════════
# ENV
# ════════════════════════════════════════

load_dotenv()

SUPA_URL = os.getenv("SUPA_URL")
SUPA_KEY = os.getenv("SUPA_KEY")

supabase = create_client(SUPA_URL, SUPA_KEY)


# ════════════════════════════════════════
# UTILS
# ════════════════════════════════════════

def calc_read_time(html):
    text = re.sub('<[^>]+>', '', html or "")
    return max(1, round(len(text.split()) / 200))


def safe_slug(slug):
    return re.sub(r'[^a-zA-Z0-9\-]', '', slug or "")


def format_date(iso):
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except:
        dt = datetime.now()
    return dt.strftime("%d %B %Y")


# ════════════════════════════════════════
# GENERATION ARTICLE
# ════════════════════════════════════════

def generate(post):
    os.makedirs("blog", exist_ok=True)

    slug = safe_slug(post.get("slug"))
    file_path = f"blog/{slug}.html"

    # ✅ IMPORTANT : éviter doublons
    if os.path.exists(file_path):
        print(f"⏩ Skip (existe déjà) : {slug}")
        return

    with open("blog_template.html", "r", encoding="utf-8") as f:
        template = f.read()

    tags = post.get("tags", [])
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",")]

    replacements = {
        "{{title}}": post.get("title", ""),
        "{{slug}}": slug,
        "{{meta_description}}": (post.get("excerpt") or "")[:160],
        "{{content}}": post.get("content", ""),
        "{{featured_image}}": post.get("featured_image", ""),
        "{{author}}": post.get("author", "Admin"),
        "{{published_at_display}}": format_date(post.get("published_at")),
        "{{read_time}}": str(calc_read_time(post.get("content", ""))),
        "{{tags_json}}": json.dumps(tags, ensure_ascii=False),
    }

    html = template
    for k, v in replacements.items():
        html = html.replace(k, str(v))

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ créé : {file_path}")


# ════════════════════════════════════════
# MAIN
# ════════════════════════════════════════

def main():
    print("🚀 génération articles...")

    res = supabase.table("blog_posts") \
        .select("*") \
        .eq("status", "published") \
        .order("published_at", desc=True) \
        .execute()

    posts = res.data or []

    for post in posts:
        generate(post)

    print(f"\n🎉 terminé : {len(posts)} articles traités")


if __name__ == "__main__":
    main()
