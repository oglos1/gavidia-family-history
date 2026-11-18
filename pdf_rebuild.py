#!/usr/bin/env python3
"""Rebuild the two Gavidia family-tree PDFs (English + Spanish) with ReportLab.

Recreates the Oct 4, 2026 originals (whose generation script was lost) from the
PDF content streams / reference renders, with the Nov 2026 content updates:

  p.1  - parents' boxes gain birth/death dates; parentage lines under them
       - siblings bullet 1: "eight verified children" (was "ten")
       - footer: birthplace confirmed by civil birth record (Santa Ana, P. No. 2223)
  p.2  - Maria Teresa's parents now known: Santiago Gonzalez / Susana Jiron
       - her dark-blue box widened + ES subtitle shrunk (fixes the overflow)
       - next-steps item 1: parents now known (checkmark); footer dashed-box
         clause dropped (parents boxes are now solid cream, like other known people)
  p.3  - (Spanish only) italic update note under the subtitle (Q5 answered, Q4 partial)

Layout is US Letter (612 x 792 pt), Helvetica family, navy #1F3A5F header,
gold #B8892B rule, cream #FAF6EC boxes, light-blue #E8EEF6 child boxes.
All coordinates were recovered from the original PDFs' content streams, so the
rebuild matches the originals except where a change is listed above.

Usage:  python3 pdf_rebuild.py
Writes: assets/Gavidia_Family_Tree.pdf  (2 pages)
        assets/Arbol_Genealogico_Gavidia_ES.pdf  (3 pages)
"""

import os
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.colors import HexColor, white
from reportlab.pdfgen import canvas
from reportlab.pdfbase.pdfmetrics import stringWidth

BASE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(BASE, "assets")

# ---------------------------------------------------------------- palette ---
NAVY = HexColor("#1F3A5F")
GOLD = HexColor("#B8892B")
CREAM = HexColor("#FAF6EC")
LIGHTBLUE = HexColor("#E8EEF6")
DARK = HexColor("#1F2937")
GRAY = HexColor("#6B7280")
LINE = HexColor("#4B5563")
LIGHTTEXT = HexColor("#D8E1EE")
RULEGRAY = HexColor("#9CA3AF")

W, H = LETTER  # 612 x 792

F = "Helvetica"
FB = "Helvetica-Bold"
FO = "Helvetica-Oblique"
DING = "ZapfDingbats"
CHECK = "\x34"  # ZapfDingbats checkmark

# The U+2713 checkmark is not in Helvetica/WinAnsi, so render it with DejaVu
# Sans (present on this machine) when available; otherwise draw it as vectors.
CHECK_FONT = None
try:
    from reportlab.pdfbase import pdfmetrics as _pm
    from reportlab.pdfbase.ttfonts import TTFont as _TTFont
    import glob as _glob
    _dj = _glob.glob("/usr/share/fonts/**/DejaVuSans.ttf", recursive=True)
    if _dj:
        _pm.registerFont(_TTFont("DejaVu", _dj[0]))
        CHECK_FONT = "DejaVu"
except Exception:
    CHECK_FONT = None

# ---------------------------------------------------------------- helpers ---
def centered(c, text, font, size, cx, y, color=DARK):
    c.setFont(font, size)
    c.setFillColor(color)
    c.drawCentredString(cx, y, text)


def left(c, text, font, size, x, y, color=DARK):
    c.setFont(font, size)
    c.setFillColor(color)
    c.drawString(x, y, text)


def rbox(c, x0, y0, x1, y1, fill, stroke, lw=1.3, dash=None, r=7):
    c.setFillColor(fill)
    c.setStrokeColor(stroke)
    c.setLineWidth(lw)
    if dash:
        c.setDash(*dash)
    c.roundRect(x0, y0, x1 - x0, y1 - y0, r, stroke=1, fill=1)
    if dash:
        c.setDash()


def hline(c, x0, x1, y, color=LINE, lw=1.4):
    c.setStrokeColor(color)
    c.setLineWidth(lw)
    c.line(x0, y, x1, y)


