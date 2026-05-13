import sqlite3
import os
import hashlib
import secrets

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "parknavetvi.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000)
    return f"{salt}${hashed.hex()}"


def verify_password(password, stored):
    salt = stored.split("$")[0]
    return hash_password(password, salt) == stored


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            image TEXT,
            published INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS instagram_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            instagram_url TEXT NOT NULL,
            image TEXT NOT NULL,
            sort_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gallery_images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            alt TEXT,
            image TEXT NOT NULL,
            sort_order INTEGER DEFAULT 0,
            published INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pricing_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            category_note TEXT,
            label TEXT NOT NULL,
            price TEXT NOT NULL,
            sort_order INTEGER DEFAULT 0,
            featured INTEGER DEFAULT 0,
            published INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            ("admin", hash_password("parknavetvi2026")),
        )

    defaults = {
        "site_name": "Park Na Větvi",
        "site_subtitle": "Lanové centrum v korunách stromů v Hradci Králové",
        "phone": "+420 722 912 565",
        "email": "info@parknavetvi.cz",
        "address": "Zeyerova 758/12, 500 02 Hradec Králové",
        "hours": "9:00 – 19:00",
        "eshop_url": "https://www.parknavetvi.cz/vstupenky",
        "facebook_url": "",
        "instagram_url": "https://www.instagram.com/navetvi_hk/",
        "instagram_token": "",
        "instagram_last_fetch": "0",
        "hero_text": "Oblíbené místo pro dětské oslavy. Platba v hotovosti i kartou. Otevřeno celoročně.",
        "about_text": "Park Na Větvi tvoří unikátní soustava tří síťových hřišť zavěšených v korunách stromů propojených s 3D bludištěm, které je složeno ze síťových překážkových drah rozprostřených ve třech patrech nad sebou. Síťové bludiště v korunách stromů obsahuje mnoho zábavných prvků, které otestují vaše motorické dovednosti. Jednotlivé herní plochy jsou propojeny visutými lávkami. Celá atrakce vrcholí sjezdem unikátním tobogánem z výšky necelých 10 m. Pohybová atrakce je natolik bezpečná, že na rozdíl od klasických lanových center nevyžaduje žádné osobní lanové jištění.",
        "ico": "08798206",
        "home_about_title": "Dobrodružství v korunách stromů",
        "home_instagram_title": "Sledujte nás",
        "home_instagram_subtitle": "@navetvi_hk na Instagramu",
        "home_pricing_title": "Vstupné",
        "home_pricing_subtitle": "Ceník vstupného do Parku Na Větvi",
        "home_cta_title": "Přijďte si užít dobrodružství",
        "home_cta_button": "Navštívit e-shop",
        "about_page_title": "O parku",
        "about_page_subtitle": "Poznejte unikátní lanové centrum v korunách stromů",
        "about_intro_extra": "Vstupné platĂ­ po celĂ˝ den bez ÄŤasovĂ©ho omezenĂ­ â€“ areĂˇl je moĹľnĂ© opustit a znovu se vrĂˇtit. DospÄ›lĂ˝ doprovod k dÄ›tem do 6 let je zdarma. DoporuÄŤenĂ˝ vstup od 3 let.",
        "about_map_title": "Mapa areálu",
        "about_map_subtitle": "Tři síťová hřiště propojená s 3D bludištěm ve třech patrech",
        "about_gallery_title": "Galerie",
        "about_gallery_subtitle": "Podívejte se, jak to u nás vypadá",
        "about_info_title": "Praktické informace",
        "about_info_subtitle": "Vše, co potřebujete vědět před návštěvou",
        "about_cta_title": "Přijďte to zažít na vlastní kůži",
        "about_cta_text": "Vstupenky lze zakoupit přímo v areálu nebo online.",
        "pricing_page_title": "Vstupné",
        "pricing_page_subtitle": "Ceník vstupného do Parku Na Větvi",
        "pricing_info_text": "Vstupné platĂ­ po celĂ˝ den bez ÄŤasovĂ©ho omezenĂ­ â€“ areĂˇl je moĹľnĂ© opustit a znovu se vrĂˇtit.\nDospÄ›lĂ˝ doprovod k dÄ›tem do 6 let je zdarma. DoporuÄŤenĂ˝ vstup od 3 let.\nVĹˇechny vstupenky lze zakoupit na mĂ­stÄ› v areĂˇlu parku ve stĂˇnku s obÄŤerstvenĂ­m. PĹ™ijĂ­mĂˇme platebnĂ­ karty.",
        "pricing_button_text": "Koupit vstupenky online",
        "contact_page_title": "Kontakt",
        "contact_page_subtitle": "Jak se k nám dostanete a kde nás najdete",
        "contact_transport": "Zastávka MHD Zděná Bouda (linky 21, 27)",
        "contact_operator_title": "Provozovatel",
        "contact_grant_text": "Park Na Větvi byl vytvořen za přispění prostředků státního rozpočtu České republiky z programu Ministerstva pro místní rozvoj.",
        "eshop_page_title": "E-shop",
        "eshop_page_subtitle": "Online prodej vstupenek připravujeme",
        "eshop_soon_title": "Již brzy",
        "eshop_soon_text": "Připravujeme pro vás pohodlný online nákup vstupenek.",
        "company_name": "Park Na Větvi provozní s.r.o.",
    }

    for key, value in defaults.items():
        cursor.execute(
            "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
            (key, value),
        )

    cursor.execute("SELECT COUNT(*) FROM gallery_images")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            "INSERT INTO gallery_images (title, alt, image, sort_order, published) VALUES (?, ?, ?, ?, 1)",
            [
                ("Síťové hřiště", "Síťové hřiště v korunĂˇch stromĹŻ", "park/hero-bg.jpg", 1),
                ("Tobogán", "Tobogán a visutĂˇ lĂˇvka", "park/bg_03.jpg", 2),
            ],
        )

    cursor.execute("SELECT COUNT(*) FROM pricing_items")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            """
            INSERT INTO pricing_items
                (category, category_note, label, price, sort_order, featured, published)
            VALUES (?, ?, ?, ?, ?, ?, 1)
            """,
            [
                ("Dětské vstupné", "do 18 let", "Dítě do 100 cm", "zdarma", 1, 0),
                ("Dětské vstupné", "do 18 let", "1 dítě", "290 Kč", 2, 0),
                ("Dětské vstupné", "do 18 let", "2 děti", "500 Kč", 3, 0),
                ("Dětské vstupné", "do 18 let", "3 děti", "650 Kč", 4, 0),
                ("Dětské vstupné", "do 18 let", "Každé další dítě", "+200 Kč", 5, 0),
                ("Rodinné vstupné", "dospělý + dítě", "1+1", "440 Kč", 10, 1),
                ("Rodinné vstupné", "dospělý + dítě", "1+2", "600 Kč", 11, 1),
                ("Rodinné vstupné", "dospělý + dítě", "1+3", "750 Kč", 12, 1),
                ("Rodinné vstupné", "dospělý + dítě", "2+1", "490 Kč", 13, 1),
                ("Rodinné vstupné", "dospělý + dítě", "2+2", "700 Kč", 14, 1),
                ("Rodinné vstupné", "dospělý + dítě", "2+3", "800 Kč", 15, 1),
                ("Ostatní vstupné", "", "Dospělý nad 18 let", "290 Kč", 20, 0),
                ("Ostatní vstupné", "", "Skupina 15 a více", "150 Kč/os.", 21, 0),
                ("Ostatní vstupné", "", "Vstup po 18. hodině", "100 Kč", 22, 0),
                ("Ostatní vstupné", "", "ZTP", "100 Kč", 23, 0),
                ("Ostatní vstupné", "", "Permanentka", "2 900 Kč", 24, 0),
            ],
        )

    conn.commit()
    conn.close()


