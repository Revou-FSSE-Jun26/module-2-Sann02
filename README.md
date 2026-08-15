# RevoShop Backend System

Repository ini berisi skema database dan logika backend untuk RevoShop.

## Checkpoint 1: Database Setup

### Cara Menjalankan Database Secara Lokal:
1. Buat database baru bernama `revoushop_db` di PostgreSQL (bisa via pgAdmin/DBeaver).
2. Buka Query Tool pada database tersebut.
3. Jalankan script dari file `schema.sql` untuk membuat struktur tabel.
4. Jalankan script dari file `seed.sql` untuk memasukkan data dummy.
5. Jalankan script dari `queries.sql` untuk menguji pengambilan data (menampilkan 2 produk termahal yang ready stock).