# -*- coding: utf-8 -*-
"""Direction-finding calibration table for the two-element Vivaldi array.

For every frequency and every angle in the H-plane (-90..+90 deg from
boresight) the script gives the simulated phase difference between the two
ports, the ideal phase difference k*d*sin(angle), both port gains and the
unambiguous region (the symmetric range around boresight where the
simulated phase difference is monotonic with a slope of at least
0.2 deg/deg, so one phase maps to one angle).

Inputs : ff_<f>GHz_p1.txt and ff_<f>GHz_p2.txt (CST farfield ASCII export of
         dualvivaldi_dizi.cst, directivity with phase, 1 degree steps)
Outputs: sonuclar/dizi/vivaldi_dizi_kalibrasyon_H_duzlemi.csv
         sonuclar/dizi/kalibrasyon_faz.png

Geometry as exported by CST: boresight is theta = 90, phi = 90 (+y), the
H-plane is the phi = 90 / 270 plane, angle = 90 - theta, co-polar component
is E_phi.

Run:  python scriptler/vivaldi_kalibrasyon.py C:\\CST
"""
import os
import sys
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FF_DIR = sys.argv[1] if len(sys.argv) > 1 else r"C:\CST"
FREQS = [2, 3, 4, 5, 6]          # GHz
D_MM = 24.0                      # element spacing (mm)
C0 = 299.792458                  # mm*GHz
OUT = os.path.join(ROOT, "sonuclar", "dizi")
os.makedirs(OUT, exist_ok=True)


def load(path):
    d = np.loadtxt(path, skiprows=2)
    return d[:, 0], d[:, 1], d[:, 5], d[:, 6]   # theta, phi, |Ephi| dBi, arg Ephi


def h_plane(th, ph, amp, arg):
    ang, a, p = [], [], []
    for deg in range(-90, 91):
        t = 90 - deg
        # theta > 180 does not exist; angles below -90 are not needed
        m = np.isclose(th, t) & np.isclose(ph, 90)
        ang.append(deg)
        a.append(amp[m][0])
        p.append(arg[m][0])
    return np.array(ang), np.array(a), np.array(p)


def wrap(x):
    return (x + 180) % 360 - 180


def unambiguous(ang, dphi, min_slope=0.2):
    """Symmetric region |angle| <= A around boresight where the (wrapped)
    phase difference changes monotonically by at least min_slope deg per deg,
    so one measured phase maps to exactly one angle."""
    best = 0
    for A in range(1, 91):
        r = np.abs(ang) <= A
        dd = np.diff(dphi[r])
        if np.all(dd > min_slope) or np.all(dd < -min_slope):
            best = A
        else:
            break
    return (np.abs(ang) <= best).astype(int)


rows = []
curves = {}
for f in FREQS:
    th, ph, a1, p1 = load(os.path.join(FF_DIR, f"ff_{f}GHz_p1.txt"))
    _, _, a2, p2 = load(os.path.join(FF_DIR, f"ff_{f}GHz_p2.txt"))
    ang, g1, q1 = h_plane(th, ph, a1, p1)
    _, g2, q2 = h_plane(th, ph, a2, p2)
    dphi = wrap(q2 - q1)
    ideal = wrap(360 * D_MM * f / C0 * np.sin(np.deg2rad(ang)))
    flag = unambiguous(ang, dphi)
    curves[f] = (ang, dphi, ideal, flag)
    for k in range(len(ang)):
        rows.append((f, ang[k], dphi[k], ideal[k], g1[k], g2[k], g1[k] - g2[k], flag[k]))
    lo, hi = ang[flag == 1].min(), ang[flag == 1].max()
    err = np.abs(wrap(dphi - ideal))[flag == 1]
    print(f"{f} GHz: unambiguous {lo:+d}..{hi:+d} deg, |sim - ideal| max {err.max():.1f} deg")

with open(os.path.join(OUT, "vivaldi_dizi_kalibrasyon_H_duzlemi.csv"), "w") as fh:
    fh.write("frekans_GHz,aci_deg,dphi_sim_deg,dphi_ideal_deg,genlik_p1_dBi,genlik_p2_dBi,genlik_farki_dB,belirsizliksiz_bolge\n")
    for r in rows:
        fh.write(f"{r[0]},{r[1]},{r[2]:.2f},{r[3]:.2f},{r[4]:.2f},{r[5]:.2f},{r[6]:.2f},{r[7]}\n")

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    cols = plt.cm.viridis(np.linspace(0, 0.9, len(FREQS)))
    for c, f in zip(cols, FREQS):
        ang, dphi, ideal, flag = curves[f]
        m = flag == 1
        ax.plot(ang[m], dphi[m], color=c, lw=1.6, label=f"{f} GHz simulated")
        ax.plot(ang, ideal, color=c, lw=0.8, ls="--")
    ax.set_xlim(-90, 90)
    ax.set_ylim(-180, 180)
    ax.set_xlabel("Angle of arrival in the H-plane (deg)")
    ax.set_ylabel("Phase difference port 2 - port 1 (deg)")
    ax.set_title(f"Two-element Vivaldi array, d = {D_MM:.0f} mm (CST; dashed = k·d·sin θ)")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8, ncol=2)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "kalibrasyon_faz.png"), dpi=150)
except ImportError:
    pass
