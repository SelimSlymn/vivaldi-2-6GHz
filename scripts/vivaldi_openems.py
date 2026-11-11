# -*- coding: utf-8 -*-
"""
Antipodal Vivaldi (elliptical profile) - openEMS simulation (version 1)
=======================================================================
The geometry was derived from the original DXF layout (units: mm).

Layers:
  z = 0   : bottom copper (arm flaring to the left + feed strip + SMA ground pads)
  0..h    : FR-4 substrate
  z = h   : top copper (arm flaring to the right + 20 mm feed pad)

Feed: instead of the SMA connector, a vertical 50 ohm lumped port through the
substrate at the pin position (0, 15) is used (bottom strip -> top ground).
Therefore the anti-pad hole in the top copper is not modelled. This is a
sufficient approximation for the antenna band and radiation pattern; the
effect of the SMA transition itself (a shift of a few hundred MHz) is not
included.

Usage:
  python scripts/vivaldi_openems.py
Plots are saved to results/v1: s11.png, zin.png, pattern_*.png
"""
import os
import numpy as np

# ------------------------------------------------------------------
# User parameters
# ------------------------------------------------------------------
h      = 1.6          # substrate thickness [mm]
eps_r  = 4.3          # FR-4 relative permittivity
tand   = 0.025        # FR-4 loss tangent
f_min  = 1e9          # [Hz]
f_max  = 10e9         # [Hz]
f_farfield = [2.4e9, 5.8e9]   # frequencies for the radiation patterns
pad    = 50.0         # air margin around the antenna [mm] (including PML)

# Mesh resolution [mm]. Smaller = accurate but slow. For a quick first run use
# res_air=3, res_board=1.5, res_feed=0.5 (~8x fewer cells).
res_air   = 1.5       # largest cell in air (lambda/20 @ 10 GHz)
res_board = 0.75      # on the board (lambda/19 in FR-4 @ 10 GHz)
res_feed  = 0.25      # in the feed region

SHOW_MODEL = True     # True: show the model in AppCSXCAD before simulating
RUN_SIM    = True     # False: only build/show the model, no simulation
ROOT       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR    = os.path.join(ROOT, 'results', 'v1')            # plots
sim_path   = os.path.join(ROOT, 'vivaldi_sim')              # raw openEMS data (git-ignored)

# ------------------------------------------------------------------
# Geometry constants extracted from the DXF [mm]
# ------------------------------------------------------------------
XC, YC = 44.4275, 27.77   # arm centres: top arm (+XC, YC), bottom arm (-XC, YC)
RA, RB = 47.21, 88.85     # arm outer edge: ellipse semi-axes (x, y)
RI     = 41.64            # arm inner edge: circle radius
RS     = 30.0             # radius of the concave cut-out at the board edge
NA, NB = 7.2175, 7.905    # neck curves of the top feed pad (ellipse semi-axes)
YPIN   = 15.0             # SMA pin position (x = 0)


# ------------------------------------------------------------------
# Geometry (pure numpy; does not need openEMS)
# ------------------------------------------------------------------
def arc(cx, cy, rx, ry, t0, t1, n=60):
    """Elliptical arc centred at (cx, cy) from t0 to t1 degrees. Returns an Nx2 array."""
    t = np.radians(np.linspace(t0, t1, n))
    return np.column_stack([cx + rx * np.cos(t), cy + ry * np.sin(t)])


def cos_taper(n=20):
    """Cosine-profile widening of the bottom strip: (1.4554, 19.865) -> (2.7825, 27.77)."""
    t = np.linspace(0.0, 1.0, n)
    x = 1.4554 + (2.7825 - 1.4554) * (1 - np.cos(np.pi * t)) / 2
    y = 19.865 + (27.77 - 19.865) * t
    return np.column_stack([x, y])


def board_outline():
    """FR-4 board outline (corner roundings neglected)."""
    pts = [np.array([[-14.4275, 10.0], [14.4275, 10.0]])]
    pts.append(arc(XC, YC, RS, RS, 180, 90, 60))        # (14.43, 27.77) -> (44.43, 57.77)
    pts.append(np.array([[49.425, 57.77], [49.425, 121.6],
                         [-49.425, 121.6], [-49.425, 57.77]]))
    pts.append(arc(-XC, YC, RS, RS, 90, 0, 60))         # (-44.43, 57.77) -> (-14.43, 27.77)
    return np.vstack(pts)


