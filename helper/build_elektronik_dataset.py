# helper/build_elektronik_dataset.py
# Ubah hasil capture scrape Tokopedia (produk elektronik) menjadi dataset siap-seed.
#
#   1. Baca capture dari helper/scrape_tokopedia_browser.mjs (CAPTURE_FILES)
#   2. Pilih produk berdasarkan BREADCRUMB KATEGORI ASLI TOKOPEDIA, sehingga
#      yang masuk hanya unit utama (laptop, handphone, TV, ...), bukan aksesoris
#      seperti tas laptop / casing HP yang ikut muncul di hasil pencarian
#   3. Buang barang bekas/refurbish, hadiah "not for sale", dan harga yang
#      tidak masuk akal untuk kategorinya (MIN_PRICE)
#   4. Ambil maksimal PER_CATEGORY produk per kategori (urutan relevansi Tokopedia)
#   5. Unduh foto produk ke revoshop-frontend/public/products/elektronik/<id>.jpg
#      (URL CDN Tokopedia bertanda tangan dan kedaluwarsa, jadi disimpan lokal)
#   6. Tulis helper/data/tokopedia_elektronik.csv
#
# Jalankan:
#   python -m helper.build_elektronik_dataset --dry-run   # hanya tampilkan hasil
#   python -m helper.build_elektronik_dataset             # unduh gambar + tulis CSV

import argparse
import csv
import json
import os
import re
import sys

import requests

HERE = os.path.dirname(__file__)
DATA_DIR = os.path.join(HERE, "data")
CAPTURE_FILES = [
    os.path.join(DATA_DIR, "tokopedia_laptop_unit_capture.json"),
    os.path.join(DATA_DIR, "tokopedia_elektronik_capture.json"),
]
OUT_CSV = os.path.join(DATA_DIR, "tokopedia_elektronik.csv")
FRONTEND_PUBLIC = os.path.abspath(os.path.join(HERE, "..", "..", "revoshop-frontend", "public"))
IMG_DIR = os.path.join(FRONTEND_PUBLIC, "products", "elektronik")
IMG_URL_PREFIX = "/products/elektronik"

MAX_NAME_LEN = 150  # batas kolom products.name
PER_CATEGORY = 8

# Nama yang menandakan produk laptop. Banyak penjual memasang laptop di
# kategori Handphone / Tablet / PC, jadi kategori non-laptop menolak nama ini.
LAPTOP_NAME = r"laptop|macbook|notebook|ideapad|vivobook|zenbook|thinkpad|thkpad|\bmsi (thin|cyborg|modern)|\btuf\b|\brog\b"

# Kategori toko. Produk masuk sebuah kategori hanya jika:
#   - breadcrumb Tokopedia diawali salah satu `breadcrumbs`,
#   - berasal dari pencarian salah satu `keywords`,
#   - namanya cocok `require` (bila ada) dan tidak cocok `reject` (bila ada).
# Urutan = urutan tampil di toko.
CATEGORY_RULES = [
    {
        "name": "Laptop",
        "keywords": ["laptop asus", "laptop lenovo", "macbook"],
        "breadcrumbs": ["komputer-laptop/laptop/"],
        "require": r"laptop|macbook|notebook|ideapad|vivobook|zenbook|thinkpad|yoga|slim",
    },
    {
        "name": "Laptop Gaming",
        "keywords": ["laptop gaming"],
        "breadcrumbs": ["komputer-laptop/pc-laptop-gaming/laptop-gaming"],
        "require": r"gaming|\brog\b|\btuf\b|legion|\bloq\b|nitro|predator|omen|victus|katana|cyborg|rtx",
        # GPU GTX / CPU generasi lama = unit lama yang dijual tanpa label "second"
        "reject": r"\bgtx\b|\bgen ?[4-9]\b|[6-9][0-9]{2}0h\b",
    },
    {
        "name": "Handphone",
        "keywords": ["handphone"],
        "breadcrumbs": ["handphone-tablet/handphone/"],
        "reject": LAPTOP_NAME + r"|\btab\b|\bpad\b|tablet",
    },
    {
        "name": "Tablet",
        "keywords": ["tablet"],
        "breadcrumbs": ["handphone-tablet/tablet/"],
        "require": r"tab|pad|tablet",
        "reject": LAPTOP_NAME,
        # RAM 16GB / storage 512GB-1TB di tablet < Rp3 jt = spesifikasi palsu
        "fake_spec": (r"16 ?gb|512 ?g|1 ?tb", 3_000_000),
    },
    {
        "name": "Televisi",
        "keywords": ["smart tv"],
        "breadcrumbs": ["elektronik/tv-aksesoris/televisi"],
        "require": r"\btv\b|televisi",
    },
    {
        "name": "PC & Komputer",
        "keywords": ["pc desktop"],
        "breadcrumbs": ["komputer-laptop/desktop-mini-pc/", "komputer-laptop/pc-laptop-gaming/pc-gaming"],
        "require": r"\bpc\b|komputer|desktop|all[- ]in[- ]one|\baio\b|mini pc|rakitan|cpu",
        "reject": LAPTOP_NAME,
    },
    {
        "name": "Monitor",
        "keywords": ["monitor"],
        "breadcrumbs": ["komputer-laptop/monitor/monitor-led", "komputer-laptop/monitor/monitor-lcd"],
        "require": r"monitor",
    },
    {
        "name": "Headphone & Audio",
        "keywords": ["headphone"],
        "breadcrumbs": [
            "audio-kamera-elektronik-lainnya/audio/headphone",
            "audio-kamera-elektronik-lainnya/audio/tws",
            "audio-kamera-elektronik-lainnya/audio/earphone",
            "komputer-laptop/aksesoris-pc-gaming/headset-gaming",
        ],
    },
    {
        "name": "Smartwatch",
        "keywords": ["smartwatch"],
        "breadcrumbs": ["handphone-tablet/wearable-devices/smart-watch", "handphone-tablet/wearable-devices/smart-band"],
    },
]
SIMILARITY_THRESHOLD = 0.6  # Jaccard token nama; di atas ini dianggap produk kembar

