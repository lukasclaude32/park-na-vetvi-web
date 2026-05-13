import os
import time
import uuid
import urllib.request
import urllib.error
import json

import database as db

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "static", "images", "uploads")
GRAPH_API = "https://graph.instagram.com"
CACHE_TTL = 3600


def fetch_feed(token, limit=12):
    url = (
        f"{GRAPH_API}/me/media"
        f"?fields=id,caption,media_type,media_url,permalink,thumbnail_url,timestamp"
        f"&limit={limit}&access_token={token}"
    )
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())["data"]


def download_image(image_url):
    ext = "jpg"
    filename = f"ig-{uuid.uuid4().hex[:10]}.{ext}"
    path = os.path.join(UPLOAD_FOLDER, filename)
    req = urllib.request.Request(image_url)
    with urllib.request.urlopen(req, timeout=15) as resp:
        with open(path, "wb") as f:
            f.write(resp.read())
    return filename


def refresh_token(token):
    url = (
        f"{GRAPH_API}/refresh_access_token"
        f"?grant_type=ig_refresh_token&access_token={token}"
    )
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode())
        return data.get("access_token", token)


def update_cache(force=False):
    settings = db.get_settings()
    token = settings.get("instagram_token", "").strip()
    if not token:
        return False

    last_fetch = float(settings.get("instagram_last_fetch", "0"))
    if not force and time.time() - last_fetch < CACHE_TTL:
        return True

    try:
        posts = fetch_feed(token)
    except Exception:
        # Avoid retrying a broken token on every homepage load.
        db.update_setting("instagram_last_fetch", str(time.time()))
        return False

    conn = db.get_db()

    old_posts = conn.execute("SELECT image FROM instagram_posts").fetchall()
    for row in old_posts:
        img_path = os.path.join(UPLOAD_FOLDER, row["image"])
        if os.path.exists(img_path):
            try:
                os.remove(img_path)
            except OSError:
                pass
    conn.execute("DELETE FROM instagram_posts")

    for i, post in enumerate(posts):
        media_type = post.get("media_type", "")
        if media_type == "VIDEO":
            img_url = post.get("thumbnail_url", "")
        else:
            img_url = post.get("media_url", "")

        if not img_url:
            continue

        try:
            local_file = download_image(img_url)
        except Exception:
            continue

        conn.execute(
            "INSERT INTO instagram_posts (instagram_url, image, sort_order) VALUES (?, ?, ?)",
            (post.get("permalink", ""), local_file, i),
        )

    conn.commit()
    conn.close()

    db.update_setting("instagram_last_fetch", str(time.time()))

    try:
        new_token = refresh_token(token)
        if new_token != token:
            db.update_setting("instagram_token", new_token)
    except Exception:
        pass

    return True
