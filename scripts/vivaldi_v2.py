# -*- coding: utf-8 -*-
"""
Antipodal Vivaldi v2 - 2-6 GHz, FR-4, openEMS
=============================================
Improvement options on top of the original design:

  1) Radial corrugations on the outer edges of the arms
     -> lowers the lower cut-off frequency, improves match and gain at 2 GHz
  2) Longer feed transition (FEED_EXT)
     -> arms and board move up by FEED_EXT; the taper of the top ground and the
        2.9 -> 5.6 mm widening of the bottom strip are spread over a longer distance

Feed: vertical 50 ohm port through the substrate at the SMA pin position (0, 15).

  3) Arm dimensions (xc: mouth width, rb: flare length) -> largest effect at 2 GHz
  4) Arm tip rounding (tip_r), back-edge shape (back_ry), FR-4 in front of the mouth (sub_ext)

Usage:  python scripts/vivaldi_v2.py
Simulates all designs in the VARIANTS list below, one after another.
Outputs in results/v2-variants: v2_s11.png (all overlaid), v2_<variant>_pattern.png,
v2_<variant>_s11.csv, v2_summary.txt
"""
import os
import sys
import numpy as np

# ------------------------------------------------------------------
# Design parameters
# ------------------------------------------------------------------
P = dict(
    h=1.6,            # FR-4 thickness [mm]
    eps_r=4.3,        # FR-4 relative permittivity
    tand=0.02,        # FR-4 loss tangent (typically 0.016-0.02 at GHz frequencies)
    # --- 1) Corrugations ---
    corr_n=0,         # corrugations per arm (0 = none)
    corr_w=2.0,       # corrugation width [mm]
    corr_frac=0.5,    # corrugation depth = this fraction of the arm width
    corr_d=0.0,       # if > 0: fixed corrugation depth [mm] (instead of corr_frac)
    corr_a0=95.0,     # angular range of the corrugations [deg]; 180 = neck, 90 = arm tip
    corr_a1=150.0,
    # --- 2) Feed transition ---
    feed_ext=0.0,     # extend the feed transition by this much [mm]
    # --- 3) Arm dimensions ---
    xc=47.0,          # mouth half-width: arm end points at x = +-xc [mm]  (original 44.4275)
    rb=110.0,         # flare length: mouth end at y = yc + rb [mm]            (original 88.85)
    back_ry=0.0,      # vertical semi-axis of the arm back-edge ellipse [mm]; 0 = circle (original)
    tip_r=0.0,        # rounding radius of the sharp arm-tip corner [mm]; 0 = sharp
    sub_ext=0.0,      # extra FR-4 extension in front of the mouth [mm]
)

f_min, f_max = 1e9, 8e9
f_farfield = [2e9, 3e9, 4e9, 5e9, 6e9]
pad = 50.0
res_air, res_board, res_feed = 1.8, 0.75, 0.25
DO_FARFIELD = True
END_CRIT = 1e-4      # -40 dB
SHOW_MODEL = False
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, 'results', 'v2-variants')
PREFIX = 'v2'

# Original geometry constants [mm]
XC, YC0 = 44.4275, 27.77
RA, RB, RI, RS = 47.21, 88.85, 41.64, 30.0
NA, NB0 = 7.2175, 7.905
YPIN = 15.0
Y_TOP0 = 121.6


# ------------------------------------------------------------------
# Geometry
# ------------------------------------------------------------------
def arc(cx, cy, rx, ry, t0, t1, n=60):
    t = np.radians(np.linspace(t0, t1, n))
    return np.column_stack([cx + rx * np.cos(t), cy + ry * np.sin(t)])


def dims(p):
    xc = p['xc']
    ri = xc - 2.7875
    return dict(xc=xc, ra=xc + 2.7825, rb=p['rb'], ri=ri,
                riy=p.get('back_ry', 0) or ri, rs=xc - 14.4275, bw=xc + 4.9975)


def r_ellipse(theta_deg, ra, rb):
    t = np.radians(theta_deg)
    return 1.0 / np.sqrt((np.cos(t) / ra) ** 2 + (np.sin(t) / rb) ** 2)


def inner_edge(p, yc):
    """Inner (outer back) edge of the top arm: circle of radius RI centred at (XC, yc), 180 -> 90 deg.
    If corr_n > 0, radial corrugations are added (cut into the copper)."""
    D = dims(p)
    cx, cy, RI, RA, RB = D['xc'], yc, D['ri'], D['ra'], D['rb']
    if p['corr_n'] <= 0:
        return arc(cx, cy, RI, D['riy'], 180, 90, 120)
    n = int(p['corr_n'])
    centers = np.linspace(p['corr_a1'], p['corr_a0'], n)        # decreasing angle
    half = np.degrees(p['corr_w'] / 2 / RI)
    pts, a_prev = [], 180.0
    for ac in centers:
        d = p['corr_d'] if p.get('corr_d', 0) > 0 else p['corr_frac'] * (r_ellipse(ac, RA, RB) - RI)
        a_hi, a_lo = ac + half, ac - half
        pts.append(arc(cx, cy, RI, RI, a_prev, a_hi, 12))
        ro = RI + d
        pts.append(arc(cx, cy, ro, ro, a_hi, a_lo, 4))
        a_prev = a_lo
    pts.append(arc(cx, cy, RI, RI, a_prev, 90, 12))
    return np.vstack(pts)