def vline(c, x, y0, y1, color=LINE, lw=1.4):
    c.setStrokeColor(color)
    c.setLineWidth(lw)
    c.line(x, y0, x, y1)


def header(c, title, subtitle):
    """Navy band + gold rule + centered title/subtitle (original geometry)."""
    c.setFillColor(NAVY)
    c.rect(0, 702, W, 90, stroke=0, fill=1)
    c.setFillColor(GOLD)
    c.rect(0, 698, W, 4, stroke=0, fill=1)
    centered(c, title, FB, 22, W / 2, 747, white)
    centered(c, subtitle, FO, 11.5, W / 2, 724, white)


def footer_lines(c, lines, ys=(38, 28, 18)):
    for text, y in zip(lines, ys):
        centered(c, text, FO, 8, W / 2, y, GRAY)


def wrap_tokens(tokens, max_width):
    """Greedy word wrap. tokens: list of (text, font, size) words (no spaces).
    Returns a list of lines, each a list of tokens."""
    lines, cur, cur_w = [], [], 0.0
    for text, font, size in tokens:
        w = stringWidth(text, font, size)
        sp = stringWidth(" ", font, size) if cur else 0.0
        if cur and cur_w + sp + w > max_width:
            lines.append(cur)
            cur, cur_w = [(text, font, size)], w
        else:
            if cur:
                cur_w += sp
            cur.append((text, font, size))
            cur_w += w
    if cur:
        lines.append(cur)
    return lines


def draw_tokens(c, tokens, x, y):
    """Draw one wrapped line of tokens left-aligned at x."""
    cx = x
    for i, (text, font, size) in enumerate(tokens):
        if i > 0:
            cx += stringWidth(" ", font, size)
        if font == DING:  # checkmark token
            if CHECK_FONT:
                c.setFont(CHECK_FONT, size)
                c.setFillColor(DARK)
                c.drawString(cx, y, "\u2713")
            else:  # vector fallback
                c.setStrokeColor(DARK)
                c.setLineWidth(1.4)
                c.setLineCap(1)
                p = c.beginPath()
                p.moveTo(cx + 0.5, y + 3)
                p.lineTo(cx + 2.8, y + 0.5)
                p.lineTo(cx + 7, y + 7.5)
                c.drawPath(p, stroke=1, fill=0)
            cx += stringWidth(CHECK, DING, size)
            continue
        c.setFont(font, size)
        c.setFillColor(DARK)
        c.drawString(cx, y, text)
        cx += stringWidth(text, font, size)


def tokenize(text, font, size, check=True):
    """Split text into word tokens; a U+2713 becomes a checkmark token."""
    out = []
    for word in text.split(" "):
        if check and word == "\u2713":
            out.append((CHECK, DING, size))
        else:
            out.append((word, font, size))
    return out


def person_box(c, x0, y0, x1, y1, fill, stroke, name, sub, name_size=10.5,
               sub_size=9, name_y=None, sub_y=None, name_color=DARK,
               sub_color=GRAY, dash=None, lw=1.3):
    rbox(c, x0, y0, x1, y1, fill, stroke, lw=lw, dash=dash)
    cx = (x0 + x1) / 2
    if name_y is None:
        name_y = y0 + 24.75
    if sub_y is None:
        sub_y = y0 + 12.25
    centered(c, name, FB, name_size, cx, name_y, name_color)
    if sub:
        centered(c, sub, F, sub_size, cx, sub_y, sub_color)


