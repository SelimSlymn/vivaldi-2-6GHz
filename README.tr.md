# 2–6 GHz Antipodal Vivaldi ve Faz Farkıyla Yön Bulma Dizisi

*English: [README.md](README.md)*

FR-4 üzerine CNC ile kazınabilecek antipodal Vivaldi anten. Amaç, iki (ileride üç) elemanlı dizide alınan sinyalin faz farkından geliş yönünü bulmak. Elemanlar doğrudan SDR'ın (HamGeek E310, AD9361, 2 RX) iki alıcı kanalına bağlanacak.

## Tasarım

| Parametre | Değer |
|---|---|
| Alttaş | FR-4, 1.6 mm, εr 4.3, tanδ 0.02 |
| Besleme | SMA, pin konumu (0, 15) mm |
| Tasarım A (seçilen) | ağız yarı genişliği xc = 47 mm, kol boyu rb = 110 mm |
| Orijinal | xc = 44.43 mm, rb = 88.85 mm |
| Dizi eleman aralığı | 24 mm |
| Üretim | Linermak LM-R50 C CNC router; tasarım A'nın DXF katmanları `uretim/Vivaldi_v2_A.zip` içinde |

## Sonuçlar (CST, tek eleman, tasarım A)

`cst/vivaldi_A.cst` CST'de (time domain) çözüldü, openEMS ile çapraz kontrol edildi.

| | CST | openEMS |
|---|---|---|
| 2–6 GHz en kötü S11 | −9.2 dB @ 2.83 GHz | −8.8 dB @ 2.70 GHz |
| 2–6 GHz maks. VSWR | 2.06 | 2.14 |
| 2–6 GHz'in −10 dB altındaki kısmı | %87 | %89 |

İki çözücü de tek zayıf bölgeyi 2.6–3.0 GHz'te gösteriyor; yani sorun çözücüde değil tasarımda. Bu bölge dışında −10 dB bandı 1.78–7.85 GHz.

| Frekans | Kazanç (realized, tepe) | Ön/arka | HPBW E / H |
|---|---|---|---|
| 2 GHz | 4.5 dBi | 10.7 dB | 66° / 134° |
| 3 GHz | 6.5 dBi | 9.2 dB | 60° / 104° |
| 4 GHz | 8.7 dBi | 9.8 dB | 40° / 77° |
| 5 GHz | 8.3 dBi | 11.8 dB | 42° / 59° |
| 6 GHz | 8.6 dBi | 12.6 dB | 38° / 50° |

Grafikler `grafikler/`, tablo `sonuclar/cst/performans_tablosu_cst.csv`.

## Varyant çalışması (openEMS)

| Varyant | 2–6 GHz en kötü S11 |
|---|---|
| orijinal | −8.62 dB @ 2.00 GHz |
| A_onerilen | −8.79 dB @ 2.70 GHz |
| B_uc_yuvarlak | −8.97 dB @ 2.73 GHz |
| C_arka_kenar | −8.36 dB @ 2.68 GHz |
| D_fr4_uzanti | −8.52 dB @ 2.69 GHz |

Hiçbir varyant 2–6 GHz'in tamamında −10 dB'yi sağlamıyor; A tasarımında tek aşım 2.50–2.92 GHz, VSWR ≤ 2.14. Grafikler: `sonuclar/v2-varyantlar/`. İlk tasarımın S11, giriş empedansı ve 2.4 / 5.8 GHz desenleri: `sonuclar/v1/`.

## Dizi

`cst/dualvivaldi_dizi.cst` iki elemanlı dizi. `sonuclar/dizi/vivaldi_dizi_kalibrasyon_H_duzlemi.csv`, 2–6 GHz'te H düzleminde açıya göre simüle edilen faz farkını, ideal faz farkını, iki portun genliğini ve belirsizliksiz açı bölgesini veriyor; yön bulma algoritmasının kalibrasyon tablosu. `scriptler/vivaldi_kalibrasyon.py` bu tabloyu CST uzak alan dışa aktarımlarından (`ff_<f>GHz_p1/p2.txt`) üretir. Düşük frekansta elemanlar arası kuplaj yüzünden simüle faz farkı ideal k·d·sin θ değerinin yaklaşık iki katına çıkıyor; yön bulmada tablo kullanılmalı.

## Dosyalar

| Klasör | İçerik |
|---|---|
| `cst/` | `vivaldi_A.cst` (tek eleman, tasarım A), `dualvivaldi_dizi.cst` (iki elemanlı dizi) |
| `cst-makrolar/` | tasarım A'yı CST'de kuran makrolar (sabit ve parametrik) |
| `scriptler/` | `vivaldi_openems.py` (v1), `vivaldi_v2.py` (varyantlar), `cst_vivaldi_A.py` (CST modelini kuran script), `vivaldi_kalibrasyon.py` (kalibrasyon tablosu) |
| `openems/` | openEMS geometri dosyası |
| `uretim/` | CNC için DXF katmanları (üst, alt, delikler, kart sınırı) |
| `sonuclar/` | CST sonuçları (`cst/`), openEMS varyantları, kalibrasyon (`dizi/`) |