def cos_taper(y0, y1, n=24):
    t = np.linspace(0.0, 1.0, n)
    x = 1.4554 + (2.7825 - 1.4554) * (1 - np.cos(np.pi * t)) / 2
    return np.column_stack([x, y0 + (y1 - y0) * t])


def geometry(p):
    fe = p['feed_ext']
    yc = YC0 + fe
    nb = NB0 + fe
    D = dims(p)
    XC, RA, RB, RS, BW = D['xc'], D['ra'], D['rb'], D['rs'], D['bw']
    ytop = yc + RB + 4.98 + p.get('sub_ext', 0)

    board = np.vstack([
        [[-14.4275, 10.0], [14.4275, 10.0]],
        arc(XC, yc, RS, RS, 180, 90, 60),
        [[BW, yc + RS], [BW, ytop], [-BW, ytop], [-BW, yc + RS]],
        arc(-XC, yc, RS, RS, 90, 0, 60)])

    ie = inner_edge(p, yc)
    outer = arc(XC, yc, RA, RB, 90, 180, 200)        # mouth edge, from tip to neck
    tr = p.get('tip_r', 0)
    if tr > 0:
        # corner (XC, yc+RB): Bezier rounding between the vertical edge and the mouth ellipse
        cum = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(outer, axis=0).T))])
        k = np.searchsorted(cum, tr)
        P0 = np.array([XC, yc + RB - tr]); P1 = np.array([XC, yc + RB]); P2 = outer[k]
        t = np.linspace(0, 1, 16)[:, None]
        fil = (1 - t) ** 2 * P0 + 2 * (1 - t) * t * P1 + t ** 2 * P2
        tip = np.vstack([fil, outer[k + 1:]])
    else:
        tip = np.vstack([[[XC, yc + RB]], outer[1:]])
    top = np.vstack([
        [[-10.0, 10.0], [10.0, 10.0], [10.0, yc - nb]],
        arc(10, yc, NA, nb, -90, -180, 40)[1:],
        ie,
        tip,
        arc(-10, yc, NA, nb, 0, -90, 40)[1:]])

    ie_b = ie[::-1].copy()
    ie_b[:, 0] *= -1                                   # mirror: inner edge of the bottom arm (90 -> 0)
    tp = cos_taper(19.865, yc)
    tl = tp[::-1].copy()
    tl[:, 0] *= -1
    bottom = np.vstack([
        [[-1.015, YPIN], [1.015, YPIN], [1.015, 19.365], [1.4554, 19.365]],
        tp,
        (tip * [-1, 1])[::-1][1:],
        ie_b,
        tl,
        [[-1.4554, 19.365], [-1.015, 19.365]]])

    pin_pad = arc(0, YPIN, 1.025, 1.025, 0, 360, 33)[:-1]
    return dict(board=board, top=top, bottom=bottom, pin_pad=pin_pad,
                yc=yc, ytop=ytop, **D)


VIAS = [(sx * 4.465, y, 0.40) for sx in (1, -1) for y in (12.46, 17.54)] + \
       [(sx * 2.54, y, 0.85) for sx in (1, -1) for y in (12.46, 17.54)]
GND_PADS = [(1.415, 11.035, 5.465, 18.965), (-5.465, 11.035, -1.415, 18.965)]


def merge_lines(important, filler, min_d=None):
    """Keep the important lines; add filler lines only where they are at least min_d from existing lines."""
    if min_d is None:
        min_d = 0.5 * res_feed
    kept = list(np.unique(np.round(np.asarray(important, float), 4)))
    for v in np.unique(np.round(np.asarray(filler, float), 4)):
        if np.min(np.abs(np.asarray(kept) - v)) >= min_d:
            kept.append(v)
    return np.unique(kept)


