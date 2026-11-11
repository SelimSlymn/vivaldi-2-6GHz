# -*- coding: utf-8 -*-
"""
Antipodal Vivaldi (elips profilli) - openEMS simulasyonu
=========================================================
Geometri Vivaldi.zip icindeki DXF dosyalarindan turetildi (birim: mm).

Katmanlar:
  z = 0   : alt bakir (sola acilan kol + besleme seridi + SMA toprak pad'leri)
  0..h    : FR-4 alttas
  z = h   : ust bakir (saga acilan kol + 20 mm besleme pad'i)

Besleme: SMA konnektoru yerine, pin konumunda (0, 15) alttasin icinden
gecen dikey 50 ohm lumped port kullaniliyor (alt serit -> ust toprak).
Bu yuzden ust bakirdaki anti-pad deligi modelde yok. Anten bandi ve
isima diyagrami icin yeterli bir yaklasim; SMA gecisinin kendi etkisi
(birkac yuz MHz'lik kayma) modelde yer almaz.

Kullanim:
  python vivaldi_openems.py
Grafikler scriptin bulundugu klasore kaydedilir: s11.png, zin.png, pattern_*.png
"""
import os
import numpy as np

# ------------------------------------------------------------------
# Kullanici parametreleri
# ------------------------------------------------------------------
h      = 1.6          # alttas kalinligi [mm]
eps_r  = 4.3          # FR-4 dielektrik sabiti
tand   = 0.025        # FR-4 kayip tanjanti
f_min  = 1e9          # [Hz]
f_max  = 10e9         # [Hz]
f_farfield = [2.4e9, 5.8e9]   # isima diyagrami hesaplanacak frekanslar
pad    = 50.0         # anten etrafindaki hava boslugu [mm] (PML dahil)

# Mesh cozunurlugu [mm]. Kucuk = dogru ama yavas. Hizli bir ilk deneme icin
# res_air=3, res_board=1.5, res_feed=0.5 yapabilirsin (~8 kat daha az hucre).
res_air   = 1.5       # havada en buyuk hucre (lambda/20 @ 10 GHz)
res_board = 0.75      # kart uzerinde (FR-4 icinde lambda/19 @ 10 GHz)
res_feed  = 0.25      # besleme bolgesinde

SHOW_MODEL = True     # True: simulasyondan once modeli AppCSXCAD'de goster
RUN_SIM    = True     # False: sadece modeli kur/goster, simulasyon yapma
OUT_DIR    = os.path.dirname(os.path.abspath(__file__))   # grafikler scriptin yanina kaydedilir
sim_path   = os.path.join(OUT_DIR, 'vivaldi_sim')         # openEMS ham verileri

# ------------------------------------------------------------------
# DXF'ten cikarilan geometri sabitleri [mm]
# ------------------------------------------------------------------
XC, YC = 44.4275, 27.77   # kol merkezleri: ust kol (+XC, YC), alt kol (-XC, YC)
RA, RB = 47.21, 88.85     # kol dis kenari: elips yari eksenleri (x, y)
RI     = 41.64            # kol ic kenari: cember yaricapi
RS     = 30.0             # kart kenarindaki icbukey oyuk yaricapi
NA, NB = 7.2175, 7.905    # ust besleme pad'inin boyun kavisleri (elips yari eksenleri)
YPIN   = 15.0             # SMA pin konumu (x = 0)


# ------------------------------------------------------------------
# Geometri (saf numpy; openEMS gerektirmez)
# ------------------------------------------------------------------
def arc(cx, cy, rx, ry, t0, t1, n=60):
    """(cx, cy) merkezli elips yayi; t0 -> t1 derece. Nx2 dizi dondurur."""
    t = np.radians(np.linspace(t0, t1, n))
    return np.column_stack([cx + rx * np.cos(t), cy + ry * np.sin(t)])


def cos_taper(n=20):
    """Alt seritteki kosinus profilli genisleme: (1.4554, 19.865) -> (2.7825, 27.77)."""
    t = np.linspace(0.0, 1.0, n)
    x = 1.4554 + (2.7825 - 1.4554) * (1 - np.cos(np.pi * t)) / 2
    y = 19.865 + (27.77 - 19.865) * t
    return np.column_stack([x, y])