# Harga minimum wajar per kategori (Rupiah). Di bawah ini hampir pasti
# aksesoris/sparepart yang salah kategori atau harga pancingan.
MIN_PRICE = {
    "Laptop": 2_000_000,
    # Laptop gaming asli (RTX) di Tokopedia mulai ~Rp8 jt; di bawah 7 jt
    # umumnya listing palsu ("ROG i7" seharga 4-6 jt).
    "Laptop Gaming": 7_000_000,
    "Handphone": 500_000,
    "Tablet": 500_000,
    "Televisi": 800_000,
    "PC & Komputer": 1_500_000,
    "Monitor": 500_000,
    "Headphone & Audio": 50_000,
    "Smartwatch": 100_000,
}

EXCLUDE_PATTERNS = [
    r"\bbekas\b", r"\bsecond\b", r"\bseken\b", r"preloved", r"rekondisi",
    r"refurb", r"\bex[ -]?(display|inter|garansi)", r"not for sale",
    r"tidak untuk di ?jual", r"tidak untuk di ?beli", r"\bdummy\b",
    r"\bsparepart\b", r"\bunit only\b.*rusak", r"\brusak\b",
    r"\bmulus\b", r"like new", r"josjis", r"\bbonus untuk pembelian\b",
]


def parse_rupiah(text):
    digits = re.sub(r"[^0-9]", "", text or "")
    return int(digits) if digits else None


def load_products():
    """Gabungkan semua capture, hilangkan duplikat, pertahankan urutan relevansi."""
    products, seen = [], set()
    for path in CAPTURE_FILES:
        with open(path, encoding="utf-8") as f:
            captured = json.load(f)
        for resp in captured:
            body = resp["body"][0] if isinstance(resp["body"], list) else resp["body"]
            for p in body["data"]["searchProductV5"]["data"]["products"]:
                if p["id"] in seen:
                    continue
                seen.add(p["id"])
                p["_keyword"] = resp.get("keyword")
                products.append(p)
    return products


def matches_rule(p, rule):
    """Apakah produk p (dari keyword tertentu) memenuhi aturan kategori `rule`."""
    breadcrumb = p["category"]["breadcrumb"] or ""
    if not any(breadcrumb.startswith(pre) for pre in rule["breadcrumbs"]):
        return False
    lower = p["name"].lower()
    if rule.get("require") and not re.search(rule["require"], lower):
        return False
    if rule.get("reject") and re.search(rule["reject"], lower):
        return False
    if rule.get("fake_spec"):
        pattern, max_price = rule["fake_spec"]
        if re.search(pattern, lower) and p["price"]["number"] < max_price:
            return False
    return True


def exclusion_reason(p, category):
    lower = p["name"].lower()
    for pat in EXCLUDE_PATTERNS:
        if re.search(pat, lower):
            return f"pola '{pat}'"
    price = p["price"]["number"]
    if str(price).strip("9") == "":
        return "harga placeholder 999..."
    if price < MIN_PRICE[category]:
        return f"harga Rp{price:,} < minimum {category}"
    return None


