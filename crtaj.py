# -*- coding: utf-8 -*-
"""
Црта онтологију библиотека у Википодацима из датотека у podaci/.

    python crtaj.py                 → izlaz/ontologija.svg, .pdf, _600dpi.png
    python crtaj.py --sirina 4000   → друга ширина PNG-а у пикселима

Онтологија се допуњује уређивањем CSV датотека, не овог кода:
    podaci/klase.csv     класе (кутије)
    podaci/veze.csv      стрелице међу класама
    podaci/svojstva.csv  списак својстава у два доња оквира

Распоред се рачуна сам: свака класа у зони „pot” која води стрелицом ка
корену почиње нови ред, а ред се продужава удесно пратећи стрелице P279.
Стрелице се секу тачно на ивицама правоугаоника.
"""
import argparse, csv, html, os, sys
from collections import defaultdict

PUT = os.path.dirname(os.path.abspath(__file__))
F = "'DejaVu Sans', 'Segoe UI', Arial, sans-serif"
BOJE = {'srbija': ("#FBE5D0", "#C06A1E"), 'opsta': ("#EEEEEE", "#808080"),
        'stavka': ("#FFFFFF", "#1A1A1A")}
PLAVA, ZELENA, CRNA = "#2F5FC4", "#2E7D32", "#1A1A1A"
W = 1500
KOREN = 'Q7075'


# ── мерење и прелом текста ───────────────────────────────────────────────
def sirina(t, fs):
    uzak = sum(1 for c in t if c in 'іijlI.,:;() ')
    return (len(t) - uzak) * fs * 0.62 + uzak * fs * 0.32


def prelomi(t, fs, maxw):
    out = []
    for deo in t.split('|'):
        red = ''
        for r in deo.split():
            p = (red + ' ' + r).strip()
            if sirina(p, fs) > maxw and red:
                out.append(red); red = r
            else:
                red = p
        if red:
            out.append(red)
    return out


# ── цртеж ────────────────────────────────────────────────────────────────
class Crtez:
    def __init__(s, w):
        s.w, s.h, s.o = w, 0, []
        s.pocetak = (f'<defs>' + ''.join(
            f'<marker id="{i}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6.5" '
            f'markerHeight="6.5" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="{c}"/></marker>'
            for i, c in (('p', PLAVA), ('z', ZELENA), ('c', CRNA))) + '</defs>')

    def t(s, x, y, txt, fs, boja=CRNA, bold=False, anchor='middle'):
        b = 'font-weight="700" ' if bold else ''
        s.o.append(f'<text x="{x:.0f}" y="{y:.0f}" text-anchor="{anchor}" font-size="{fs}" '
                   f'{b}fill="{boja}">{html.escape(txt)}</text>')

    def kutija(s, x, y, w, qid, naziv, grupa, redovi=(), kolone=1,
               fs_q=29, fs_n=26, fs_r=22, deb=2, min_h=0):
        boja = BOJE[grupa]
        lin = prelomi(naziv, fs_n, w - 24) if naziv else []
        nr = -(-len(redovi) // kolone) if redovi else 0
        h = max(min_h, 22 + (fs_q * .8 + 8 if qid else 0) + len(lin) * (fs_n * .84 + 6)
                + nr * (fs_r * .84 + 6) + 14)
        s.o.append(f'<rect x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}" rx="8" '
                   f'fill="{boja[0]}" stroke="{boja[1]}" stroke-width="{deb}"/>')
        cx, yy = x + w / 2, y + 22
        if qid:
            yy += fs_q * .8; s.t(cx, yy, qid, fs_q, bold=True); yy += 8
        for l in lin:
            yy += fs_n * .84; s.t(cx, yy, l, fs_n, bold=True); yy += 6
        if kolone == 1:
            for r in redovi:
                yy += fs_r * .84; s.t(cx, yy, r, fs_r, '#333333'); yy += 6
        else:
            kw, y0 = (w - 30) / kolone, yy
            for k in range(kolone):
                yy = y0
                for r in redovi[k * nr:(k + 1) * nr]:
                    yy += fs_r * .84
                    s.t(x + 16 + kw * k, yy, r, fs_r, '#333333', anchor='start')
                    yy += 6
        s.h = max(s.h, y + h)
        return {'x': x, 'y': y, 'x2': x + w, 'y2': y + h, 'cx': cx, 'cy': y + h / 2}

    def linija(s, x1, y1, x2, y2, boja=PLAVA, mk='p', crt=False, lw=2.3):
        d = ' stroke-dasharray="9 7"' if crt else ''
        m = f' marker-end="url(#{mk})"' if mk else ''
        s.o.append(f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" '
                   f'stroke="{boja}" stroke-width="{lw}"{d}{m}/>')

    def spoji(s, a, b, boja=PLAVA, mk='p', crt=False, razmak=5):
        """Стрелица од кутије a до кутије b, пресечена тачно на обе ивице."""
        p1 = iseci(a, b['cx'], b['cy'], razmak)
        p2 = iseci(b, a['cx'], a['cy'], razmak)
        s.linija(p1[0], p1[1], p2[0], p2[1], boja, mk, crt)

    def snimi(s, ime, px, naslov):
        glava = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{s.w}" height="{s.h:.0f}" '
                 f'viewBox="0 0 {s.w} {s.h:.0f}" font-family="{F}">{s.pocetak}'
                 f'<rect width="{s.w}" height="{s.h:.0f}" fill="#FFFFFF"/>')
        t = glava + '\n'.join(s.o) + '</svg>'
        os.makedirs(os.path.join(PUT, 'izlaz'), exist_ok=True)
        p = os.path.join(PUT, 'izlaz', ime)
        open(p + '.svg', 'w', encoding='utf-8').write(t)
        try:
            import cairosvg
            cairosvg.svg2png(bytestring=t.encode(), write_to=p + '_600dpi.png', output_width=px)
            cairosvg.svg2pdf(bytestring=t.encode(), write_to=p + '.pdf')
        except ImportError:
            print('напомена: cairosvg није инсталиран, настао је само SVG '
                  '(pip install cairosvg)', file=sys.stderr)
        print(f'{ime}: {s.w} × {s.h:.0f} | однос в/ш {s.h / s.w:.2f} '
              f'| на 15,9 cm ширине: {15.9 * s.h / s.w:.1f} cm висине')


