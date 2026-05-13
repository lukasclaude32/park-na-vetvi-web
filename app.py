import os
import uuid
from functools import wraps

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    jsonify,
)
from werkzeug.utils import secure_filename

import database as db
import instagram as ig

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "park-na-vetvi-secret-key-change-me")

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "static", "images", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_uploaded_image(file, prefix="upload"):
    if not file or not file.filename or not allowed_file(file.filename):
        return None
    ext = file.filename.rsplit(".", 1)[1].lower()
    filename = f"{prefix}-{uuid.uuid4().hex}.{ext}"
    file.save(os.path.join(UPLOAD_FOLDER, filename))
    return f"uploads/{filename}"


def remove_uploaded_image(image_path):
    if not image_path or not image_path.startswith("uploads/"):
        return
    full_path = os.path.join(os.path.dirname(__file__), "static", "images", image_path)
    if os.path.exists(full_path):
        os.remove(full_path)


def group_pricing_items(items):
    groups = []
    by_category = {}
    for item in items:
        key = item["category"]
        if key not in by_category:
            by_category[key] = {
                "category": item["category"],
                "category_note": item.get("category_note", ""),
                "featured": item.get("featured", 0),
                "prices": [],
            }
            groups.append(by_category[key])
        if item.get("featured"):
            by_category[key]["featured"] = 1
        if item.get("category_note"):
            by_category[key]["category_note"] = item["category_note"]
        by_category[key]["prices"].append(item)
    return groups


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)

    return decorated


# ---------- PUBLIC ROUTES ----------


@app.route("/")
def index():
    settings = db.get_settings()
    news = db.get_news(published_only=True, limit=3)
    ig.update_cache()
    ig_posts = db.get_instagram_posts()
    pricing_groups = group_pricing_items(db.get_pricing_items(published_only=True))
    return render_template(
        "index.html",
        settings=settings,
        news=news,
        ig_posts=ig_posts,
        pricing_groups=pricing_groups,
    )


@app.route("/o-parku")
def about():
    settings = db.get_settings()
    gallery = db.get_gallery_images(published_only=True)
    return render_template("about.html", settings=settings, gallery=gallery)


@app.route("/aktuality")
def news_list():
    settings = db.get_settings()
    news = db.get_news(published_only=True)
    return render_template("news.html", settings=settings, news=news)


@app.route("/aktuality/<int:news_id>")
def news_detail(news_id):
    settings = db.get_settings()
    item = db.get_news_by_id(news_id)
    if not item or not item.get("published"):
        return redirect(url_for("news_list"))
    return render_template("news_detail.html", settings=settings, item=item)


@app.route("/vstupne")
def pricing():
    settings = db.get_settings()
    pricing_groups = group_pricing_items(db.get_pricing_items(published_only=True))
    return render_template("pricing.html", settings=settings, pricing_groups=pricing_groups)


@app.route("/kontakt")
def contact():
    settings = db.get_settings()
    return render_template("contact.html", settings=settings)


@app.route("/eshop")
def eshop():
    settings = db.get_settings()
    return render_template("eshop.html", settings=settings)


# ---------- ADMIN ROUTES ----------


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        conn = db.get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        conn.close()

        if user and db.verify_password(password, user["password"]):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("admin_dashboard"))

        flash("Nesprávné přihlašovací údaje.", "error")

    return render_template("admin/login.html")


@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))


@app.route("/admin")
@login_required
def admin_dashboard():
    news = db.get_news(published_only=False)
    settings = db.get_settings()
    return render_template("admin/dashboard.html", news=news, settings=settings)


@app.route("/admin/novinky/nova", methods=["GET", "POST"])
@login_required
def admin_news_create():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        published = 1 if request.form.get("published") else 0

        image_path = None
        if "image" in request.files:
            file = request.files["image"]
            if file and file.filename and allowed_file(file.filename):
                ext = file.filename.rsplit(".", 1)[1].lower()
                filename = f"{uuid.uuid4().hex}.{ext}"
                file.save(os.path.join(UPLOAD_FOLDER, filename))
                image_path = filename

        if title and content:
            db.create_news(title, content, image_path, published)
            flash("Novinka byla vytvořena.", "success")
            return redirect(url_for("admin_dashboard"))

        flash("Vyplňte prosím název a obsah.", "error")

    return render_template("admin/news_edit.html", news=None)