# ------------------------------------------------------------------
# Simulation
# ------------------------------------------------------------------
def simulate(p, tag, do_ff=DO_FARFIELD, run=True):
    from CSXCAD import ContinuousStructure
    from openEMS import openEMS
    from openEMS.physical_constants import EPS0

    g = geometry(p)
    h = p['h']
    sim_path = os.path.join(ROOT, 'sim_' + tag)   # raw openEMS data (git-ignored)
    f0, fc = 0.5 * (f_min + f_max), 0.5 * (f_max - f_min)

    FDTD = openEMS(NrTS=100000, EndCriteria=END_CRIT)
    FDTD.SetGaussExcite(f0, fc)
    FDTD.SetBoundaryCond(['PML_8'] * 6)
    CSX = ContinuousStructure()
    FDTD.SetCSX(CSX)
    mesh = CSX.GetGrid()
    mesh.SetDeltaUnit(1e-3)

    kappa = 2 * np.pi * 4e9 * EPS0 * p['eps_r'] * p['tand']    # loss referenced to ~4 GHz
    fr4 = CSX.AddMaterial('FR4', epsilon=p['eps_r'], kappa=kappa)
    pec = CSX.AddMetal('PEC')

    b = g['board']
    fr4.AddLinPoly(points=[b[:, 0], b[:, 1]], norm_dir='z', elevation=0, length=h, priority=1)
    for key, z in (('top', h), ('bottom', 0), ('pin_pad', 0)):
        q = g[key]
        pec.AddPolygon(points=[q[:, 0], q[:, 1]], norm_dir='z', elevation=z, priority=10)
    for (x0, y0, x1, y1) in GND_PADS:
        pec.AddBox([x0, y0, 0], [x1, y1, 0], priority=10)
    for (x, y, r) in VIAS:
        pec.AddCylinder([x, y, 0], [x, y, h], r, priority=10)

    rp = 0.635
    port = FDTD.AddLumpedPort(1, 50, [-rp, YPIN - rp, 0], [rp, YPIN + rp, h], 'z', 1.0, priority=5)

    yc, ytop = g['yc'], g['ytop']
    XC, BW, RS, RI, RB = g['xc'], g['bw'], g['rs'], g['ri'], g['rb']
    x_imp = [-BW - pad, BW + pad, -BW, BW, -XC, XC, -14.4275, 14.4275,
             -10, 10, -5.465, -1.415, 1.415, 5.465, -2.7825, 2.7825, -rp, rp]
    x_fill = np.concatenate([np.arange(-BW + 1.0, BW - 0.99, res_board), np.arange(-6.0, 6.01, res_feed)])
    y_imp = [10 - pad, ytop + pad, 10, ytop, 11.035, 18.965, 19.365, 19.865,
             yc, yc + RS, yc + g['riy'], yc + RB, YPIN - rp, YPIN + rp]
    y_fill = np.concatenate([np.arange(10, ytop, res_board), np.arange(9.0, yc + 1.01, res_feed)])
    mesh.AddLine('x', merge_lines(x_imp, x_fill))
    mesh.AddLine('y', merge_lines(y_imp, y_fill))
    mesh.AddLine('z', [-pad, h + pad] + list(np.linspace(0, h, 5)))
    mesh.SmoothMeshLines('all', res_air, ratio=1.4)
    n = [mesh.GetQtyLines(d) for d in 'xyz']
    print('[{}] Mesh: {} x {} x {} = {:.2f} million cells'.format(tag, *n, np.prod(n) / 1e6))

    nf2ff = FDTD.CreateNF2FFBox() if do_ff else None
    os.makedirs(sim_path, exist_ok=True)
    if SHOW_MODEL:
        from CSXCAD import AppCSXCAD_BIN
        xml = os.path.join(sim_path, 'model.xml')
        CSX.Write2XML(xml)
        os.system(AppCSXCAD_BIN + ' "{}"'.format(xml))
    if run:
        FDTD.Run(sim_path, cleanup=True, verbose=1)

    f = np.linspace(f_min, f_max, 701)
    port.CalcPort(sim_path, f)
    s11 = port.uf_ref / port.uf_inc
    zin = port.uf_tot / port.if_tot
    res = dict(f=f, s11=s11, zin=zin, p_acc=np.real(port.P_acc))

    if do_ff:
        center = [0, (ytop + 10) / 2 * 1e-3, 0]
        phi = np.arange(0, 361, 2.0)
        theta = np.arange(-180, 181, 2.0)
        re = nf2ff.CalcNF2FF(sim_path, f_farfield, [90.0], phi, center=center, outfile='ffE.h5')
        rh = nf2ff.CalcNF2FF(sim_path, f_farfield, theta, [90.0], center=center, outfile='ffH.h5')
        ff = []
        for i, fr in enumerate(f_farfield):
            eff = re.Prad[i] / np.interp(fr, f, res['p_acc'])
            e = re.E_norm[i][0, :]
            hh = rh.E_norm[i][:, 0]
            dmax = 10 * np.log10(re.Dmax[i])
            d_e = 20 * np.log10(e / e.max()) + dmax
            d_h = 20 * np.log10(hh / hh.max()) + 10 * np.log10(rh.Dmax[i])
            d_y = np.interp(90.0, phi, d_e)
            ff.append(dict(f=fr, dmax=dmax, d_y=d_y, eff=eff,
                           g_y=d_y + 10 * np.log10(max(eff, 1e-6)),
                           phi=phi, d_e=d_e, theta=theta, d_h=d_h,
                           peak_phi=phi[np.argmax(d_e)]))
        res['ff'] = ff
    return res