def iseci(k, tx, ty, razmak):
    """Тачка на ивици правоугаоника k у правцу тачке (tx, ty)."""
    dx, dy = tx - k['cx'], ty - k['cy']
    if dx == 0 and dy == 0:
        return k['cx'], k['cy']
    pw, ph = (k['x2'] - k['x']) / 2 + razmak, (k['y2'] - k['y']) / 2 + razmak
    t = min(pw / abs(dx) if dx else 9e9, ph / abs(dy) if dy else 9e9)
    return k['cx'] + dx * t, k['cy'] + dy * t


# ── учитавање података ───────────────────────────────────────────────────
def ucitaj(ime):
    with open(os.path.join(PUT, 'podaci', ime), encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def legenda(c, w, y, stavke, razmak, fs):
    uk = sum(64 + sirina(t, fs) + razmak for _, t in stavke) - razmak
    x = (w - uk) / 2
    for vrsta, t in stavke:
        if vrsta in BOJE:
            b = BOJE[vrsta]
            c.o.append(f'<rect x="{x:.0f}" y="{y-19:.0f}" width="32" height="24" rx="4" '
                       f'fill="{b[0]}" stroke="{b[1]}" stroke-width="2"/>')
        else:
            boja = ZELENA if vrsta == 'zel' else PLAVA
            d = ' stroke-dasharray="9 7"' if vrsta in ('zel', 'crt') else ''
            c.o.append(f'<line x1="{x:.0f}" y1="{y-8:.0f}" x2="{x+48:.0f}" y2="{y-8:.0f}" '
                       f'stroke="{boja}" stroke-width="2.5"{d} '
                       f'marker-end="url(#{"z" if vrsta == "zel" else "p"})"/>')
        c.t(x + 64, y, t, fs, '#333333', anchor='start')
        x += 64 + sirina(t, fs) + razmak


LEGENDA_1 = [('srbija', 'класа са установама из Србије'), ('opsta', 'општа класа'),
             ('stavka', 'ставка — установа на Википодацима')]
LEGENDA_2 = [('pun', 'P279 — поткласа'), ('crt', 'P279* — поткласа посредно'),
             ('zel', 'својство које повезује класе')]


def raspored_sirok(zona, po_qid, veze, svoj, redovi, prvi, px, ime):
    """Водоравни распоред, онакав какав је у објављеном раду:
    стабло поткласа расте надоле, својства стоје у кутији корена."""
    w = 2400
    c = Crtez(w)
    c.t(w / 2, 46, 'Библиотека у Википодацима: класе, везе међу класама и својства',
        32, bold=True)
    kut = {}
    nad = zona['nad']
    gw = 560
    x0 = (w - (len(nad) * gw + (len(nad) - 1) * 40)) / 2
    for i, k in enumerate(nad):
        kut[k['qid']] = c.kutija(x0 + i * (gw + 40), 84, gw, k['qid'], k['naziv'], k['grupa'],
                                 fs_q=26, fs_n=23)
    y = max(v['y2'] for v in kut.values()) + 54
    for k in zona['medju']:
        kut[k['qid']] = c.kutija(680, y, gw, k['qid'], k['naziv'], k['grupa'], fs_q=26, fs_n=23)
        y = kut[k['qid']]['y2'] + 54
    kor = zona['koren'][0]
    red_u = [f"{s['kod']} ({s['naziv']})" for s in svoj if s['blok'] == 'ustanova']
    kut[KOREN] = c.kutija(680, y, gw, KOREN, kor['naziv'], kor['grupa'], red_u,
                          fs_q=26, fs_n=23, fs_r=19)
    st = zona['stavka'][0]
    kut['_stavka'] = c.kutija(80, y + 70, 480, '', st['naziv'], st['grupa'], fs_n=22)
    c.t(320, kut['_stavka']['y2'] + 26, '(иста установа може носити више класа)', 18, '#666666')

    yv = y
    for k in zona['veza']:
        kk = c.kutija(1500, yv, 440, k['qid'], k['naziv'], k['grupa'], fs_q=24, fs_n=21)
        kut[k['qid']] = kk
        yv = kk['y2'] + 14
    red_i = [f"{s['kod']} ({s['naziv']})" for s in svoj if s['blok'] == 'identifikator']
    c.kutija(1980, y, 400, '', 'Спољашњи идентификатори|уписани на истим установама',
             'stavka', red_i, fs_n=21, fs_r=19, deb=1.6)

    # стабло: колона по грани, ред по дубини
    yt = max(kut[KOREN]['y2'], yv) + 96
    kw, gap = 450, 22
    xt = (w - (5 * kw + 4 * gap)) / 2
    c.t(xt, yt - 30, 'Поткласе (P279)', 24, '#444444', bold=True, anchor='start')
    dubina_y = {}
    for ci, red in enumerate(redovi):
        for di, q in enumerate(red):
            k = po_qid[q]
            dodaci = [s for s in (k['svojstva'] or '').split(';') if s.strip()]
            yy = dubina_y.get(di, yt + di * 110)
            kut[q] = c.kutija(xt + ci * (kw + gap), yy, kw, q, k['naziv'], k['grupa'],
                              dodaci, fs_q=24, fs_n=21, fs_r=18)
            dubina_y[di] = yy
            if di + 1 not in dubina_y:
                dubina_y[di + 1] = kut[q]['y2'] + 46

    for v in veze:
        a_, b_ = kut.get(v['od']), kut.get(v['do'])
        if v['vrsta'] == 'P31':
            c.spoji(kut['_stavka'], kut[KOREN], CRNA, 'c')
            c.t((kut['_stavka']['x2'] + kut[KOREN]['x']) / 2, kut[KOREN]['cy'] - 12,
                'P31', 20, CRNA, bold=True)
        elif v['vrsta'].startswith('P279') and a_ and b_:
            c.spoji(a_, b_, crt=v['vrsta'] == 'P279*')
        elif a_ and b_:
            y0 = min(max(b_['cy'], a_['y'] + 24), a_['y2'] - 24)
            c.linija(a_['x2'], y0, b_['x'] - 5, b_['cy'], ZELENA, 'z', True)
            c.t((a_['x2'] + b_['x']) / 2, (y0 + b_['cy']) / 2 - 9, v['vrsta'], 19,
                ZELENA, bold=True)

    yl = c.h + 56
    legenda(c, w, yl, LEGENDA_1, 60, 21)
    legenda(c, w, yl + 38, LEGENDA_2, 66, 20)
    c.h = yl + 62
    c.snimi(ime, px, '')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--sirina', type=int, default=3756, help='ширина PNG-а у пикселима')
    ap.add_argument('--raspored', choices=['uspravan', 'sirok'], default='uspravan',
                    help='„sirok” је распоред из објављеног рада, „uspravan” стаје у страну')
    ap.add_argument('--ime', default=None)
    a = ap.parse_args()
    if a.ime is None:
        a.ime = 'ontologija' if a.raspored == 'uspravan' else 'ontologija_siroka'

    klase = ucitaj('klase.csv')
    veze = ucitaj('veze.csv')
    svoj = ucitaj('svojstva.csv')
    po_qid = {k['qid']: k for k in klase if k['qid']}
    zona = defaultdict(list)
    for k in klase:
        zona[k['zona']].append(k)
    for z in zona:
        zona[z].sort(key=lambda k: int(k['redosled'] or 0))

    p279 = [v for v in veze if v['vrsta'].startswith('P279')]
    roditelji = defaultdict(list)   # дете → [(родитељ, веза)]
    deca = defaultdict(list)        # родитељ → [(дете, веза)]
    for v in p279:
        roditelji[v['od']].append(v)
        deca[v['do']].append(v)

    # гране стабла: свака класа која води ка корену почиње грану,
    # која се продужава пратећи стрелице P279
    pot = [k['qid'] for k in zona['pot']]
    prvi = [q for q in pot if any(v['do'] == KOREN for v in roditelji[q])]
    redovi, uzeti = [], set()
    for q in prvi:
        red, tek = [q], q
        uzeti.add(q)
        while True:
            sl = [v['od'] for v in deca[tek] if v['od'] in pot and v['od'] not in uzeti]
            if not sl:
                break
            tek = sl[0]; red.append(tek); uzeti.add(tek)
        redovi.append(red)
    for q in pot:                         # класе ван стабла библиотека
        if q not in uzeti:
            redovi.append([q]); uzeti.add(q)

    if a.raspored == 'sirok':
        return raspored_sirok(zona, po_qid, veze, svoj, redovi, prvi, a.sirina, a.ime)

    c = Crtez(W)
    kut = {}
    c.t(W / 2, 48, 'Библиотека у Википодацима: класе, везе међу класама и својства',
        33, bold=True)

    # 1. наткласе, међукласа, корен, ставка
    nad = zona['nad']
    gw = (W - 52 - 20 * (len(nad) - 1)) / len(nad)
    for i, k in enumerate(nad):
        kut[k['qid']] = c.kutija(26 + i * (gw + 20), 82, gw, k['qid'], k['naziv'], k['grupa'],
                                 fs_q=31, fs_n=28)
    y = max(v['y2'] for v in kut.values()) + 64
    for k in zona['medju']:
        kut[k['qid']] = c.kutija(270, y, 460, k['qid'], k['naziv'], k['grupa'], fs_q=31, fs_n=28)
    y = max(kut[k['qid']]['y2'] for k in zona['medju']) + 56
    kor = zona['koren'][0]
    kut[KOREN] = c.kutija(270, y, 460, kor['qid'], kor['naziv'], kor['grupa'], fs_q=31, fs_n=28)
    st = zona['stavka'][0]
    kut['_stavka'] = c.kutija(830, y + 4, 530, '', st['naziv'], st['grupa'], fs_n=27)
    c.t(1095, kut['_stavka']['y2'] + 30, '(иста установа може носити више класа)', 22, '#666666')

    # 2. стабло поткласа, ред по грани
    Y0, RH, KW, XM = kut[KOREN]['y2'] + 118, 134, 430, 48
    X = [90 + i * 476 for i in range(max(len(r) for r in redovi))]
    c.t(W / 2, Y0 - 30, 'Поткласе (P279): лево општија класа, десно ужа', 26, '#444444', bold=True)
    for i, red in enumerate(redovi):
        yy = Y0 + i * RH
        for j, q in enumerate(red):
            k = po_qid[q]
            dodaci = [s for s in (k['svojstva'] or '').split(';') if s.strip()]
            kut[q] = c.kutija(X[j], yy, KW, q, k['naziv'], k['grupa'], dodaci, fs_r=22)
        if red[0] in prvi:                # крак ка усправној окосници
            v = next(v for v in roditelji[red[0]] if v['do'] == KOREN)
            c.linija(kut[red[0]]['x'], kut[red[0]]['cy'], XM, kut[red[0]]['cy'],
                     PLAVA, None, v['vrsta'] == 'P279*')
    posl = kut[redovi[len(prvi) - 1][0]]
    c.o.append(f'<path d="M{XM} {posl["cy"]:.0f} V{kut[KOREN]["cy"]:.0f} '
               f'H{kut[KOREN]["x"]:.0f}" fill="none" stroke="{PLAVA}" stroke-width="2.3" '
               f'marker-end="url(#p)"/>')
    c.t(XM + 54, kut[KOREN]['cy'] - 16, 'P279', 23, PLAVA, bold=True, anchor='start')

    # 3. све преостале стрелице, пресечене на ивицама кутија
    for v in p279:
        if v['do'] == KOREN and v['od'] in prvi:
            continue                      # већ нацртано преко окоснице
        a_, b_ = kut.get(v['od']), kut.get(v['do'])
        if a_ and b_:
            c.spoji(a_, b_, crt=v['vrsta'] == 'P279*')
    for v in veze:
        if v['vrsta'] == 'P31':
            c.spoji(kut['_stavka'], kut[KOREN], CRNA, 'c')
            c.t((kut['_stavka']['x'] + kut[KOREN]['x2']) / 2, kut[KOREN]['cy'] - 14,
                'P31', 23, CRNA, bold=True)
    for v in p279:                        # ознаке P279 на везама ка врху
        if v['do'] in [k['qid'] for k in zona['nad'] + zona['medju']]:
            a_, b_ = kut[v['od']], kut[v['do']]
            c.t((a_['cx'] + b_['cx']) / 2 + 40, (a_['cy'] + b_['cy']) / 2, 'P279',
                23, PLAVA, bold=True)

    # 4. својства, класе које она повезују, идентификатори
    Y1 = max(k['y2'] for q, k in kut.items() if q in po_qid and po_qid[q]['zona'] == 'pot') + 46
    vezane = zona['veza']
    visina_desno = len(vezane) * 91 + (len(vezane) - 1) * 12
    red_u = [f"{s['kod']} ({s['naziv']})" for s in svoj if s['blok'] == 'ustanova']
    sv = c.kutija(26, Y1, 712, '', f'Својства уписана на установама ({KOREN})', 'srbija',
                  red_u, fs_n=27, fs_r=25, min_h=visina_desno)
    c.t(1120, Y1 - 16, 'Својства која повезују са другим класама', 25, '#444444', bold=True)
    yv = Y1
    for k in vezane:
        kk = c.kutija(900, yv, 574, k['qid'], k['naziv'], k['grupa'], fs_q=26, fs_n=24)
        kod = next((v['vrsta'] for v in veze if v['do'] == k['qid'] and v['od'] == KOREN), '')
        c.linija(sv['x2'], kk['cy'], kk['x'], kk['cy'], ZELENA, 'z', True)
        c.t((sv['x2'] + kk['x']) / 2, kk['cy'] - 9, kod, 23, ZELENA, bold=True)
        yv = kk['y2'] + 12
    red_i = [f"{s['kod']} ({s['naziv']})" for s in svoj if s['blok'] == 'identifikator']
    idb = c.kutija(26, max(sv['y2'], yv) + 24, 1448, '',
                   'Спољашњи идентификатори уписани на истим установама', 'stavka',
                   red_i, kolone=3, fs_n=27, fs_r=23, deb=1.6)

    # 5. легенда
    yl = idb['y2'] + 52
    legenda(c, W, yl, LEGENDA_1, 56, 25)
    legenda(c, W, yl + 44, LEGENDA_2, 62, 23)
    c.h = yl + 70
    c.snimi(a.ime, a.sirina, 'ontologija')


if __name__ == '__main__':
    main()