@app.route("/admin/novinky/<int:news_id>", methods=["GET", "POST"])
@login_required
def admin_news_edit(news_id):
    news = db.get_news_by_id(news_id)
    if not news:
        flash("Novinka nenalezena.", "error")
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        published = 1 if request.form.get("published") else 0

        image_path = None
        if "image" in request.files:
            file = request.files["image"]
            if file and file.filename and allowed_file(file.filename):
                ext = file.filename.rsplit(".", 1)[1].lower()
                filename = f"{uuid.uuid4().hex}.{ext}"
                file.save(os.path.join(UPLOAD_FOLDER, filename))
                image_path = filename

        if title and content:
            db.update_news(news_id, title, content, image_path, published)
            flash("Novinka byla aktualizována.", "success")
            return redirect(url_for("admin_dashboard"))

        flash("Vyplňte prosím název a obsah.", "error")

    return render_template("admin/news_edit.html", news=news)


@app.route("/admin/novinky/<int:news_id>/smazat", methods=["POST"])
@login_required
def admin_news_delete(news_id):
    news = db.get_news_by_id(news_id)
    if news and news.get("image"):
        img_path = os.path.join(UPLOAD_FOLDER, news["image"])
        if os.path.exists(img_path):
            os.remove(img_path)
    db.delete_news(news_id)
    flash("Novinka byla smazána.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/nastaveni", methods=["GET", "POST"])
@login_required
def admin_settings():
    if request.method == "POST":
        fields = [
            "phone", "email", "address", "hours", "eshop_url",
            "facebook_url", "instagram_url", "hero_text", "about_text",
            "site_subtitle", "instagram_token",
        ]
        for field in fields:
            value = request.form.get(field, "").strip()
            db.update_setting(field, value)

        flash("Nastavení bylo uloženo.", "success")
        return redirect(url_for("admin_settings"))

    settings = db.get_settings()
    return render_template("admin/settings.html", settings=settings)


@app.route("/admin/obsah", methods=["GET", "POST"])
@login_required
def admin_content():
    fields = [
        "site_subtitle", "hero_text",
        "home_about_title", "home_instagram_title", "home_instagram_subtitle",
        "home_pricing_title", "home_pricing_subtitle", "home_cta_title", "home_cta_button",
        "about_page_title", "about_page_subtitle", "about_text", "about_intro_extra",
        "about_map_title", "about_map_subtitle", "about_gallery_title", "about_gallery_subtitle",
        "about_info_title", "about_info_subtitle", "about_cta_title", "about_cta_text",
        "pricing_page_title", "pricing_page_subtitle", "pricing_info_text", "pricing_button_text",
        "contact_page_title", "contact_page_subtitle", "contact_transport",
        "contact_operator_title", "contact_grant_text",
        "eshop_page_title", "eshop_page_subtitle", "eshop_soon_title", "eshop_soon_text",
    ]
    if request.method == "POST":
        for field in fields:
            db.update_setting(field, request.form.get(field, "").strip())
        flash("Obsah webu byl uložen.", "success")
        return redirect(url_for("admin_content"))

    settings = db.get_settings()
    return render_template("admin/content.html", settings=settings, fields=fields)


@app.route("/admin/galerie", methods=["GET", "POST"])
@login_required
def admin_gallery():
    if request.method == "POST":
        image = save_uploaded_image(request.files.get("image"), prefix="gallery")
        if not image:
            flash("Nahrajte prosím obrázek galerie.", "error")
            return redirect(url_for("admin_gallery"))
        db.create_gallery_image(
            request.form.get("title", "").strip(),
            request.form.get("alt", "").strip(),
            image,
            int(request.form.get("sort_order", 0) or 0),
            1 if request.form.get("published") else 0,
        )
        flash("Fotka byla přidána do galerie.", "success")
        return redirect(url_for("admin_gallery"))

    images = db.get_gallery_images(published_only=False)
    return render_template("admin/gallery.html", images=images)


@app.route("/admin/galerie/<int:image_id>", methods=["GET", "POST"])
@login_required
def admin_gallery_edit(image_id):
    image = db.get_gallery_image_by_id(image_id)
    if not image:
        flash("Fotka nebyla nalezena.", "error")
        return redirect(url_for("admin_gallery"))

    if request.method == "POST":
        new_image = save_uploaded_image(request.files.get("image"), prefix="gallery")
        if new_image:
            remove_uploaded_image(image.get("image"))
        db.update_gallery_image(
            image_id,
            request.form.get("title", "").strip(),
            request.form.get("alt", "").strip(),
            int(request.form.get("sort_order", 0) or 0),
            1 if request.form.get("published") else 0,
            new_image,
        )
        flash("Fotka byla upravena.", "success")
        return redirect(url_for("admin_gallery"))

    return render_template("admin/gallery_edit.html", image=image)