def board_outline():
    """FR-4 kart dis hatti (kose yuvarlatmalari ihmal edildi)."""
    pts = [np.array([[-14.4275, 10.0], [14.4275, 10.0]])]
    pts.append(arc(XC, YC, RS, RS, 180, 90, 60))        # (14.43, 27.77) -> (44.43, 57.77)
    pts.append(np.array([[49.425, 57.77], [49.425, 121.6],
                         [-49.425, 121.6], [-49.425, 57.77]]))
    pts.append(arc(-XC, YC, RS, RS, 90, 0, 60))         # (-44.43, 57.77) -> (-14.43, 27.77)
    return np.vstack(pts)


def top_copper():
    """Ust bakir: 20 mm besleme pad'i + saga acilan kol."""
    pts = [np.array([[-10.0, 10.0], [10.0, 10.0], [10.0, 19.865]])]
    pts.append(arc(10, YC, NA, NB, -90, -180, 40)[1:])  # sag boyun kavsi
    pts.append(arc(XC, YC, RI, RI, 180, 90, 120))       # kolun ic kenari
    pts.append(np.array([[XC, YC + RB]]))               # sag kenar boyunca yukari
    pts.append(arc(XC, YC, RA, RB, 90, 180, 160)[1:])   # kolun dis kenari
    pts.append(arc(-10, YC, NA, NB, 0, -90, 40)[1:])    # sol boyun kavsi
    return np.vstack(pts)


def bottom_copper():
    """Alt bakir: pinden cikan serit + kosinus gecis + sola acilan kol."""
    tp = cos_taper()
    pts = [np.array([[-1.015, YPIN], [1.015, YPIN], [1.015, 19.365], [1.4554, 19.365]])]
    pts.append(tp)                                      # sag gecis
    pts.append(arc(-XC, YC, RA, RB, 0, 90, 160)[1:])    # kolun dis kenari (sola kivrilir)
    pts.append(arc(-XC, YC, RI, RI, 90, 0, 120))        # kolun ic kenari
    tl = tp[::-1].copy()
    tl[:, 0] *= -1                                      # sol gecis (yukaridan asagi)
    pts.append(tl)
    pts.append(np.array([[-1.4554, 19.365], [-1.015, 19.365]]))
    return np.vstack(pts)


def pin_pad():
    """Alt yuzdeki pin pad'i (r = 1.025 mm)."""
    return arc(0, YPIN, 1.025, 1.025, 0, 360, 33)[:-1]


# Via ve SMA toprak bacaklari: (x, y, yaricap), z = 0 .. h
VIAS = [(sx * 4.465, y, 0.40) for sx in (1, -1) for y in (12.46, 17.54)] + \
       [(sx * 2.54,  y, 0.85) for sx in (1, -1) for y in (12.46, 17.54)]

# Alt yuzdeki SMA toprak pad'leri: (xmin, ymin, xmax, ymax)
GND_PADS = [(1.415, 11.035, 5.465, 18.965), (-5.465, 11.035, -1.415, 18.965)]


def merge_lines(important, filler, min_d=0.12):
    """Onemli cizgileri koru; onlara min_d'den yakin dolgu cizgilerini at."""
    imp = np.unique(np.round(np.asarray(important, float), 4))
    keep = [v for v in np.unique(np.round(np.asarray(filler, float), 4))
            if np.min(np.abs(imp - v)) > min_d]
    return np.unique(np.concatenate([imp, keep]))


