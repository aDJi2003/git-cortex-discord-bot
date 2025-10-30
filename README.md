# Git Cortex Bot

Git Cortex Bot adalah AI Agent cerdas yang dirancang untuk merangkum dan menganalisis repositori GitHub langsung dari server Discord Anda. Ucapkan selamat tinggal pada waktu yang terbuang untuk membaca dokumentasi panjang dan menelusuri struktur proyek yang kompleks.

## Demo

Berikut adalah contoh interaksi dengan Git Cortex Bot di Discord. Bot akan menganalisis URL repositori yang diberikan dan memberikan ringkasan komprehensif.

*(Catatan: Ganti file ini dengan GIF atau screenshot demo Anda sendiri di dalam folder `images`)*

## Latar Belakang

Developer menghabiskan hampir **60% waktu kerja** mereka hanya untuk memahami kode dan dokumentasi yang ada. Proses manual ini—membaca README, melacak file konfigurasi, memahami arsitektur, dan mencari contoh—sangat tidak efisien dan rentan terhadap kesalahan. Git Cortex Bot hadir untuk mengatasi masalah ini dengan mengotomatiskan proses "onboarding" ke repositori baru, sehingga Anda bisa fokus pada hal yang paling penting: **menulis kode**.

## Fitur Utama

- 📄 **Ringkasan README**: Mendapatkan inti dari sebuah proyek tanpa membaca keseluruhan dokumentasi.
- 📂 **Analisis Struktur Repositori**: Memvisualisasikan tata letak direktori dan file-file penting.
- 📦 **Deteksi Dependensi**: Mengidentifikasi dependensi proyek (misalnya dari `package.json` atau `requirements.txt`) secara otomatis.
- 🔍 **Pembacaan File**: Mampu membaca konten dari file tertentu di dalam repositori untuk analisis lebih dalam.
- ⚙️ **Identifikasi Teknologi**: Mengetahui bahasa pemrograman dan tumpukan teknologi yang digunakan.
- 📝 **Laporan PDF**: Menghasilkan laporan PDF terstruktur dari hasil analisis untuk dokumentasi dan berbagi.

## Setup & Menjalankan Bot

Untuk menjalankan Git Cortex Bot di lingkungan lokal Anda, ikuti langkah-langkah berikut.

### Prasyarat

- Python 3.9+
- Git

### 1. Kloning Repositori

```bash
git clone [https://github.com/your-username/git-cortex-bot.git](https://github.com/your-username/git-cortex-bot.git)
cd git-cortex-bot
```

### 2. Buat Lingkungan Virtual (Virtual Environment)
Sangat disarankan untuk menggunakan lingkungan virtual untuk mengisolasi dependensi.

```bash
python -m venv venv
.\venv\Scripts\activate
```

### 3. Instal Dependensi
Asumsikan Anda memiliki file requirements.txt yang berisi semua pustaka yang diperlukan (seperti langchain, discord.py, groq, fpdf2, dll.).

```bash
pip install -r requirements.txt
```

### 4. Konfigurasi Kredensial
Bot ini memerlukan beberapa kunci API untuk dapat berfungsi.

Salin file .env.example menjadi file baru bernama .env.

```bash
# Untuk Windows
copy .env.example .env

# Untuk macOS / Linux
cp .env.example .env
```
Buka file .env yang baru dibuat dan isi dengan kredensial Anda. (Lihat file .env.example untuk detailnya).

### 5. Jalankan Bot
Setelah semua konfigurasi selesai, jalankan bot (asumsikan file utamanya adalah main.py):
```bash
python main.py
```
Jika tidak ada error, bot Anda akan online dan siap menerima perintah di server Discord Anda.

## Cara Menggunakan
Setelah bot ditambahkan ke server Discord Anda, Anda dapat berinteraksi dengannya menggunakan perintah slash (/).

- `/summarize [repo_url]`: Memulai analisis pada repositori GitHub yang diberikan.
- `... (Tambahkan perintah lain jika ada)`

Bot akan merespons secara interaktif untuk memberikan informasi yang Anda butuhkan.