# ============================================================== PAGE 1 ======
def page1(c, L):
    header(c, "Capit\u00e1n Carlos Gavidia Castro", L["p1_sub"])
    left(c, L["p1_family"], FB, 12, 54, 672, NAVY)

    # --- parents (now with dates; parentage note underneath each box) ---
    # box y 603-647; name 633, dates 621.5, label 610
    for (x0, x1, name, dates, label, note) in (
            (110, 300, "Jos\u00e9 Gavidia", "1884 \u2013 1941", L["father"],
             L["jose_note"]),
            (312, 502, "Carlota Castro de Gavidia", "1893 \u2013 1938", L["mother"],
             L["carlota_note"])):
        rbox(c, x0, 603, x1, 647, CREAM, GOLD)
        cx = (x0 + x1) / 2
        centered(c, name, FB, 10.5, cx, 633)
        centered(c, dates, F, 9, cx, 621.5)
        centered(c, label, F, 9, cx, 610, GRAY)
        centered(c, note, FO, 7.5, cx, 594, GRAY)

    # connectors: parents -> Carlos
    hline(c, 300, 312, 625)
    vline(c, 306, 590, 625)
    hline(c, 205, 306, 590)
    vline(c, 205, 556, 590)

    # --- Carlos (dark blue) + Maria Teresa (cream) ---
    rbox(c, 105, 512, 305, 558, NAVY, NAVY)
    centered(c, "Carlos Gavidia Castro", FB, L["carlos_name_size"], 205,
             L["carlos_name_y"], white)
    centered(c, L["carlos_sub"], F, 9, 205, L["carlos_sub_y"], LIGHTTEXT)
    person_box(c, 337, 512, 537, 558, CREAM, GOLD,
               "Mar\u00eda Teresa Gonz\u00e1lez", L["wife_label"])

    # connectors: couple -> children
    hline(c, 305, 337, 535)
    vline(c, 321, 480, 535)
    hline(c, 90, 520, 480)
    for x in (105, 235, 365, 495):
        vline(c, x, 462, 480)
    centered(c, L["children"], FB, 10, 321, 497, NAVY)

    # --- children ---
    kids = [("Carlos Gavidia II", L["son"]),
            ("Memo Gavidia", L["son"]),
            ("Mario Gavidia", L["son"]),
            ("Tony Gavidia", L["tony_sub"])]
    for i, (name, sub) in enumerate(kids):
        x0 = 46 + i * 130
        person_box(c, x0, 416, x0 + 118, 460, LIGHTBLUE, NAVY, name, sub)

    # --- siblings (bullet 1 wraps to two lines; rest of page shifts down 14) ---
    left(c, L["siblings"], FB, 11, 54, 385, NAVY)
    y = 368
    for bullet in L["sib_bullets"]:
        tokens = tokenize(bullet, F, 9.5, check=False)
        lines = wrap_tokens(tokens, 496)
        for j, ln in enumerate(lines):
            draw_tokens(c, ln, 62 if j == 0 else 72.6, y)
            y -= 14
    # --- life (shifted down 14 from the original to make room) ---
    left(c, L["life"], FB, 11, 54, 286, NAVY)
    y = 269
    for year, text in L["life_rows"]:
        left(c, year, FB, 9.5, 62, y, GOLD)
        left(c, text, F, 9.5, 120, y)
        y -= 15

    # --- Remembered box (shifted down 14) ---
    rbox(c, 54, 86, 558, 142, CREAM, GOLD, lw=1.2)
    left(c, L["remembered"], FB, 10, 66, 124)
    left(c, L["remembered_l1"], F, 9.5, 66, 109)
    left(c, L["remembered_l2"], F, 9.5, 66, 96)

    footer_lines(c, L["p1_footer"])