# ------------------------------------------------------------------
# openEMS modeli
# ------------------------------------------------------------------
def build_and_run():
    from CSXCAD import ContinuousStructure
    from openEMS import openEMS
    from openEMS.physical_constants import EPS0

    unit = 1e-3
    f0 = 0.5 * (f_min + f_max)
    fc = 0.5 * (f_max - f_min)

    FDTD = openEMS(NrTS=80000, EndCriteria=1e-4)   # -40 dB enerji kriteri
    FDTD.SetGaussExcite(f0, fc)
    FDTD.SetBoundaryCond(['PML_8'] * 6)

    CSX = ContinuousStructure()
    FDTD.SetCSX(CSX)
    mesh = CSX.GetGrid()
    mesh.SetDeltaUnit(unit)

    # --- Malzemeler ---
    kappa = 2 * np.pi * f0 * EPS0 * eps_r * tand
    fr4 = CSX.AddMaterial('FR4', epsilon=eps_r, kappa=kappa)
    pec = CSX.AddMetal('PEC')

    # --- Alttas ---
    o = board_outline()
    fr4.AddLinPoly(points=[o[:, 0], o[:, 1]], norm_dir='z',
                   elevation=0, length=h, priority=1)

    # --- Bakir (sifir kalinlikli PEC levhalar) ---
    t = top_copper()
    pec.AddPolygon(points=[t[:, 0], t[:, 1]], norm_dir='z', elevation=h, priority=10)
    b = bottom_copper()
    pec.AddPolygon(points=[b[:, 0], b[:, 1]], norm_dir='z', elevation=0, priority=10)
    d = pin_pad()
    pec.AddPolygon(points=[d[:, 0], d[:, 1]], norm_dir='z', elevation=0, priority=10)
    for (x0, y0, x1, y1) in GND_PADS:
        pec.AddBox([x0, y0, 0], [x1, y1, 0], priority=10)
    for (x, y, r) in VIAS:
        pec.AddCylinder([x, y, 0], [x, y, h], r, priority=10)

    # --- Port: pin konumunda dikey 50 ohm lumped port ---
    rp = 0.635
    port = FDTD.AddLumpedPort(1, 50, [-rp, YPIN - rp, 0], [rp, YPIN + rp, h],
                              'z', 1.0, priority=5)

    # --- Mesh ---
    xb, yb0, yb1 = 49.425, 10.0, 121.6
    x_imp = [-xb - pad, xb + pad, -xb, xb, -XC, XC, -14.4275, 14.4275,
             -10, 10, -5.465, -1.415, 1.415, 5.465, -2.7825, 2.7825, -rp, rp]
    x_fill = np.concatenate([np.arange(-48.0, 48.01, res_board),   # kart
                             np.arange(-6.0, 6.01, res_feed)])      # besleme bolgesi
    y_imp = [yb0 - pad, yb1 + pad, yb0, yb1, 11.035, 18.965, 19.365, 19.865,
             27.77, 57.77, YC + RI, YC + RB, YPIN - rp, YPIN + rp]
    y_fill = np.concatenate([np.arange(yb0, yb1, res_board),
                             np.arange(9.0, 29.01, res_feed)])
    mesh.AddLine('x', merge_lines(x_imp, x_fill))
    mesh.AddLine('y', merge_lines(y_imp, y_fill))
    mesh.AddLine('z', [-pad, h + pad] + list(np.linspace(0, h, 5)))
    mesh.SmoothMeshLines('all', res_air, ratio=1.4)
    n = [mesh.GetQtyLines(d) for d in 'xyz']
    print('Mesh: {} x {} x {} = {:.2f} milyon hucre'.format(*n, np.prod(n) / 1e6))

    # --- Uzak alan kutusu ---
    nf2ff = FDTD.CreateNF2FFBox()

    os.makedirs(sim_path, exist_ok=True)
    if SHOW_MODEL:
        from CSXCAD import AppCSXCAD_BIN
        xml = os.path.join(sim_path, 'vivaldi.xml')
        CSX.Write2XML(xml)
        os.system(AppCSXCAD_BIN + ' "{}"'.format(xml))

    if not RUN_SIM:
        return

    FDTD.Run(sim_path, cleanup=True)
    postprocess(port, nf2ff)


