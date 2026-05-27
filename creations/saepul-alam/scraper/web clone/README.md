# 🌐 Web Cloner

> Download & clone seluruh website untuk offline viewing — mirip [saveweb2zip.com](https://saveweb2zip.com) tapi jalan di lokal kamu sendiri.

Mendukung crawl HTML biasa **+** mode **Path Bruteforce** untuk menemukan file yang tidak ter-link di halaman manapun.

---

## ✨ Fitur

- **Crawl rekursif** — ikuti semua link HTML, CSS, JS, gambar, font, video, dll.
- **Rewrite URL otomatis** — semua link diubah ke path relatif, bisa langsung dibuka offline
- **Auto ZIP** — hasil langsung dipack jadi `.zip` siap kirim/backup
- **Path Bruteforce** — coba 250+ path umum (`/admin`, `/uploads/`, `.env`, dll.) untuk temukan file yang tidak ter-link
- **Directory listing parser** — kalau server punya open directory, semua file di dalamnya ikut didownload
- **Thread paralel** — bruteforce jalan dengan banyak thread sekaligus, lebih cepat
- **Filter URL cerdas** — tidak lagi salah ambil nilai meta tag (`keywords`, `viewport`, dll.) sebagai URL
- **robots.txt** — bisa ikuti atau abaikan sesuai kebutuhan
- **Retry otomatis** — request gagal otomatis dicoba ulang sampai 3 kali

---

## 📦 Instalasi

### 1. Pastikan Python 3.10+ terinstall

```bash
python --version
# Python 3.10.x atau lebih baru
```

### 2. Install dependency

```bash
pip install requests beautifulsoup4
```

### 3. Download script

Simpan file `web_cloner.py` ke folder mana saja, lalu jalankan via terminal.

---

## 🚀 Cara Pakai

### Crawl biasa (paling simpel)

```bash
python web_cloner.py https://websitekamu.com
```

### Aktifkan bruteforce — temukan file tersembunyi

```bash
python web_cloner.py https://websitekamu.com --bruteforce
```

### Bruteforce saja (skip crawl normal)

```bash
python web_cloner.py https://websitekamu.com --bf-only
```

### Crawl dalam + bruteforce + lebih banyak thread

```bash
python web_cloner.py https://websitekamu.com --depth 5 --pages 1000 --bruteforce --bf-threads 20
```

### Tanpa ZIP (lebih cepat, lihat filenya langsung)

```bash
python web_cloner.py https://websitekamu.com --no-zip
```

---

## ⚙️ Semua Opsi

| Opsi | Pendek | Default | Keterangan |
|---|---|---|---|
| `url` | | *(wajib)* | URL website target |
| `--depth` | `-d` | `3` | Kedalaman crawl maksimum |
| `--pages` | `-p` | `500` | Batas halaman HTML yang di-download |
| `--delay` | | `0.3` | Jeda antar request (detik) |
| `--timeout` | | `12` | Timeout per request (detik) |
| `--output` | `-o` | `output` | Folder hasil download |
| `--no-zip` | | off | Jangan buat file ZIP |
| `--no-robots` | | off | Abaikan aturan `robots.txt` |
| `--allow-external` | | off | Download aset dari domain lain |
| `--max-url` | | `500` | Batas panjang URL yang diterima |
| `--bruteforce` | `-b` | off | Aktifkan path bruteforce |
| `--bf-only` | | off | Hanya bruteforce, skip crawl normal |
| `--bf-threads` | | `10` | Jumlah thread paralel bruteforce |
| `--bf-delay` | | `0.1` | Jeda per request bruteforce (detik) |
| `--user-agent` | | Chrome | Custom User-Agent string |

---

## 📁 Struktur Output

```
output/
└── websitekamu.com/
    ├── index.html              ← buka ini di browser untuk lihat offline
    ├── about.html
    ├── login.html
    ├── assets/
    │   ├── style.css
    │   ├── main.js
    │   └── logo.png
    ├── uploads/
    │   └── foto-produk.jpg
    └── ...
websitekamu.com.zip             ← ZIP siap kirim / backup
```

Semua link di HTML & CSS sudah otomatis diubah ke path relatif, jadi cukup buka `index.html` di browser dan website bisa dilihat offline tanpa perlu server.

---

## 🔍 Path Bruteforce — Detail

Mode bruteforce mencoba **250+ path umum** secara paralel menggunakan thread pool. Cocok untuk menemukan file yang tidak ter-link dari halaman manapun.

### Apa saja yang dicoba?

| Kategori | Jumlah | Contoh |
|---|---|---|
| Halaman umum | ~30 | `/about`, `/contact`, `/login`, `/register` |
| File PHP | ~70 | `config.php`, `upload.php`, `admin.php`, `auth.php` |
| Folder umum | ~98 | `/uploads/`, `/images/`, `/assets/`, `/backup/` |
| File konfigurasi | ~24 | `.env`, `.htaccess`, `web.config`, `composer.json` |
| CMS (WP/Joomla/Drupal) | ~15 | `/wp-admin/`, `/wp-content/uploads/`, `/administrator/` |
| Root assets | ~20 | `logo.png`, `style.css`, `main.js`, `favicon.ico` |

### Directory Listing

Jika server mengaktifkan directory listing (Apache/Nginx tanpa `Options -Indexes`), script akan otomatis parse semua file yang tampil dan mendownloadnya satu per satu.

```
[BF   1] ✅ 200  https://site.com/uploads/            [?]
[DIR] 📂 https://site.com/uploads/  →  47 file/subdir ditemukan
```

---

## 📋 Contoh Output Terminal

```
═════════════════════════════════════════════════════════════════
  🌐  Web Cloner  —  https://websitekamu.com
═════════════════════════════════════════════════════════════════
  Output     : output
  Domain     : websitekamu.com
  Max Depth  : 3
  Max Pages  : 500
  Bruteforce : ✅ ON
─────────────────────────────────────────────────────────────────

  [   1] (d=0) https://websitekamu.com
  [   A] (d=1) https://websitekamu.com/assets/style.css
  [   A] (d=1) https://websitekamu.com/assets/main.js
  [   2] (d=1) https://websitekamu.com/about
  [   3] (d=1) https://websitekamu.com/login
  ...

═════════════════════════════════════════════════════════════════
  🔍  BRUTEFORCE PATH SCAN  —  https://websitekamu.com
═════════════════════════════════════════════════════════════════
  Total path yang dicoba : 250
  Thread paralel         : 10
─────────────────────────────────────────────────────────────────

  [BF    1] ✅ 200  https://websitekamu.com/uploads/      [?]
  [DIR] 📂 https://websitekamu.com/uploads/  →  23 file ditemukan
  [BF    2] ✅ 200  https://websitekamu.com/config.php    [2.1 KB]
  [BF    3] ✅ 200  https://websitekamu.com/.htaccess     [0.4 KB]
  ...

─────────────────────────────────────────────────────────────────
  ✅  312 file tersimpan  (18.45 MB)
  📁  Lokasi: output/websitekamu.com
  📦  Membuat ZIP → output/websitekamu.com.zip ...
  ✅  ZIP selesai  (14.20 MB)
═════════════════════════════════════════════════════════════════
```

---

## ⚠️ Keterbatasan

Beberapa file **tidak bisa** diambil hanya dengan crawler, meski bruteforce aktif:

- **File dengan nama random** — contoh: `/uploads/a7f3d9b2.jpg` (nama tidak bisa ditebak)
- **Halaman login-protected** — konten yang butuh autentikasi
- **Data dari database** — konten yang di-generate secara dinamis
- **JavaScript-rendered content** — SPA (React/Vue/Angular) yang render konten via JS setelah load

Untuk kasus ini, satu-satunya cara adalah dengan recover akses hosting (cPanel/FTP).

---

## 🔑 Cara Recover Akses Hosting (Jika Lupa Password)

Jika tujuan kamu menggunakan tool ini adalah untuk backup website karena lupa password hosting, coba langkah berikut:

1. **Cek saved password di browser**
   - Chrome: buka `chrome://password-manager/passwords`
   - Edge: buka `edge://passwords`

2. **Cek FTP client lama**
   - FileZilla: *Edit → Settings → Saved Sites*
   - WinSCP / CyberDuck: cek saved sessions

3. **Recover email hosting dulu**
   - Gmail: `accounts.google.com/signin/recovery`
   - Setelah email bisa diakses, baru reset password hosting

4. **Hubungi support hosting**
   - Siapkan: KTP, invoice/bukti bayar, nama domain
   - Minta reset password via verifikasi identitas

---

## 🛡️ Etika Penggunaan

Tool ini dibuat untuk keperluan **backup website milik sendiri**. Penggunaan yang diizinkan:

- ✅ Backup website milik sendiri
- ✅ Arsip halaman publik untuk keperluan riset/dokumentasi
- ✅ Mirror website dengan izin pemilik
- ❌ Scraping website orang lain tanpa izin
- ❌ Melanggar Terms of Service website target
- ❌ Menggunakan hasil untuk tujuan ilegal

Selalu hormati `robots.txt` dan ToS website target.

---

## 📄 Lisensi

MIT License — bebas digunakan, dimodifikasi, dan didistribusikan.