# ============================================================== PAGE 2 ======
def page2(c, L):
    header(c, L["p2_title"], L["p2_sub"])
    left(c, L["parents"], FB, 12, 54, 672, NAVY)

    # --- parents: now KNOWN, so solid cream/gold boxes (was dashed/unknown) ---
    person_box(c, 110, 603, 300, 647, CREAM, GOLD,
               "Santiago Gonz\u00e1lez", L["father_note"], sub_size=8.5)
    person_box(c, 312, 603, 502, 647, CREAM, GOLD,
               "Susana Jir\u00f3n", L["mother_note"], sub_size=8.5)

    # connectors: parents -> Maria Teresa
    hline(c, 300, 312, 625)
    vline(c, 306, 575, 625)

    # --- Maria Teresa: WIDENED box (156-456, was 186-426) so the subtitle fits.
    #     ES subtitle also shrunk 9 -> 8.5 pt. ---
    rbox(c, 156, 530, 456, 576, NAVY, NAVY)
    centered(c, "Mar\u00eda Teresa Gonz\u00e1lez", FB, L["mt_name_size"], 306,
             L["mt_name_y"], white)
    centered(c, L["mt_sub"], F, L["mt_sub_size"], 306, L["mt_sub_y"], LIGHTTEXT)

    # connectors: Maria Teresa -> two marriages
    vline(c, 306, 500, 530)
    hline(c, 165, 447, 500)
    vline(c, 165, 485, 500)
    vline(c, 447, 485, 500)
    centered(c, L["m1"], FB, 9, 165, 507, GOLD)
    centered(c, L["m2"], FB, 9, 447, 507, GOLD)

    # --- spouses ---
    person_box(c, 50, 438, 280, 482, CREAM, GOLD,
               "Carlos Gavidia Castro", "1915 - 1944")
    person_box(c, 332, 438, 562, 482, CREAM, GOLD,
               L["ayala"], L["ayala_sub"])
    centered(c, L["children"], FB, 10, 165, 424, NAVY)
    centered(c, L["children"], FB, 10, 447, 424, NAVY)
    vline(c, 165, 375, 438)
    vline(c, 447, 375, 438)

    # --- children, left column (4) / right column (2) ---
    left_kids = [("Carlos Gavidia II", L["son"]),
                 ("Memo Gavidia", L["son"]),
                 ("Mario Gavidia", L["son"]),
                 ("Tony Gavidia", L["tony_sub2"])]
    right_kids = [("Gloria Gavidia Ayala", L["daughter"]),
                  ("Herbert Ayala", L["son"])]
    ys = (375, 325, 275, 225)
    for (name, sub), y0 in zip(left_kids, ys):
        person_box(c, 65, y0, 265, y0 + 40, LIGHTBLUE, NAVY, name, sub)
    for (name, sub), y0 in zip(right_kids, ys[:2]):
        person_box(c, 347, y0, 547, y0 + 40, LIGHTBLUE, NAVY, name, sub)
    # connectors between stacked child boxes
    for y0 in (375, 325, 275):
        vline(c, 165, y0 - 10, y0)
    vline(c, 447, 365, 375)

    # --- next steps (item 1 wraps to two lines) ---
    rbox(c, 54, 70, 558, 178, CREAM, GOLD, lw=1.2)
    left(c, L["next_title"], FB, 10.5, 66, 160, NAVY)
    y = 143
    for item in L["next_items"]:
        tokens = tokenize(item, F, 9.5)
        lines = wrap_tokens(tokens, 486)
        for j, ln in enumerate(lines):
            draw_tokens(c, ln, 66 if j == 0 else 78, y)
            y -= 15

    footer_lines(c, L["p2_footer"])


