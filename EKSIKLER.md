# Eksikler – Vivaldi

## Tamamlananlar

- [x] Kalibrasyon scripti yeniden yazıldı (`scriptler/vivaldi_kalibrasyon.py`). CST uzak alan dosyalarından eski tablonun faz ve genlik sütunlarını birebir üretiyor; belirsizliksiz bölge tanımı (simetrik, eğim ≥ 0.2°/°) eskisiyle en fazla 1° farklı.
- [x] Eleman aralığı bulundu: 24 mm (ideal faz sütunundan).
- [x] `uretim/Vivaldi_v2_A.zip` içindeki DXF'ler tasarım A'ya ait (bakır kenar ±47 mm, flare boyu 110 mm). Önizleme `uretim/preview.png`.
- [x] README'de S11 iddiası düzeltildi: "VSWR ≤ 2.14, bandın %89'unda S11 < −10 dB".
- [x] İngilizce `README.md`, Türkçe `README.tr.md`, `LICENSE` (MIT), repoya özel `.gitignore`.

## Senin yapman gerekenler

- [x] Tek eleman CST 2025'te makroyla yeniden kurulup çözüldü (`cst/vivaldi_A.cst`); S11, desenler ve kazanç tablosu README'de, openEMS ile karşılaştırmalı.
- [ ] **Dizinin S-parametreleri:** `dualvivaldi_dizi.cst` açıkken `cst-makrolar/dizi_s2p_aktar.bas`'ı çalıştır (`sonuclar/dizi/dualvivaldi_dizi.s2p`). Eleman arası kuplaj (S21) README'ye eklenecek.
- [ ] `cst/vivaldi.cst` (Learning Edition dosyası) ve `cst/dualvivaldi.cst` (eski parametre taraması) silinecek; `sonuclar/cst/` içindeki boş .txt'ler (`s11`, `vswr`, `tot_eff`, `rad_eff`, `export_log`) silinecek.

## Portfolyo için

- [ ] CNC'de kazınmış kart fotoğrafı, VNA ile S11 ölçümü.
- [ ] Bilinen açılarda yön bulma testi ve hata (derece).
- [ ] 3 elemanlı yarışma versiyonu.