def top_copper():
    """Top copper: 20 mm feed pad + arm flaring to the right."""
    pts = [np.array([[-10.0, 10.0], [10.0, 10.0], [10.0, 19.865]])]
    pts.append(arc(10, YC, NA, NB, -90, -180, 40)[1:])  # right neck curve
    pts.append(arc(XC, YC, RI, RI, 180, 90, 120))       # inner edge of the arm
    pts.append(np.array([[XC, YC + RB]]))               # up along the right edge
    pts.append(arc(XC, YC, RA, RB, 90, 180, 160)[1:])   # outer edge of the arm
    pts.append(arc(-10, YC, NA, NB, 0, -90, 40)[1:])    # left neck curve
    return np.vstack(pts)


def bottom_copper():
    """Bottom copper: strip from the pin + cosine transition + arm flaring to the left."""
    tp = cos_taper()
    pts = [np.array([[-1.015, YPIN], [1.015, YPIN], [1.015, 19.365], [1.4554, 19.365]])]
    pts.append(tp)                                      # right transition
    pts.append(arc(-XC, YC, RA, RB, 0, 90, 160)[1:])    # outer edge of the arm (curving to the left)
    pts.append(arc(-XC, YC, RI, RI, 90, 0, 120))        # inner edge of the arm
    tl = tp[::-1].copy()
    tl[:, 0] *= -1                                      # left transition (top to bottom)
    pts.append(tl)
    pts.append(np.array([[-1.4554, 19.365], [-1.015, 19.365]]))
    return np.vstack(pts)


def pin_pad():
    """Pin pad on the bottom side (r = 1.025 mm)."""
    return arc(0, YPIN, 1.025, 1.025, 0, 360, 33)[:-1]


# Vias and SMA ground legs: (x, y, radius), z = 0 .. h
VIAS = [(sx * 4.465, y, 0.40) for sx in (1, -1) for y in (12.46, 17.54)] + \
       [(sx * 2.54,  y, 0.85) for sx in (1, -1) for y in (12.46, 17.54)]

# SMA ground pads on the bottom side: (xmin, ymin, xmax, ymax)
GND_PADS = [(1.415, 11.035, 5.465, 18.965), (-5.465, 11.035, -1.415, 18.965)]


def merge_lines(important, filler, min_d=0.12):
    """Keep the important lines; drop filler lines closer than min_d to them."""
    imp = np.unique(np.round(np.asarray(important, float), 4))
    keep = [v for v in np.unique(np.round(np.asarray(filler, float), 4))
            if np.min(np.abs(imp - v)) > min_d]
    return np.unique(np.concatenate([imp, keep]))