# ============================================================== PAGE 3 ======
def page3_es(c):
    header(c, "Preguntas para Ricardo",
           "Con cari\u00f1o, para completar la historia de nuestra familia")

    # update note, italic, centred under the subtitle (3 lines, 9.5 pt)
    note = ("Actualizaci\u00f3n (nov. 2026): la pregunta 5 ya tiene respuesta "
            "\u2014 los padres de Mar\u00eda Teresa son Santiago Gonz\u00e1lez y "
            "Susana Jir\u00f3n (Registro de la Penitenciar\u00eda Central, 1944). "
            "La pregunta 4, parcialmente: la madre de Jos\u00e9 era Carmen "
            "Gavidia (c. 1866\u20131961); su padre sigue desconocido.")
    lines = wrap_tokens(tokenize(note, FO, 9.5, check=False), 500)
    y = 686
    for ln in lines:
        w = sum(stringWidth(t, f, s) for t, f, s in ln) \
            + stringWidth(" ", F, 9.5) * (len(ln) - 1)
        draw_tokens(c, ln, (W - w) / 2, y)
        y -= 13

    # everything below shifts down 52 pt to make room for the note
    rbox(c, 54, 588, 558, 654, CREAM, GOLD, lw=1.2)
    left(c, "AGRADECIMIENTO", FB, 10.5, 66, 636, NAVY)
    left(c, "Gracias, Ricardo, por preservar el apellido y la historia de la familia Gavidia, y por tu",
         F, 9.5, 66, 621)
    left(c, "colaboraci\u00f3n con el Museo Nacional de Aviaci\u00f3n, donde honras la memoria de nuestro abuelo.",
         F, 9.5, 66, 608)

    questions = [
        "\u00bfEn qu\u00e9 a\u00f1o y c\u00f3mo fue incluido nuestro abuelo en el Museo Nacional de Aviaci\u00f3n? \u00bfQui\u00e9n ayud\u00f3?",
        "\u00bfQu\u00e9 objetos suyos se exhiben en el museo (carta, uniforme, fotos, otros)?",
        "\u00bfQu\u00e9 sabes de la familia Castro (Carlota Castro y su hermano Jos\u00e9 Cipriano Castro Bernal)?",
        "\u00bfC\u00f3mo se llamaban nuestros bisabuelos del lado Gavidia y de qu\u00e9 pueblo eran? \u00bfHay v\u00ednculo con Espa\u00f1a?",
        "\u00bfQu\u00e9 sabes de los padres de la abuela Mar\u00eda Teresa Gonz\u00e1lez y de d\u00f3nde era su familia?",
        "\u00bfD\u00f3nde puedo conseguir una copia de Pugna a un dictador? \u00bfQui\u00e9n la public\u00f3?",
        "\u00bfHay cartas, fotos o documentos que podamos escanear y compartir en familia?",
        "\u00bfMe puedes compartir el contacto de Gloria, Herbert y otros primos?",
    ]
    y = 564
    for i, q in enumerate(questions, 1):
        left(c, "%d." % i, FB, 9.5, 54, y, NAVY)
        left(c, q, F, 9.5, 70, y)
        c.setStrokeColor(RULEGRAY)
        c.setLineWidth(0.6)
        c.line(70, y - 18, 558, y - 18)
        c.line(70, y - 34, 558, y - 34)
        y -= 56

    centered(c, "Respuestas en espa\u00f1ol (o como prefieras). \u00a1Gracias, primo! Dios te bendiga a ti y a tu familia.",
             FO, 8, W / 2, 38, GRAY)