def get_settings():
    conn = get_db()
    rows = conn.execute("SELECT key, value FROM settings").fetchall()
    conn.close()
    return {row["key"]: row["value"] for row in rows}


def update_setting(key, value):
    conn = get_db()
    conn.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value)
    )
    conn.commit()
    conn.close()


def repair_czech_texts():
    fixes = {
        "site_name": "Park Na Větvi",
        "site_subtitle": "Lanové centrum v korunách stromů v Hradci Králové",
        "address": "Zeyerova 758/12, 500 02 Hradec Králové",
        "hours": "9:00 - 19:00",
        "hero_text": "Oblíbené místo pro dětské oslavy. Platba v hotovosti i kartou. Otevřeno celoročně.",
        "about_text": "Park Na Větvi tvoří unikátní soustava tří síťových hřišť zavěšených v korunách stromů propojených s 3D bludištěm, které je složeno ze síťových překážkových drah rozprostřených ve třech patrech nad sebou. Síťové bludiště v korunách stromů obsahuje mnoho zábavných prvků, které otestují vaše motorické dovednosti. Jednotlivé herní plochy jsou propojeny visutými lávkami. Celá atrakce vrcholí sjezdem unikátním tobogánem z výšky necelých 10 m. Pohybová atrakce je natolik bezpečná, že na rozdíl od klasických lanových center nevyžaduje žádné osobní lanové jištění.",
        "company_name": "Park Na Větvi provozní s.r.o.",
        "home_about_title": "Dobrodružství v korunách stromů",
        "home_instagram_title": "Sledujte nás",
        "home_instagram_subtitle": "@navetvi_hk na Instagramu",
        "home_pricing_title": "Vstupné",
        "home_pricing_subtitle": "Ceník vstupného do Parku Na Větvi",
        "home_cta_title": "Přijďte si užít dobrodružství",
        "home_cta_button": "Navštívit e-shop",
        "about_page_title": "O parku",
        "about_page_subtitle": "Poznejte unikátní lanové centrum v korunách stromů",
        "about_intro_extra": "Vstupné platí po celý den bez časového omezení - areál je možné opustit a znovu se vrátit. Dospělý doprovod k dětem do 6 let je zdarma. Doporučený vstup od 3 let.",
        "about_map_title": "Mapa areálu",
        "about_map_subtitle": "Tři síťová hřiště propojená s 3D bludištěm ve třech patrech",
        "about_gallery_title": "Galerie",
        "about_gallery_subtitle": "Podívejte se, jak to u nás vypadá",
        "about_info_title": "Praktické informace",
        "about_info_subtitle": "Vše, co potřebujete vědět před návštěvou",
        "about_cta_title": "Přijďte to zažít na vlastní kůži",
        "about_cta_text": "Vstupenky lze zakoupit přímo v areálu nebo online.",
        "pricing_page_title": "Vstupné",
        "pricing_page_subtitle": "Ceník vstupného do Parku Na Větvi",
        "pricing_info_text": "Vstupné platí po celý den bez časového omezení - areál je možné opustit a znovu se vrátit.\nDospělý doprovod k dětem do 6 let je zdarma. Doporučený vstup od 3 let.\nVšechny vstupenky lze zakoupit na místě v areálu parku ve stánku s občerstvením. Přijímáme platební karty.",
        "pricing_button_text": "Koupit vstupenky online",
        "contact_page_title": "Kontakt",
        "contact_page_subtitle": "Jak se k nám dostanete a kde nás najdete",
        "contact_transport": "Zastávka MHD Zděná Bouda (linky 21, 27)",
        "contact_operator_title": "Provozovatel",
        "contact_grant_text": "Park Na Větvi byl vytvořen za přispění prostředků státního rozpočtu České republiky z programu Ministerstva pro místní rozvoj.",
        "eshop_page_title": "E-shop",
        "eshop_page_subtitle": "Online prodej vstupenek připravujeme",
        "eshop_soon_title": "Již brzy",
        "eshop_soon_text": "Připravujeme pro vás pohodlný online nákup vstupenek.",
    }
    conn = get_db()
    for key, value in fixes.items():
        conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value),
        )
    conn.execute("UPDATE gallery_images SET title=?, alt=? WHERE image=?", ("Síťové hřiště", "Síťové hřiště v korunách stromů", "park/hero-bg.jpg"))
    conn.execute("UPDATE gallery_images SET title=?, alt=? WHERE image=?", ("Tobogán", "Tobogán a visutá lávka", "park/bg_03.jpg"))
    pricing_fixes = [
        ("Dětské vstupné", "do 18 let", "Dítě do 100 cm", "zdarma", 1),
        ("Dětské vstupné", "do 18 let", "1 dítě", "290 Kč", 2),
        ("Dětské vstupné", "do 18 let", "2 děti", "500 Kč", 3),
        ("Dětské vstupné", "do 18 let", "3 děti", "650 Kč", 4),
        ("Dětské vstupné", "do 18 let", "Každé další dítě", "+200 Kč", 5),
        ("Rodinné vstupné", "dospělý + dítě", "1+1", "440 Kč", 10),
        ("Rodinné vstupné", "dospělý + dítě", "1+2", "600 Kč", 11),
        ("Rodinné vstupné", "dospělý + dítě", "1+3", "750 Kč", 12),
        ("Rodinné vstupné", "dospělý + dítě", "2+1", "490 Kč", 13),
        ("Rodinné vstupné", "dospělý + dítě", "2+2", "700 Kč", 14),
        ("Rodinné vstupné", "dospělý + dítě", "2+3", "800 Kč", 15),
        ("Ostatní vstupné", "", "Dospělý nad 18 let", "290 Kč", 20),
        ("Ostatní vstupné", "", "Skupina 15 a více", "150 Kč/os.", 21),
        ("Ostatní vstupné", "", "Vstup po 18. hodině", "100 Kč", 22),
        ("Ostatní vstupné", "", "ZTP", "100 Kč", 23),
        ("Ostatní vstupné", "", "Permanentka", "2 900 Kč", 24),
    ]
    for category, note, label, price, sort_order in pricing_fixes:
        conn.execute(
            "UPDATE pricing_items SET category=?, category_note=?, label=?, price=? WHERE sort_order=?",
            (category, note, label, price, sort_order),
        )
    conn.commit()
    conn.close()


