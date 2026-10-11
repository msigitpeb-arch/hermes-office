/**
 * Penerima data content plan PeopleSync untuk Google Sheets.
 * Dipasang di spreadsheet tujuan: Extensions > Apps Script, tempel file ini,
 * ganti TOKEN, lalu Deploy > New deployment > Web app
 * (Execute as: Me, Who has access: Anyone). Langkah lengkap ada di README repo.
 *
 * save_plan.py mengirim {token, fields, rows}. Baris dicocokkan lewat kolom id:
 * id yang sudah ada ditimpa, id baru ditambahkan di bawah. Baris tidak pernah dihapus.
 */
const TOKEN = 'GANTI_DENGAN_TOKEN_RAHASIA';
const SHEET_NAME = 'Content Plan';

function doPost(e) {
  let body;
  try {
    body = JSON.parse(e.postData.contents);
  } catch (err) {
    return balas({ ok: false, error: 'JSON tidak valid' });
  }
  // Placeholder sengaja tidak ditulis ulang di sini: "ganti semua" akan ikut mengubahnya
  // dan membuat semua kiriman ditolak.
  if (TOKEN.indexOf('GANTI_') === 0 || body.token !== TOKEN) {
    return balas({ ok: false, error: 'token salah atau belum diganti' });
  }
  const fields = body.fields || [];
  const rows = body.rows || [];
  if (!fields.length || fields[0] !== 'id') {
    return balas({ ok: false, error: 'fields harus diawali kolom id' });
  }

  const lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const sh = ss.getSheetByName(SHEET_NAME) || ss.insertSheet(SHEET_NAME);
    sh.getRange(1, 1, 1, fields.length).setValues([fields]).setFontWeight('bold');
    sh.setFrozenRows(1);

    const last = sh.getLastRow();
    const ids = last > 1 ? sh.getRange(2, 1, last - 1, 1).getValues().map(function (r) { return String(r[0]); }) : [];
    let baru = 0, diperbarui = 0;
    rows.forEach(function (r) {
      const id = String(r.id || '');
      if (!id) return;
      let i = ids.indexOf(id);
      if (i === -1) { ids.push(id); i = ids.length - 1; baru++; } else { diperbarui++; }
      const nilai = fields.map(function (f) { return r[f] == null ? '' : String(r[f]); });
      // Format teks: tanggal tidak diubah Sheets dan isi berawalan "=" tidak dijalankan sebagai rumus
      sh.getRange(i + 2, 1, 1, fields.length).setNumberFormat('@').setValues([nilai]);
    });
    return balas({ ok: true, baru: baru, diperbarui: diperbarui, total: ids.length });
  } finally {
    lock.releaseLock();
  }
}

function balas(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}
