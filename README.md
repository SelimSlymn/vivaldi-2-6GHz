# 2–6 GHz Antipodal Vivaldi and Two-Element Direction-Finding Array

An antipodal Vivaldi antenna on FR-4 that can be milled on a desktop CNC router. Two elements are connected directly to the two receive channels of an AD9361-based SDR (HamGeek E310), and the angle of arrival is estimated from the phase difference between them.

*Türkçe açıklama: [README.tr.md](README.tr.md)*

![Board layout](uretim/preview.png)

## Results

### Single element

Simulated in CST (time domain, `cst/vivaldi_A.cst`) and cross-checked with openEMS.

| | CST | openEMS |
|---|---|---|
| Worst S11 in 2–6 GHz | −9.2 dB @ 2.83 GHz | −8.8 dB @ 2.70 GHz |
| Max VSWR in 2–6 GHz | 2.06 | 2.14 |
| Share of 2–6 GHz below −10 dB | 87 % | 89 % |

Both solvers place the only weak region at 2.6–3.0 GHz, so it is a property of the design rather than of the solver; outside it the −10 dB band extends from 1.78 to 7.85 GHz.

![S11, CST vs openEMS](grafikler/s11_cst_openems.png)

| Frequency | Realized gain (peak) | Front-to-back | HPBW E / H |
|---|---|---|---|
| 2 GHz | 4.5 dBi | 10.7 dB | 66° / 134° |
| 3 GHz | 6.5 dBi | 9.2 dB | 60° / 104° |
| 4 GHz | 8.7 dBi | 9.8 dB | 40° / 77° |
| 5 GHz | 8.3 dBi | 11.8 dB | 42° / 59° |
| 6 GHz | 8.6 dBi | 12.6 dB | 38° / 50° |

Full table: [`sonuclar/cst/performans_tablosu_cst.csv`](sonuclar/cst/performans_tablosu_cst.csv). The beam points along the flare (+y); the E-plane is the board plane.

![Radiation patterns](grafikler/patterns_E_H.png)

The openEMS study of four shape variants that led to design A is in [`sonuclar/v2-varyantlar/`](sonuclar/v2-varyantlar/).

### Two-element array (CST)

The array (`cst/dualvivaldi_dizi.cst`, element spacing 24 mm) was solved in CST with both ports excited in turn. The calibration table [`sonuclar/dizi/vivaldi_dizi_kalibrasyon_H_duzlemi.csv`](sonuclar/dizi/vivaldi_dizi_kalibrasyon_H_duzlemi.csv) gives, for 2–6 GHz in 1° steps, the simulated phase difference, the ideal k·d·sin θ, both port gains and the unambiguous region.

| Frequency | Unambiguous region |
|---|---|
| 2 GHz | ±81° |
| 3 GHz | ±68° |
| 4 GHz | ±65° |
| 5 GHz | ±50° |
| 6 GHz | ±71° |

![Phase difference vs angle](sonuclar/dizi/kalibrasyon_faz.png)

Mutual coupling between the closely spaced elements (0.16 λ at 2 GHz) makes the simulated phase difference up to about twice the free-space value at low frequencies. The simple k·d·sin θ formula would therefore give large angle errors, so the direction finder should use the simulated (or measured) calibration table.

## Design

| Parameter | Value |
|---|---|
| Substrate | FR-4, 1.6 mm, εr 4.3, tanδ 0.02 |
| Board | 104.0 × 132.8 mm |
| Feed | SMA, pin at (0, 15) mm |
| Design A (selected) | mouth half-width xc = 47 mm, flare length rb = 110 mm |
| Original | xc = 44.43 mm, rb = 88.85 mm |
| Array spacing | 24 mm |
| Fabrication | Linermak LM-R50 C CNC router; DXF layers of design A in `uretim/Vivaldi_v2_A.zip` |

## Reproducing the results

```
pip install numpy matplotlib
python scriptler/vivaldi_v2.py                       # openEMS variants (needs openEMS)
# CST: open cst/vivaldi_A.cst, Start Simulation, then run cst-makrolar/vivaldi_sonuc_aktar.bas (Touchstone export)
python scriptler/vivaldi_kalibrasyon.py <ff folder>  # calibration table from CST farfields
```

The array farfields (`ff_<f>GHz_p1/p2.txt`, 10 × 10 MB) are not included; export them from `cst/dualvivaldi_dizi.cst` (Farfields → ASCII export, 1° steps).

## Limitations

- The matching goal of S11 < −10 dB across 2–6 GHz is missed at 2.6–3.0 GHz (worst −9.2 dB in CST, VSWR 2.06).
- Not yet fabricated or measured.

## Files

| Path | Contents |
|---|---|
| `cst/` | `vivaldi_A.cst` (single element, design A), `dualvivaldi_dizi.cst` (two-element array) |
| `cst-makrolar/` | macros that build design A in CST (fixed and parametric) and export results |
| `scriptler/` | openEMS models, CST build script, calibration script |
| `openems/` | openEMS geometry |
| `uretim/` | CNC DXF layers (top, bottom, drills, outline) and preview |
| `sonuclar/` | CST results (`cst/`), openEMS variants, calibration data (`dizi/`) |

## Author

Selim Süleyman Hüthüt, Electrical and Electronics Engineering, Çukurova University

## License

MIT, see [LICENSE](LICENSE).