# ------------------------------------------------------------------
# Sonuclar
# ------------------------------------------------------------------
def postprocess(port, nf2ff):
    import matplotlib.pyplot as plt

    f = np.linspace(f_min, f_max, 901)
    port.CalcPort(sim_path, f)
    s11 = port.uf_ref / port.uf_inc
    s11_db = 20 * np.log10(np.abs(s11))
    zin = port.uf_tot / port.if_tot

    # S11
    plt.figure()
    plt.plot(f / 1e9, s11_db, 'k-', lw=2)
    plt.axhline(-10, color='r', ls='--', lw=1)
    plt.grid(True)
    plt.xlabel('Frekans (GHz)')
    plt.ylabel('S11 (dB)')
    plt.title('Antipodal Vivaldi - S11')
    plt.savefig(os.path.join(OUT_DIR, 's11.png'), dpi=150, bbox_inches='tight')

    # Giris empedansi
    plt.figure()
    plt.plot(f / 1e9, np.real(zin), 'k-', lw=2, label='Re{Zin}')
    plt.plot(f / 1e9, np.imag(zin), 'r--', lw=2, label='Im{Zin}')
    plt.grid(True)
    plt.legend()
    plt.xlabel('Frekans (GHz)')
    plt.ylabel('Zin (ohm)')
    plt.savefig(os.path.join(OUT_DIR, 'zin.png'), dpi=150, bbox_inches='tight')

    # -10 dB bandi
    ok = s11_db < -10
    if np.any(ok):
        edges = np.flatnonzero(np.diff(ok.astype(int)))
        print('S11 < -10 dB olan bolgeler (GHz):')
        start = f[0] if ok[0] else None
        for i in edges:
            if ok[i + 1]:
                start = f[i + 1]
            else:
                print('  {:.2f} - {:.2f}'.format(start / 1e9, f[i] / 1e9))
                start = None
        if start is not None:
            print('  {:.2f} - {:.2f}'.format(start / 1e9, f[-1] / 1e9))
    else:
        print('S11 hicbir frekansta -10 dB altina inmiyor.')

    # Isima diyagramlari
    #   E-duzlemi (anten duzlemi, xy): theta = 90, phi = 0..360
    #   H-duzlemi (yz):                phi = 90, theta = -180..180
    #   Ana isima yonu +y (theta = 90, phi = 90)
    center = [0, 60e-3, 0]
    phi = np.arange(0, 361, 2.0)
    theta = np.arange(-180, 181, 2.0)
    res_e = nf2ff.CalcNF2FF(sim_path, f_farfield, [90.0], phi, center=center,
                            outfile='nf2ff_E.h5')
    res_h = nf2ff.CalcNF2FF(sim_path, f_farfield, theta, [90.0], center=center,
                            outfile='nf2ff_H.h5')

    for i, fr in enumerate(f_farfield):
        p_acc = np.interp(fr, f, port.P_acc)
        eff = res_e.Prad[i] / p_acc
        d_max = 10 * np.log10(res_e.Dmax[i])
        e_e = res_e.E_norm[i][0, :]
        e_h = res_h.E_norm[i][:, 0]
        d_e = 20 * np.log10(e_e / np.max(e_e)) + d_max
        d_h = 20 * np.log10(e_h / np.max(e_h)) + 10 * np.log10(res_h.Dmax[i])
        d_y = np.interp(90.0, phi, d_e)   # +y yonundeki yonluluk
        print('{:.1f} GHz: Dmax = {:.2f} dBi, +y yonunde D = {:.2f} dBi, '
              'isima verimi = {:.0f} %, kazanc ~ {:.2f} dBi'
              .format(fr / 1e9, d_max, d_y, 100 * eff,
                      d_y + 10 * np.log10(max(eff, 1e-6))))

        fig = plt.figure(figsize=(10, 5))
        ax1 = fig.add_subplot(121, projection='polar')
        ax1.plot(np.radians(phi), np.maximum(d_e, d_max - 30), 'k-', lw=2)
        ax1.set_rmin(d_max - 30)
        ax1.set_title('E-duzlemi (xy) {:.1f} GHz [dBi]'.format(fr / 1e9))
        ax2 = fig.add_subplot(122, projection='polar')
        ax2.plot(np.radians(theta), np.maximum(d_h, d_max - 30), 'r-', lw=2)
        ax2.set_rmin(d_max - 30)
        ax2.set_title('H-duzlemi (yz) {:.1f} GHz [dBi]'.format(fr / 1e9))
        fig.savefig(os.path.join(OUT_DIR, 'pattern_{:.1f}GHz.png'.format(fr / 1e9)), dpi=150, bbox_inches='tight')

    plt.show()


if __name__ == '__main__':
    build_and_run()
