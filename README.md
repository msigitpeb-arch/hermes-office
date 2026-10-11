# Hermes Office

Virtual office untuk Hermes Agent di VPS SML: skill, persona (profile Hermes), dan script setup.

## Pasang pertama kali

```bash
cd ~ && git clone https://github.com/msigitpeb-arch/hermes-office.git
cd hermes-office
bash install_skills.sh <THREAD_ID_TOPIK_CONTENT_PLANNING>
bash setup_team.sh
```

Update: `cd ~/hermes-office && git pull`, lalu jalankan ulang kedua script di atas (aman diulang).

## content-planning
Content planner PeopleSync (tema: masalah SaaS dan keuntungan software sekali beli).
Alur: pembuat menyusun draft → pemeriksa (profile content-reviewer, model berbeda) mengoreksi dan memberi skor/approval → baris yang lolos disimpan ke `~/hermes-data/content-plan/peoplesync_content_plan.csv` dengan status "Menunggu review SML" → file CSV dikirim ke topik Telegram → SML membalas `approve CP-xxx`, `revisi CP-xxx <catatan>`, atau `tolak CP-xxx <alasan>`.

Pakai di Telegram: `/content-planning buat content plan 2 minggu untuk PeopleSync`

## Tim (virtual office)

`setup_team.sh` membuat tim berbasis profile Hermes + Kanban:

| Profile | Peran | Model |
|---|---|---|
| default (lead) | Ngobrol dengan SML, membuat kartu Kanban | sesuai config default |
| content-planner | Menyusun draft, lalu `kanban_request_review` | ag/gemini-3.8-flash-high |
| content-reviewer | Mengoreksi dan memberi approval, menyimpan ke CSV + kirim ke Telegram | ag/claude-sonnet-4-6 |

```bash
cd ~/hermes-office && git pull
bash setup_team.sh
```

Semua profile dilayani satu gateway (`gateway.multiplex_profiles: true`). Worker hanya jalan sebagai proses saat ada kartu Kanban, jadi tidak memakan RAM saat idle.

Mission Control 3D: [Ruang](https://github.com/yugienugraha/ruang) (read-only, membaca lewat `hermes` CLI).