def summary(tag, res):
    f, s = res['f'], 20 * np.log10(np.abs(res['s11']))
    m = (f >= 2e9) & (f <= 6e9)
    line = '{:>15s}: worst S11 in 2-6 GHz = {:6.2f} dB @ {:.2f} GHz'.format(
        tag, s[m].max(), f[m][np.argmax(s[m])] / 1e9)
    ok = s < -10
    # -10 dB band (the part containing 2.5 GHz)
    i2 = np.argmin(np.abs(f - 2.5e9))
    lo = hi = i2
    if ok[i2]:
        while lo > 0 and ok[lo - 1]:
            lo -= 1
        while hi < len(f) - 1 and ok[hi + 1]:
            hi += 1
        line += ' | -10 dB band {:.2f}-{:.2f} GHz'.format(f[lo] / 1e9, f[hi] / 1e9)
    print(line)
    for d in res.get('ff', []):
        print('      {:.1f} GHz: gain(+y) {:5.2f} dBi, Dmax {:5.2f} dBi, efficiency {:3.0f} %, beam {:.0f} deg'
              .format(d['f'] / 1e9, d['g_y'], d['dmax'], 100 * d['eff'], d['peak_phi']))
    return line


def plots(results):
    import matplotlib
    import matplotlib.pyplot as plt
    plt.figure(figsize=(8, 5))
    for tag, r in results.items():
        plt.plot(r['f'] / 1e9, 20 * np.log10(np.abs(r['s11'])), lw=2, label=tag)
    plt.axhline(-10, color='k', ls='--', lw=1)
    plt.axvspan(2, 6, color='0.9', zorder=0)
    plt.grid(True)
    plt.legend()
    plt.xlabel('Frequency (GHz)')
    plt.ylabel('S11 (dB)')
    plt.title('Antipodal Vivaldi - S11 (openEMS shape variants)')
    plt.savefig(os.path.join(OUT_DIR, PREFIX + '_s11.png'), dpi=150, bbox_inches='tight')

    for tag, r in results.items():
        np.savetxt(os.path.join(OUT_DIR, '{}_{}_s11.csv'.format(PREFIX, tag)),
                   np.column_stack([r['f'] / 1e9, 20 * np.log10(np.abs(r['s11'])),
                                    r['zin'].real, r['zin'].imag]),
                   delimiter=',', header='f_GHz,S11_dB,ReZin,ImZin', comments='')
        if 'ff' in r:
            fig, axs = plt.subplots(1, 2, subplot_kw=dict(projection='polar'), figsize=(11, 5))
            for d in r['ff']:
                lab = '{:.0f} GHz'.format(d['f'] / 1e9)
                axs[0].plot(np.radians(d['phi']), np.maximum(d['d_e'], -20), lw=1.5, label=lab)
                axs[1].plot(np.radians(d['theta']), np.maximum(d['d_h'], -20), lw=1.5, label=lab)
            for ax, t in zip(axs, ['E-plane (xy) [dBi]', 'H-plane (yz) [dBi]']):
                ax.set_rmin(-20)
                ax.set_title(t)
            axs[1].legend(loc='lower right', bbox_to_anchor=(1.35, 0))
            fig.savefig(os.path.join(OUT_DIR, '{}_{}_pattern.png'.format(PREFIX, tag)),
                        dpi=150, bbox_inches='tight')


# ------------------------------------------------------------------
# Variants to run: each one overrides values in P.
# Comment out the ones you do not need. Each takes ~6-7 minutes.
# ------------------------------------------------------------------
VARIANTS = {
    'original':        dict(xc=44.4275, rb=88.85),    # first design, for comparison
    'A_proposed':      dict(),                        # wide mouth + long flare
    'B_round_tip':     dict(tip_r=10),               # A + rounded arm tips
    'C_back_edge':     dict(back_ry=60),              # A + elliptical arm back edge
    'D_fr4_extension': dict(sub_ext=20),              # A + 20 mm FR-4 in front of the mouth
}

if __name__ == '__main__':
    results = {}
    lines = []
    for tag, mods in VARIANTS.items():
        p = dict(P)
        p.update(mods)
        results[tag] = simulate(p, tag)
        lines.append(summary(tag, results[tag]))
        plots(results)                      # update the plots after every variant
    print('\n===== SUMMARY =====')
    for tag in results:
        summary(tag, results[tag])
    with open(os.path.join(OUT_DIR, PREFIX + '_summary.txt'), 'w') as fh:
        fh.write('\n'.join(lines))
    import matplotlib.pyplot as plt
    plt.show()