def get_news(published_only=True, limit=None):
    conn = get_db()
    query = "SELECT * FROM news"
    if published_only:
        query += " WHERE published = 1"
    query += " ORDER BY created_at DESC"
    if limit:
        query += f" LIMIT {int(limit)}"
    rows = conn.execute(query).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_news_by_id(news_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM news WHERE id = ?", (news_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def create_news(title, content, image=None, published=1):
    conn = get_db()
    conn.execute(
        "INSERT INTO news (title, content, image, published) VALUES (?, ?, ?, ?)",
        (title, content, image, published),
    )
    conn.commit()
    conn.close()


def update_news(news_id, title, content, image=None, published=1):
    conn = get_db()
    if image is not None:
        conn.execute(
            "UPDATE news SET title=?, content=?, image=?, published=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (title, content, image, published, news_id),
        )
    else:
        conn.execute(
            "UPDATE news SET title=?, content=?, published=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (title, content, published, news_id),
        )
    conn.commit()
    conn.close()


def delete_news(news_id):
    conn = get_db()
    conn.execute("DELETE FROM news WHERE id = ?", (news_id,))
    conn.commit()
    conn.close()


def get_instagram_posts():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM instagram_posts ORDER BY sort_order ASC, created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_instagram_post_by_id(post_id):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM instagram_posts WHERE id = ?", (post_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def create_instagram_post(instagram_url, image, sort_order=0):
    conn = get_db()
    conn.execute(
        "INSERT INTO instagram_posts (instagram_url, image, sort_order) VALUES (?, ?, ?)",
        (instagram_url, image, sort_order),
    )
    conn.commit()
    conn.close()


def delete_instagram_post(post_id):
    conn = get_db()
    conn.execute("DELETE FROM instagram_posts WHERE id = ?", (post_id,))
    conn.commit()
    conn.close()


def get_gallery_images(published_only=True):
    conn = get_db()
    query = "SELECT * FROM gallery_images"
    if published_only:
        query += " WHERE published = 1"
    query += " ORDER BY sort_order ASC, created_at DESC"
    rows = conn.execute(query).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_gallery_image_by_id(image_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM gallery_images WHERE id = ?", (image_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def create_gallery_image(title, alt, image, sort_order=0, published=1):
    conn = get_db()
    conn.execute(
        "INSERT INTO gallery_images (title, alt, image, sort_order, published) VALUES (?, ?, ?, ?, ?)",
        (title, alt, image, sort_order, published),
    )
    conn.commit()
    conn.close()


def update_gallery_image(image_id, title, alt, sort_order=0, published=1, image=None):
    conn = get_db()
    if image is None:
        conn.execute(
            "UPDATE gallery_images SET title=?, alt=?, sort_order=?, published=? WHERE id=?",
            (title, alt, sort_order, published, image_id),
        )
    else:
        conn.execute(
            "UPDATE gallery_images SET title=?, alt=?, image=?, sort_order=?, published=? WHERE id=?",
            (title, alt, image, sort_order, published, image_id),
        )
    conn.commit()
    conn.close()


def delete_gallery_image(image_id):
    conn = get_db()
    conn.execute("DELETE FROM gallery_images WHERE id = ?", (image_id,))
    conn.commit()
    conn.close()


def get_pricing_items(published_only=True):
    conn = get_db()
    query = "SELECT * FROM pricing_items"
    if published_only:
        query += " WHERE published = 1"
    query += " ORDER BY sort_order ASC, id ASC"
    rows = conn.execute(query).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_pricing_item_by_id(item_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM pricing_items WHERE id = ?", (item_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def create_pricing_item(category, category_note, label, price, sort_order=0, featured=0, published=1):
    conn = get_db()
    conn.execute(
        """
        INSERT INTO pricing_items
            (category, category_note, label, price, sort_order, featured, published)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (category, category_note, label, price, sort_order, featured, published),
    )
    conn.commit()
    conn.close()


def update_pricing_item(item_id, category, category_note, label, price, sort_order=0, featured=0, published=1):
    conn = get_db()
    conn.execute(
        """
        UPDATE pricing_items
        SET category=?, category_note=?, label=?, price=?, sort_order=?, featured=?, published=?
        WHERE id=?
        """,
        (category, category_note, label, price, sort_order, featured, published, item_id),
    )
    conn.commit()
    conn.close()


def delete_pricing_item(item_id):
    conn = get_db()
    conn.execute("DELETE FROM pricing_items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