# ------------------------------------------------------------------
# openEMS model
# ------------------------------------------------------------------
def build_and_run():
    from CSXCAD import ContinuousStructure
    from openEMS import openEMS
    from openEMS.physical_constants import EPS0

    unit = 1e-3
    f0 = 0.5 * (f_min + f_max)
    fc = 0.5 * (f_max - f_min)

    FDTD = openEMS(NrTS=80000, EndCriteria=1e-4)   # -40 dB energy criterion
    FDTD.SetGaussExcite(f0, fc)
    FDTD.SetBoundaryCond(['PML_8'] * 6)

    CSX = ContinuousStructure()
    FDTD.SetCSX(CSX)
    mesh = CSX.GetGrid()
    mesh.SetDeltaUnit(unit)

    # --- Materials ---
    kappa = 2 * np.pi * f0 * EPS0 * eps_r * tand
    fr4 = CSX.AddMaterial('FR4', epsilon=eps_r, kappa=kappa)
    pec = CSX.AddMetal('PEC')

    # --- Substrate ---
    o = board_outline()
    fr4.AddLinPoly(points=[o[:, 0], o[:, 1]], norm_dir='z',
                   elevation=0, length=h, priority=1)

    # --- Copper (zero-thickness PEC sheets) ---
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

    # --- Port: vertical 50 ohm lumped port at the pin position ---
    rp = 0.635
    port = FDTD.AddLumpedPort(1, 50, [-rp, YPIN - rp, 0], [rp, YPIN + rp, h],
                              'z', 1.0, priority=5)

    # --- Mesh ---
    xb, yb0, yb1 = 49.425, 10.0, 121.6
    x_imp = [-xb - pad, xb + pad, -xb, xb, -XC, XC, -14.4275, 14.4275,
             -10, 10, -5.465, -1.415, 1.415, 5.465, -2.7825, 2.7825, -rp, rp]
    x_fill = np.concatenate([np.arange(-48.0, 48.01, res_board),   # board
                             np.arange(-6.0, 6.01, res_feed)])      # feed region
    y_imp = [yb0 - pad, yb1 + pad, yb0, yb1, 11.035, 18.965, 19.365, 19.865,
             27.77, 57.77, YC + RI, YC + RB, YPIN - rp, YPIN + rp]
    y_fill = np.concatenate([np.arange(yb0, yb1, res_board),
                             np.arange(9.0, 29.01, res_feed)])
    mesh.AddLine('x', merge_lines(x_imp, x_fill))
    mesh.AddLine('y', merge_lines(y_imp, y_fill))
    mesh.AddLine('z', [-pad, h + pad] + list(np.linspace(0, h, 5)))
    mesh.SmoothMeshLines('all', res_air, ratio=1.4)
    n = [mesh.GetQtyLines(d) for d in 'xyz']
    print('Mesh: {} x {} x {} = {:.2f} million cells'.format(*n, np.prod(n) / 1e6))

    # --- Farfield box ---
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
# Results
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
    plt.xlabel('Frequency (GHz)')
    plt.ylabel('S11 (dB)')
    plt.title('Antipodal Vivaldi - S11')
    plt.savefig(os.path.join(OUT_DIR, 's11.png'), dpi=150, bbox_inches='tight')

    # Input impedance
    plt.figure()
    plt.plot(f / 1e9, np.real(zin), 'k-', lw=2, label='Re{Zin}')
    plt.plot(f / 1e9, np.imag(zin), 'r--', lw=2, label='Im{Zin}')
    plt.grid(True)
    plt.legend()
    plt.xlabel('Frequency (GHz)')
    plt.ylabel('Zin (ohm)')
    plt.savefig(os.path.join(OUT_DIR, 'zin.png'), dpi=150, bbox_inches='tight')

    # -10 dB band
    ok = s11_db < -10
    if np.any(ok):
        edges = np.flatnonzero(np.diff(ok.astype(int)))
        print('Regions with S11 < -10 dB (GHz):')
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
        print('S11 does not go below -10 dB at any frequency.')

    # Radiation patterns
    #   E-plane (antenna plane, xy): theta = 90, phi = 0..360
    #   H-plane (yz):                phi = 90, theta = -180..180
    #   Main beam direction +y (theta = 90, phi = 90)
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
        d_y = np.interp(90.0, phi, d_e)   # directivity towards +y
        print('{:.1f} GHz: Dmax = {:.2f} dBi, D towards +y = {:.2f} dBi, '
              'radiation efficiency = {:.0f} %, gain ~ {:.2f} dBi'
              .format(fr / 1e9, d_max, d_y, 100 * eff,
                      d_y + 10 * np.log10(max(eff, 1e-6))))

        fig = plt.figure(figsize=(10, 5))
        ax1 = fig.add_subplot(121, projection='polar')
        ax1.plot(np.radians(phi), np.maximum(d_e, d_max - 30), 'k-', lw=2)
        ax1.set_rmin(d_max - 30)
        ax1.set_title('E-plane (xy) {:.1f} GHz [dBi]'.format(fr / 1e9))
        ax2 = fig.add_subplot(122, projection='polar')
        ax2.plot(np.radians(theta), np.maximum(d_h, d_max - 30), 'r-', lw=2)
        ax2.set_rmin(d_max - 30)
        ax2.set_title('H-plane (yz) {:.1f} GHz [dBi]'.format(fr / 1e9))
        fig.savefig(os.path.join(OUT_DIR, 'pattern_{:.1f}GHz.png'.format(fr / 1e9)), dpi=150, bbox_inches='tight')

    plt.show()


if __name__ == '__main__':
    build_and_run()