# ============================================================== CONTENT =====
EN = {
    "p1_sub": "Salvadoran Air Force pilot  |  1915 - 1944",
    "p1_family": "HIS FAMILY",
    "father": "Father", "mother": "Mother",
    "jose_note": "Son of Carmen Gavidia (c. 1866\u20131961)",
    "carlota_note": "Daughter of Juan Jos\u00e9 Castro and Isabel Bernal",
    "carlos_name_size": 11, "carlos_name_y": 538, "carlos_sub_y": 524,
    "carlos_sub": "b. Nov 24, 1915, Santa Ana",
    "wife_label": "Wife (later Ayala)",
    "children": "Children", "son": "Son", "tony_sub": "4th child",
    "siblings": "HIS SIBLINGS",
    "sib_bullets": [
        "-  Second of eight verified children of Jos\u00e9 Gavidia and Carlota Castro (total disputed: the biography says ten; the 1936 photo shows eight).",
        "-  Jos\u00e9 Gavidia Castro, the eldest brother, lived to age 105 (died 2016).",
        "-  Jos\u00e9 Antonio Gavidia Castro, a younger brother, also served in the army.",
        "-  Maternal uncle: Jos\u00e9 Cipriano Castro Bernal (1895-1958), of Santa Ana.",
    ],
    "life": "HIS LIFE",
    "life_rows": [
        ("1931", "Entered the Military School as a cadet at age 15."),
        ("1933", "Graduated as a second lieutenant (Oct 20)."),
        ("1936", "Chosen for the Aviation School at Ilopango; promoted to lieutenant."),
        ("1937", "Became a military pilot on Jan 5; later married Mar\u00eda Teresa."),
        ("1939-42", "Left aviation; managed haciendas El \u00c1ngel and El Carmen."),
        ("1943", "Returned to the air force; promoted to captain (Nov 12)."),
        ("1944", "Died April 24 after the failed April uprising."),
    ],
    "remembered": "Remembered",
    "remembered_l1": "Some of his personal belongings are on permanent display at the National",
    "remembered_l2": "Aviation Museum in Ilopango, shared by the Gavidia family.",
    "p1_footer": [
        "Sources: Flotilla A\u00e9rea, \"Capit\u00e1n Carlos Gavidia Castro (1915-1944)\" (with Ricardo Gavidia); Gavidia family accounts.",
        "Birthplace confirmed by his civil birth record (Santa Ana, P. No. 2223).",
    ],
    "p2_title": "The Family of Mar\u00eda Teresa Gonz\u00e1lez",
    "p2_sub": "Grandmother  |  two marriages  |  author of Pugna a un dictador (1987)",
    "parents": "HER PARENTS",
    "father_note": "named in the 1944 prison marriage record",
    "mother_note": "named in the 1944 prison marriage record",
    "mt_name_size": 12, "mt_name_y": 556, "mt_sub_size": 9, "mt_sub_y": 541,
    "mt_sub": "Maiden name Gonz\u00e1lez; later de Gavidia, then Ayala",
    "m1": "1ST MARRIAGE (from 1937)", "m2": "2ND MARRIAGE (after 1944)",
    "ayala": "Mr. Ayala", "ayala_sub": "first name unknown",
    "daughter": "Daughter", "tony_sub2": "4th child; father of Ricardo",
    "next_title": "NEXT STEPS TO FIND HER FAMILY",
    "next_items": [
        "1.  \u2713 Her parents are now known: Santiago Gonz\u00e1lez and Susana Jir\u00f3n, named in her 1944 prison marriage record (Central Penitentiary registry, p. 296).",
        "2.  Her baptism record (about 1910-1918) and her second marriage record.",
        "3.  Her book Pugna a un dictador (1987) for family background.",
        "4.  Ask Gloria and Herbert for her papers, photos, and family stories.",
    ],
    "p2_footer": [
        "Prepared from Flotilla A\u00e9rea and information shared by the Gavidia family (Ricardo Gavidia).",
        "Names and dates should be confirmed against records.",
    ],
}

