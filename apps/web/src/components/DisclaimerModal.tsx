import { useEffect, useState } from 'react';

const STORAGE_KEY = 'spa.disclaimer.accepted.v1';

export function DisclaimerModal() {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (typeof localStorage !== 'undefined' && !localStorage.getItem(STORAGE_KEY)) {
      setOpen(true);
    }
  }, []);

  if (!open) return null;

  const accept = () => {
    localStorage.setItem(STORAGE_KEY, new Date().toISOString());
    setOpen(false);
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4">
      <div className="card max-w-lg w-full bg-slate-900 border-slate-700">
        <div className="text-2xl mb-3">⚠️ Disclaimer Penting</div>
        <div className="space-y-3 text-sm text-slate-300">
          <p>
            <strong>Sports Parlay Analyst v3.0</strong> adalah <em>tool analisa statistik</em> untuk
            tujuan edukasi. Aplikasi ini bukan layanan judi atau prediksi pemenang.
          </p>
          <ul className="list-disc list-inside space-y-1 text-slate-300">
            <li>Tidak ada jaminan akurasi pick. Olahraga punya variance tinggi.</li>
            <li>Bankroll yang ditampilkan adalah <strong>VIRTUAL</strong> (simulasi).</li>
            <li>Tidak ada link ke bandar judi, tidak ada deposit, tidak ada uang asli.</li>
            <li>Stake hard cap 3% per pick. Loss streak warning aktif.</li>
            <li>
              Kalau Anda merasa kesulitan mengontrol perilaku judi: hubungi{' '}
              <a className="underline text-emerald-400" href="https://www.kemkes.go.id/" target="_blank" rel="noreferrer">
                layanan kesehatan terdekat
              </a>{' '}
              atau hotline 119.
            </li>
          </ul>
          <p className="text-xs text-slate-500">
            Dengan klik "Saya mengerti", Anda menyetujui disclaimer di atas dan bertanggung jawab penuh
            atas penggunaan aplikasi ini. Tool ini tidak boleh dipakai oleh anak di bawah 18 tahun.
          </p>
        </div>
        <button onClick={accept} className="btn-primary w-full mt-4">
          Saya mengerti & lanjut
        </button>
      </div>
    </div>
  );
}
