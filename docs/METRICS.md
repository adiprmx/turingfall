# Metrik
Tiga angka, dipisah tegas karena sering dicampur.

- per-challenge: benar pada percobaan pertama. Untuk membandingkan model persepsi.
- per-session@N: berhasil dalam <=N percobaan. Ini yang dirasakan pengguna. Headline.
- ES v1: `100 * per_session / (1 + usd_per_1k + p95_s/2)`. Bobot 1 dolar = 2 detik = 1 poin.
  Dibekukan 2026-11-17. Mengubahnya butuh ADR baru + re-bench seluruh scoreboard.

Wajib dilaporkan: n, CI95 Wilson, p50, p95, $/1k, tanggal corpus.
`per-challenge` tanpa `n` dan CI95 ditolak di review.
Corpus di bawah 200 item: label `provisional` wajib ada di tabel.