ES = {
    "p1_sub": "Piloto de la Fuerza A\u00e9rea Salvadore\u00f1a  |  1915 - 1944",
    "p1_family": "SU FAMILIA",
    "father": "Padre", "mother": "Madre",
    "jose_note": "Hijo de Carmen Gavidia (c. 1866\u20131961)",
    "carlota_note": "Hija de Juan Jos\u00e9 Castro e Isabel Bernal",
    "carlos_name_size": 10.5, "carlos_name_y": 537.75, "carlos_sub_y": 525.25,
    "carlos_sub": "n. 24 de nov. de 1915, Santa Ana",
    "wife_label": "Esposa (luego Ayala)",
    "children": "Hijos", "son": "Hijo", "tony_sub": "4.\u00ba hijo",
    "siblings": "SUS HERMANOS",
    "sib_bullets": [
        "-  Segundo de ocho hijos verificados de Jos\u00e9 Gavidia y Carlota Castro (total disputado: la biograf\u00eda dice diez; la foto de 1936 muestra ocho).",
        "-  Jos\u00e9 Gavidia Castro, el hermano mayor, vivi\u00f3 105 a\u00f1os (falleci\u00f3 en 2016).",
        "-  Jos\u00e9 Antonio Gavidia Castro, hermano menor, tambi\u00e9n fue militar.",
        "-  T\u00edo materno: Jos\u00e9 Cipriano Castro Bernal (1895-1958), de Santa Ana.",
    ],
    "life": "SU VIDA",
    "life_rows": [
        ("1931", "Ingres\u00f3 a la Escuela Militar como cadete a los 15 a\u00f1os."),
        ("1933", "Se gradu\u00f3 de subteniente (20 de octubre)."),
        ("1936", "Elegido para la Escuela de Aviaci\u00f3n en Ilopango; ascendi\u00f3 a teniente."),
        ("1937", "Obtuvo el t\u00edtulo de piloto militar el 5 de enero; luego se cas\u00f3 con Mar\u00eda Teresa."),
        ("1939-42", "Dej\u00f3 la aviaci\u00f3n; administr\u00f3 las haciendas El \u00c1ngel y El Carmen."),
        ("1943", "Regres\u00f3 a la Fuerza A\u00e9rea; ascendido a capit\u00e1n (12 de noviembre)."),
        ("1944", "Falleci\u00f3 el 24 de abril tras el fallido alzamiento de abril."),
    ],
    "remembered": "Recordado",
    "remembered_l1": "Algunos de sus objetos personales se exhiben de forma permanente en el Museo",
    "remembered_l2": "Nacional de Aviaci\u00f3n en Ilopango, gracias a la colaboraci\u00f3n de la familia Gavidia.",
    "p1_footer": [
        "Con gratitud a Ricardo Gavidia por preservar el apellido y la historia de la familia Gavidia.",
        "Fuentes: Flotilla A\u00e9rea, \"Capit\u00e1n Carlos Gavidia Castro (1915-1944)\"; familia Gavidia. Lugar de nacimiento",
        "confirmado por su partida de nacimiento (Santa Ana, P. n.\u00ba 2223).",
    ],
    "p2_title": "La Familia de Mar\u00eda Teresa Gonz\u00e1lez",
    "p2_sub": "Abuela  |  dos matrimonios  |  autora de Pugna a un dictador (1987)",
    "parents": "SUS PADRES",
    "father_note": "nombrado en el acta de matrimonio de 1944",
    "mother_note": "nombrada en el acta de matrimonio de 1944",
    "mt_name_size": 10.5, "mt_name_y": 555.75, "mt_sub_size": 8.5, "mt_sub_y": 543.25,
    "mt_sub": "Apellido de soltera Gonz\u00e1lez; luego de Gavidia, despu\u00e9s Ayala",
    "m1": "1ER MATRIMONIO (desde 1937)", "m2": "2.\u00ba MATRIMONIO (despu\u00e9s de 1944)",
    "ayala": "Sr. Ayala", "ayala_sub": "nombre desconocido",
    "daughter": "Hija", "tony_sub2": "4.\u00ba hijo; padre de Ricardo",
    "next_title": "PR\u00d3XIMOS PASOS PARA ENCONTRAR A SU FAMILIA",
    "next_items": [
        "1.  \u2713 Sus padres ya se conocen: Santiago Gonz\u00e1lez y Susana Jir\u00f3n, nombrados en su acta de matrimonio de 1944 en prisi\u00f3n (Registro de la Penitenciar\u00eda Central, folio 296).",
        "2.  Su partida de bautizo (hacia 1910-1918) y el acta de su segundo matrimonio.",
        "3.  Su libro Pugna a un dictador (1987), para datos de su familia.",
        "4.  Pedir a Gloria y Herbert sus papeles, fotos e historias familiares.",
    ],
    "p2_footer": [
        "Con gratitud a Ricardo Gavidia por preservar el apellido y la historia de la familia Gavidia.",
        "Preparado con informaci\u00f3n de Flotilla A\u00e9rea y de la familia Gavidia (Ricardo Gavidia).",
        "Los nombres y fechas deben confirmarse con documentos.",
    ],
}


def build(lang, out_path, title):
    c = canvas.Canvas(out_path, pagesize=LETTER)
    c.setTitle(title)
    c.setAuthor("anonymous")
    c.setCreator("anonymous")
    page1(c, lang)
    c.showPage()
    page2(c, lang)
    c.showPage()
    if lang is ES:
        page3_es(c)
        c.showPage()
    c.save()
    print("wrote", out_path)


def main():
    build(EN, os.path.join(ASSETS, "Gavidia_Family_Tree.pdf"),
          "Gavidia Family Tree - Carlos Gavidia Castro")
    build(ES, os.path.join(ASSETS, "Arbol_Genealogico_Gavidia_ES.pdf"),
          "\u00c1rbol Geneal\u00f3gico de la Familia Gavidia")


if __name__ == "__main__":
    main()