def name_tokens(name):
    """Token nama untuk deteksi produk kembar (abaikan prefix promo [..] / 【..】)."""
    name = re.sub(r"[\[【(][^\]】)]*[\]】)]", " ", name.lower())
    return {t for t in re.findall(r"[a-z0-9]+", name) if len(t) > 1}


def is_near_duplicate(tokens, picked_tokens):
    for other in picked_tokens:
        union = tokens | other
        if union and len(tokens & other) / len(union) >= SIMILARITY_THRESHOLD:
            return True
    return False


def clean_name(name):
    name = re.sub(r"\s+", " ", name).strip()
    if len(name) > MAX_NAME_LEN:
        name = name[: MAX_NAME_LEN - 1].rstrip() + "…"
    return name


def download(url, path):
    resp = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://www.tokopedia.com/"})
    resp.raise_for_status()
    if not resp.headers.get("Content-Type", "").startswith("image/"):
        raise RuntimeError(f"bukan gambar: {resp.headers.get('Content-Type')}")
    with open(path, "wb") as f:
        f.write(resp.content)
    return len(resp.content)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    raw = load_products()
    picked = {rule["name"]: [] for rule in CATEGORY_RULES}
    dropped = []
    used_ids = set()
    picked_tokens = []

    for rule in CATEGORY_RULES:
        category = rule["name"]
        # Kandidat per keyword (urutan relevansi Tokopedia), lalu diambil
        # bergiliran antar keyword supaya merek/model lebih bervariasi.
        queues = [[p for p in raw if p["_keyword"] == kw and matches_rule(p, rule)] for kw in rule["keywords"]]
        while len(picked[category]) < PER_CATEGORY and any(queues):
            for queue in queues:
                if not queue or len(picked[category]) >= PER_CATEGORY:
                    continue
                p = queue.pop(0)
                if p["id"] in used_ids:
                    continue
                reason = exclusion_reason(p, category)
                tokens = name_tokens(p["name"])
                if not reason and is_near_duplicate(tokens, picked_tokens):
                    reason = "produk kembar (nama mirip)"
                if reason:
                    dropped.append((category, p["name"], reason))
                    continue
                used_ids.add(p["id"])
                picked_tokens.append(tokens)
                picked[category].append(to_row(p, category))

    report_and_write(raw, picked, dropped, args.dry_run)


def to_row(p, category):
    return {
        "id": p["oldID"] or p["id"],
        "name": clean_name(p["name"]),
        "price": p["price"]["number"],
        "price_original": parse_rupiah(p["price"]["original"]) or "",
        "rating": p.get("rating") or "",
        "shop_name": p["shop"]["name"],
        "shop_city": p["shop"]["city"],
        "category": category,
        "tokopedia_breadcrumb": p["category"]["breadcrumb"],
        "source_image": p["mediaURL"]["image300"] or p["mediaURL"]["image"],
        "product_url": p["url"].split("?")[0],
    }


def report_and_write(raw, picked, dropped, dry_run):
    kept = [item for items in picked.values() for item in items]
    print(f"Total produk unik di capture : {len(raw)}")
    print(f"Dibuang (dari kandidat)      : {len(dropped)}")
    for cat, name, reason in dropped:
        print(f"   x [{cat}] {reason}: {name[:70]}")
    print(f"Dipakai                      : {len(kept)}")
    for cat, items in picked.items():
        print(f"\n[{cat}] {len(items)} produk")
        for k in items:
            print(f"   Rp{k['price']:>11,}  {k['name'][:72]}")
            print(f"                  {k['tokopedia_breadcrumb']}")

    short = [cat for cat, items in picked.items() if len(items) < PER_CATEGORY]
    if short:
        print(f"\n! Kategori kurang dari {PER_CATEGORY} produk: {short}")
    if dry_run:
        print("\n(dry-run: tidak ada file yang ditulis)")
        return

    os.makedirs(IMG_DIR, exist_ok=True)
    for k in kept:
        filename = f"{k['id']}.jpg"
        size = download(k["source_image"], os.path.join(IMG_DIR, filename))
        k["image_url"] = f"{IMG_URL_PREFIX}/{filename}"
        print(f"  img {filename} ({size // 1024} KB)")

    fields = ["name", "price", "price_original", "rating", "shop_name", "shop_city",
              "category", "tokopedia_breadcrumb", "image_url", "product_url"]
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(kept)
    print(f"\n+ {len(kept)} produk -> {os.path.relpath(OUT_CSV)}")
    print(f"+ gambar -> {IMG_DIR}")


if __name__ == "__main__":
    main()