@app.route("/admin/galerie/<int:image_id>/smazat", methods=["POST"])
@login_required
def admin_gallery_delete(image_id):
    image = db.get_gallery_image_by_id(image_id)
    if image:
        remove_uploaded_image(image.get("image"))
    db.delete_gallery_image(image_id)
    flash("Fotka byla smazána.", "success")
    return redirect(url_for("admin_gallery"))


@app.route("/admin/cenik", methods=["GET", "POST"])
@login_required
def admin_pricing():
    if request.method == "POST":
        db.create_pricing_item(
            request.form.get("category", "").strip(),
            request.form.get("category_note", "").strip(),
            request.form.get("label", "").strip(),
            request.form.get("price", "").strip(),
            int(request.form.get("sort_order", 0) or 0),
            1 if request.form.get("featured") else 0,
            1 if request.form.get("published") else 0,
        )
        flash("Položka ceníku byla přidána.", "success")
        return redirect(url_for("admin_pricing"))

    items = db.get_pricing_items(published_only=False)
    return render_template("admin/pricing.html", items=items)


@app.route("/admin/cenik/<int:item_id>", methods=["GET", "POST"])
@login_required
def admin_pricing_edit(item_id):
    item = db.get_pricing_item_by_id(item_id)
    if not item:
        flash("Položka ceníku nebyla nalezena.", "error")
        return redirect(url_for("admin_pricing"))

    if request.method == "POST":
        db.update_pricing_item(
            item_id,
            request.form.get("category", "").strip(),
            request.form.get("category_note", "").strip(),
            request.form.get("label", "").strip(),
            request.form.get("price", "").strip(),
            int(request.form.get("sort_order", 0) or 0),
            1 if request.form.get("featured") else 0,
            1 if request.form.get("published") else 0,
        )
        flash("Položka ceníku byla upravena.", "success")
        return redirect(url_for("admin_pricing"))

    return render_template("admin/pricing_edit.html", item=item)


@app.route("/admin/cenik/<int:item_id>/smazat", methods=["POST"])
@login_required
def admin_pricing_delete(item_id):
    db.delete_pricing_item(item_id)
    flash("Položka ceníku byla smazána.", "success")
    return redirect(url_for("admin_pricing"))


@app.route("/admin/instagram", methods=["GET", "POST"])
@login_required
def admin_instagram():
    if request.method == "POST":
        if ig.update_cache(force=True):
            flash("Instagram feed byl obnoven.", "success")
        else:
            flash("Instagram feed se nepodařilo obnovit. Zkontrolujte token v nastavení.", "error")
        return redirect(url_for("admin_instagram"))

    settings = db.get_settings()
    posts = db.get_instagram_posts()
    return render_template("admin/instagram.html", posts=posts, settings=settings)


@app.route("/admin/heslo", methods=["POST"])
@login_required
def admin_change_password():
    old_password = request.form.get("old_password", "")
    new_password = request.form.get("new_password", "")
    confirm_password = request.form.get("confirm_password", "")

    if new_password != confirm_password:
        flash("Nová hesla se neshodují.", "error")
        return redirect(url_for("admin_settings"))

    if len(new_password) < 6:
        flash("Heslo musí mít alespoň 6 znaků.", "error")
        return redirect(url_for("admin_settings"))

    conn = db.get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE id = ?", (session["user_id"],)
    ).fetchone()

    if not db.verify_password(old_password, user["password"]):
        flash("Staré heslo je nesprávné.", "error")
        conn.close()
        return redirect(url_for("admin_settings"))

    conn.execute(
        "UPDATE users SET password = ? WHERE id = ?",
        (db.hash_password(new_password), session["user_id"]),
    )
    conn.commit()
    conn.close()

    flash("Heslo bylo změněno.", "success")
    return redirect(url_for("admin_settings"))


if __name__ == "__main__":
    db.init_db()
    db.repair_czech_texts()
    app.run(debug=True, port=5000)
