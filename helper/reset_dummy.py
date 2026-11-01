# helper/reset_dummy.py
# Hapus data DUMMY lama supaya toko hanya berisi data real hasil scrape Tokopedia.
#
# Data real = 6 kategori berikut beserta produknya; SELALU dipertahankan:
#   Laptop, Mouse, Keyboard, Tas & Sleeve Laptop, Aksesoris Komputer, Komponen & Pendingin
#
# Semua kategori/produk DI LUAR daftar itu dianggap dummy.
#
# Mode:
#   python -m helper.reset_dummy
#       -> AMAN. Hanya hapus produk dummy yang TIDAK dipakai order,
#          lalu hapus kategori dummy yang menjadi kosong.
#          Produk dummy yang masih direferensikan order dibiarkan (histori utuh).
#
#   python -m helper.reset_dummy --force
#       -> DESTRUKTIF. Hapus SEMUA data dummy, termasuk baris order_items
#          yang mereferensikannya. Order yang jadi kosong ikut dihapus.
#          Dipakai hanya jika Anda yakin histori order dummy boleh hilang.

import sys

from app import app
from extensions import db
from models import Product, Category, Order, order_items


# Kategori data real yang wajib dipertahankan.
REAL_CATEGORIES = {
    "Laptop",
    "Mouse",
    "Keyboard",
    "Tas & Sleeve Laptop",
    "Aksesoris Komputer",
    "Komponen & Pendingin",
}


def _dummy_category_ids():
    cats = Category.query.all()
    return [c for c in cats if c.name not in REAL_CATEGORIES]


def _product_ids_used_in_orders():
    rows = db.session.execute(
        db.text("SELECT DISTINCT product_id FROM order_items")
    ).fetchall()
    return {r[0] for r in rows}


def reset_safe():
    """Hapus hanya produk dummy yang tidak dipakai order + kategori dummy kosong."""
    dummy_cats = _dummy_category_ids()
    if not dummy_cats:
        print("  Tidak ada kategori dummy. Database sudah bersih.")
        return

    dummy_cat_ids = [c.id for c in dummy_cats]
    dummy_products = Product.query.filter(Product.category_id.in_(dummy_cat_ids)).all()
    used_ids = _product_ids_used_in_orders()

    deleted_products = 0
    kept_products = 0
    for p in dummy_products:
        if p.id in used_ids:
            kept_products += 1
            print(f"  - Produk '{p.name[:40]}' dipakai order, DIPERTAHANKAN")
        else:
            db.session.delete(p)
            deleted_products += 1
            print(f"  x Produk '{p.name[:40]}' dihapus")

    db.session.flush()

    # Hapus kategori dummy yang sudah tidak punya produk sama sekali.
    deleted_cats = 0
    for c in dummy_cats:
        remaining = Product.query.filter_by(category_id=c.id).count()
        if remaining == 0:
            db.session.delete(c)
            deleted_cats += 1
            print(f"  x Kategori '{c.name}' dihapus (kosong)")
        else:
            print(f"  - Kategori '{c.name}' masih punya {remaining} produk, DIPERTAHANKAN")

    db.session.commit()
    print(f"\n  Ringkasan: {deleted_products} produk dihapus, "
          f"{kept_products} dipertahankan, {deleted_cats} kategori dihapus.")
    if kept_products:
        print("  Catatan: ada produk dummy yang masih dipakai order. "
              "Jalankan dengan --force untuk menghapus paksa beserta order terkait.")


def reset_force():
    """Hapus SEMUA data dummy, termasuk order_items dan order yang jadi kosong."""
    dummy_cats = _dummy_category_ids()
    if not dummy_cats:
        print("  Tidak ada kategori dummy. Database sudah bersih.")
        return

    dummy_cat_ids = [c.id for c in dummy_cats]
    dummy_products = Product.query.filter(Product.category_id.in_(dummy_cat_ids)).all()
    dummy_product_ids = [p.id for p in dummy_products]

    # 1. Catat order yang menyentuh produk dummy (untuk cek kosong nanti).
    affected_order_ids = set()
    if dummy_product_ids:
        rows = db.session.execute(
            order_items.select().where(order_items.c.product_id.in_(dummy_product_ids))
        ).fetchall()
        affected_order_ids = {r.order_id for r in rows}

        # 2. Hapus baris order_items yang mereferensikan produk dummy.
        result = db.session.execute(
            order_items.delete().where(order_items.c.product_id.in_(dummy_product_ids))
        )
        print(f"  x {result.rowcount} baris order_items dihapus")

    db.session.flush()

    # 3. Hapus produk dummy.
    for p in dummy_products:
        db.session.delete(p)
    print(f"  x {len(dummy_products)} produk dummy dihapus")

    # 4. Hapus kategori dummy.
    for c in dummy_cats:
        db.session.delete(c)
    print(f"  x {len(dummy_cats)} kategori dummy dihapus")

    db.session.flush()

    # 5. Hapus order yang jadi kosong (tidak punya item sama sekali).
    deleted_orders = 0
    for oid in affected_order_ids:
        remaining = db.session.execute(
            db.text("SELECT COUNT(*) FROM order_items WHERE order_id = :oid"),
            {"oid": oid},
        ).scalar()
        if remaining == 0:
            order = Order.query.get(oid)
            if order:
                db.session.delete(order)
                deleted_orders += 1
    print(f"  x {deleted_orders} order kosong dihapus")

    db.session.commit()
    print("\n  Ringkasan: semua data dummy + referensi order-nya telah dibersihkan.")


def run():
    force = "--force" in sys.argv

    with app.app_context():
        print("\n=== Reset Data Dummy ===\n")
        if force:
            print("Mode: --force (DESTRUKTIF terhadap histori order dummy)\n")
            reset_force()
        else:
            print("Mode: aman (hanya hapus produk dummy yang tidak dipakai order)\n")
            reset_safe()

        # Laporan akhir
        print("\n[Status akhir]")
        print(f"  Kategori total : {Category.query.count()}")
        print(f"  Produk total   : {Product.query.count()}")
        print("\n=== Selesai ===\n")


if __name__ == "__main__":
    run()
