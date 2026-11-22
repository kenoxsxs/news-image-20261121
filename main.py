#!/usr/bin/env python3
"""The World in One Day - Saturday, 21 November 2026.

A deterministic newspaper front page drawn with the Python standard
library only: no Pillow, no system fonts, no network, no subprocess.
The image is rendered pixel by pixel into an RGB buffer. Text comes
from a hand-drawn vector serif font embedded below: every glyph is a
set of strokes (polylines) in a 12 x 14 unit grid, rendered through a
supersampled coverage mask, so edges are smooth like a Times face.
The PNG file is written by hand (signature, IHDR,
zlib-compressed IDAT, IEND).

Output goes to MAKEFUN_OUTPUT_DIR when set, else next to this file.
Running the program twice produces byte-identical output.
"""

import math
import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
NAVY = (46, 52, 104)
NAVY_DK = (36, 42, 88)
CREAM = (250, 247, 238)
PAPER = (255, 255, 255)
INK = (28, 28, 36)
GREY = (110, 105, 95)
SRC = (122, 102, 78)
GOLD = (198, 164, 110)
TICKER = (190, 96, 110)
BORDER = (206, 200, 184)
BLUE = (58, 96, 150)
PURPLE = (140, 125, 181)
TAN = (198, 141, 95)
TEAL = (77, 155, 144)
PINK = (197, 117, 147)
GREEN = (110, 160, 110)
STEEL = (99, 129, 169)
DARKBOX = (44, 36, 64)
PERU_BG = (44, 56, 110)
RED = (200, 40, 50)
YELLOW = (240, 200, 60)
WHITE = (255, 255, 255)
BLACK = (20, 20, 25)

# ------------------------------------------- vector serif font (Times-like)
# Every glyph is a set of strokes (polylines) in a 12 x 14 unit grid:
# cap top y=0, baseline y=10, x-height top y=3, descender bottom y=13.
# Each entry is (advance, [stroke, ...]); a stroke is a list of (x, y)
# points, curves approximated by short segments. Serif feet are short
# horizontal strokes at the ends of vertical stems. The renderer draws
# each stroke thick (vertical/diagonal full weight, horizontal thinner,
# like a Times face) through a supersampled mask, so edges are smooth.
FONTV = {
    "A": (11, [[(1, 10), (5.5, 0)], [(5.5, 0), (10, 10)],
              [(3.2, 6.5), (7.8, 6.5)], [(0, 10), (2, 10)],
              [(9, 10), (11, 10)]]),
    "B": (10, [[(1.5, 0), (1.5, 10)], [(0, 0), (3, 0)], [(0, 10), (3, 10)],
              [(1.5, 1), (5, 0.5), (8, 1.5), (8.5, 3.5), (5, 5), (1.5, 5)],
              [(1.5, 5), (5.5, 5), (8.5, 6), (8.5, 9), (5, 10), (1.5, 10)]]),
    "C": (10, [[(9, 1.5), (7, 0.5), (4, 0.5), (1.5, 2), (1, 5), (1.5, 8),
              (4, 9.5), (7, 9.5), (9, 8.5)]]),
    "D": (10, [[(1.5, 0), (1.5, 10)], [(0, 0), (3, 0)], [(0, 10), (3, 10)],
              [(1.5, 0.5), (5, 0), (8.5, 1.5), (9.5, 5), (8.5, 8.5),
               (5, 10), (1.5, 10)]]),
    "E": (10, [[(1.5, 0), (1.5, 10)], [(0, 0), (3, 0)], [(0, 10), (3, 10)],
              [(1.5, 0.5), (9, 0.5)], [(1.5, 5), (7, 5)],
              [(1.5, 9.5), (9, 9.5)]]),
    "F": (9, [[(1.5, 0), (1.5, 10)], [(0, 0), (3, 0)], [(0, 10), (3, 10)],
              [(1.5, 0.5), (9, 0.5)], [(1.5, 5), (7, 5)]]),
    "G": (10, [[(9, 1.5), (7, 0.5), (4, 0.5), (1.5, 2), (1, 5), (1.5, 8),
              (4, 9.5), (7, 9.5), (9, 8.5)], [(6, 5.5), (9.5, 5.5)],
              [(9.5, 5.5), (9.5, 8)]]),
    "H": (11, [[(1.5, 0), (1.5, 10)], [(0, 0), (3, 0)], [(0, 10), (3, 10)],
              [(9.5, 0), (9.5, 10)], [(8, 0), (11, 0)], [(8, 10), (11, 10)],
              [(1.5, 5), (9.5, 5)]]),
    "I": (8, [[(4, 0), (4, 10)], [(2, 0), (6, 0)], [(2, 10), (6, 10)]]),
    "Í": (8, [[(6.5, 0), (8, 1.5)], [(4, 2), (4, 10)], [(2, 10), (6, 10)]]),
    "J": (9, [[(3, 0), (9, 0)], [(7, 0), (7, 9)],
              [(7, 9), (5, 10.5), (3, 10.5), (1.5, 9), (1.5, 7)]]),
    "K": (10, [[(1.5, 0), (1.5, 10)], [(0, 0), (3, 0)], [(0, 10), (3, 10)],
              [(5.5, 5), (9.5, 0.5)], [(5, 5.5), (9.5, 9.5)],
              [(8, 10), (10.5, 10)]]),
    "L": (9, [[(1.5, 0), (1.5, 10)], [(0, 0), (3, 0)], [(0, 10), (3, 10)],
              [(1.5, 9.5), (9.5, 9.5)]]),
    "M": (12, [[(1, 0), (1, 10)], [(0, 0), (2, 0)], [(0, 10), (2, 10)],
              [(11, 0), (11, 10)], [(10, 0), (12, 0)], [(10, 10), (12, 10)],
              [(1, 0), (6, 6)], [(6, 6), (11, 0)]]),
    "N": (11, [[(1.5, 0), (1.5, 10)], [(0, 0), (3, 0)], [(0, 10), (3, 10)],
              [(9.5, 0), (9.5, 10)], [(8, 0), (11, 0)], [(8, 10), (11, 10)],
              [(1.5, 0), (9.5, 10)]]),
    "O": (11, [[(5.5, 0.5), (8.5, 1.5), (10, 4), (10, 6), (8.5, 8.5),
              (5.5, 9.5), (2.5, 8.5), (1, 6), (1, 4), (2.5, 1.5),
              (5.5, 0.5)]]),
    "P": (10, [[(1.5, 0), (1.5, 10)], [(0, 0), (3, 0)], [(0, 10), (3, 10)],
              [(1.5, 1), (5, 0.5), (8, 1.5), (8.5, 3.5), (5, 5), (1.5, 5)]]),
    "Q": (11, [[(5.5, 0.5), (8.5, 1.5), (10, 4), (10, 6), (8.5, 8.5),
              (5.5, 9.5), (2.5, 8.5), (1, 6), (1, 4), (2.5, 1.5),
              (5.5, 0.5)], [(7, 8), (10.5, 11.5)]]),
    "R": (10, [[(1.5, 0), (1.5, 10)], [(0, 0), (3, 0)], [(0, 10), (3, 10)],
              [(1.5, 1), (5, 0.5), (8, 1.5), (8.5, 3.5), (5, 5), (1.5, 5)],
              [(5.5, 5), (9.5, 10)], [(8, 10), (10.5, 10)]]),
    "S": (10, [[(9, 1.5), (7, 0.5), (4, 0.5), (2, 2), (1.5, 4), (3, 5.5),
              (7, 6), (9.5, 7.5), (9, 9), (7, 9.5), (4, 9.5), (2, 8.5)]]),
    "T": (11, [[(1, 0.5), (10, 0.5)], [(5.5, 0.5), (5.5, 10)],
              [(4, 10), (7, 10)]]),
    "U": (11, [[(1.5, 0), (1.5, 8)], [(0, 0), (3, 0)], [(9.5, 0), (9.5, 8)],
              [(8, 0), (11, 0)],
              [(1.5, 8), (3, 9.5), (5.5, 10), (8, 9.5), (9.5, 8)]]),
    "V": (11, [[(1, 0), (5.5, 10)], [(10, 0), (5.5, 10)], [(0.5, 0), (2.5, 0)],
              [(8.5, 0), (10.5, 0)]]),
    "W": (12, [[(0.5, 0), (3, 10)], [(3, 10), (6, 3.5)], [(6, 3.5), (9, 10)],
              [(9, 10), (11.5, 0)]]),
    "X": (10, [[(1, 0), (10, 10)], [(10, 0), (1, 10)]]),
    "Y": (11, [[(1, 0), (5.5, 5.5)], [(10, 0), (5.5, 5.5)],
              [(5.5, 5.5), (5.5, 10)], [(4, 10), (7, 10)]]),
    "Z": (10, [[(1, 0.5), (10, 0.5)], [(10, 0.5), (1, 9.5)],
              [(1, 9.5), (10, 9.5)]]),
    "a": (10, [[(8.5, 3), (8.5, 10)], [(7, 10), (10, 10)],
              [(8.5, 3), (7, 3), (5.5, 3.5)],
              [(8.5, 4), (6, 3.5), (3.5, 4), (2, 5.5), (2, 7.5), (3.5, 9),
               (6, 9.5), (8.5, 9)]]),
    "b": (10, [[(1.5, 0), (1.5, 10)], [(0, 10), (3, 10)],
              [(1.5, 4), (4, 3.5), (7, 4), (8, 6), (7, 8.5), (4, 9.5),
               (1.5, 9)]]),
    "c": (9, [[(8.5, 4), (6, 3.5), (3, 4.5), (1.5, 6.5), (2, 8.5),
              (4.5, 9.5), (7, 9), (8.5, 7.5)]]),
    "d": (10, [[(1.5, 4), (4, 3.5), (7, 4), (8, 6), (7, 8.5), (4, 9.5),
              (1.5, 9)], [(9, 0), (9, 10)], [(7.5, 10), (10.5, 10)]]),
    "e": (9, [[(8, 7), (6, 9), (3.5, 9.5), (1.5, 8), (1, 6), (2.5, 4),
              (5, 3.5), (7.5, 4.5), (8, 6.5)], [(1, 6.5), (8, 6.5)]]),
    "f": (7, [[(6.5, 0.5), (4.5, 0), (3, 1.5), (3, 10)], [(2, 5), (7, 5)]]),
    "g": (10, [[(8.5, 3), (8.5, 11)],
              [(8.5, 3), (7, 3), (5.5, 3.5)],
              [(8.5, 4), (6, 3.5), (3.5, 4), (2, 5.5), (2, 7.5), (3.5, 9),
               (6, 9.5), (8.5, 9)],
              [(8.5, 11), (6, 13), (3.5, 13), (2, 11.5), (3, 10), (5, 9.5)]]),
    "h": (10, [[(1.5, 0), (1.5, 10)], [(0, 10), (3, 10)],
              [(1.5, 4), (4, 3.5), (7, 4), (8, 6), (8, 10)],
              [(6.5, 10), (9.5, 10)]]),
    "i": (7, [[(4.5, 1.2), (5.5, 1.2)], [(5, 3.5), (5, 10)],
              [(3.5, 10), (6.5, 10)]]),
    "j": (7, [[(5.5, 1.2), (6.5, 1.2)], [(6, 3.5), (6, 11.5)],
              [(6, 11.5), (4.5, 13), (2.5, 12.5)]]),
    "k": (9, [[(1.5, 0), (1.5, 10)], [(0, 10), (3, 10)],
              [(1.5, 6.5), (8.5, 3.5)], [(5, 6.5), (9, 10)],
              [(7.5, 10), (10, 10)]]),
    "l": (7, [[(4, 0), (4, 10)], [(2.5, 0), (5.5, 0)], [(2.5, 10), (5.5, 10)]]),
    "m": (12, [[(1.5, 3.5), (1.5, 10)], [(0, 10), (3, 10)],
              [(1.5, 4), (4, 3.5), (6, 4.5), (6, 10)],
              [(6, 4), (8.5, 3.5), (10, 4.5), (10, 10)],
              [(8.5, 10), (11.5, 10)]]),
    "n": (10, [[(1.5, 3.5), (1.5, 10)], [(0, 10), (3, 10)],
              [(1.5, 4), (4, 3.5), (7, 4), (8, 6), (8, 10)],
              [(6.5, 10), (9.5, 10)]]),
    "o": (9, [[(5, 3.5), (7.5, 4), (8.5, 6), (7.5, 8.5), (5, 9.5),
              (2.5, 8.5), (1.5, 6), (2.5, 4), (5, 3.5)]]),
    "p": (10, [[(1.5, 3.5), (1.5, 13)], [(0, 13), (3, 13)],
              [(1.5, 4), (4, 3.5), (7, 4), (8, 6), (7, 8.5), (4, 9.5),
               (1.5, 9)]]),
    "q": (10, [[(1.5, 4), (4, 3.5), (7, 4), (8, 6), (7, 8.5), (4, 9.5),
              (1.5, 9)], [(9, 3.5), (9, 13)], [(7.5, 13), (10.5, 13)]]),
    "r": (7, [[(1.5, 3.5), (1.5, 10)], [(0, 10), (3, 10)],
              [(1.5, 4), (4, 3.5), (6, 4), (7, 5.5)]]),
    "s": (9, [[(8, 4.5), (6, 3.5), (3.5, 3.5), (2, 5), (1.5, 6.5),
              (3.5, 7.5), (6, 8), (7.5, 9), (6.5, 9.5), (4, 9.5), (2, 9)]]),
    "t": (8, [[(5.5, 0.5), (5.5, 11.5)], [(5.5, 11.5), (6.5, 12.5), (8, 12)],
              [(2.5, 5), (8, 5)]]),
    "u": (10, [[(1.5, 3.5), (1.5, 8)], [(8.5, 3.5), (8.5, 10)],
              [(7, 10), (10, 10)],
              [(1.5, 8), (3, 9.5), (5.5, 10), (8, 9.5), (8.5, 8)]]),
    "v": (10, [[(1, 3.5), (5, 10)], [(9, 3.5), (5, 10)], [(0.5, 3.5), (2.5, 3.5)],
              [(7.5, 3.5), (9.5, 3.5)]]),
    "w": (11, [[(0.5, 3.5), (2.5, 10)], [(2.5, 10), (5.5, 5)],
              [(5.5, 5), (8, 10)], [(8, 10), (10.5, 3.5)]]),
    "x": (9, [[(1.5, 3.5), (8.5, 10)], [(8.5, 3.5), (1.5, 10)]]),
    "y": (9, [[(1, 3.5), (5, 9.5)], [(9, 3.5), (5, 9.5)], [(5, 9.5), (4.5, 13)]]),
    "z": (9, [[(1, 3.5), (9, 3.5)], [(9, 3.5), (1, 9.5)], [(1, 9.5), (9, 9.5)]]),
    "0": (10, [[(5, 0.5), (7.5, 1), (9, 3.5), (9, 6.5), (7.5, 9), (5, 9.5),
              (2.5, 9), (1, 6.5), (1, 3.5), (2.5, 1), (5, 0.5)]]),
    "1": (9, [[(3, 2), (5.5, 0), (5.5, 10)], [(3.5, 10), (7.5, 10)]]),
    "2": (10, [[(2, 2), (4, 0.5), (7, 0.5), (8.5, 2), (8, 4), (5, 7),
              (2, 9.5), (9, 9.5)]]),
    "3": (10, [[(2, 1), (4, 0.5), (7, 0.5), (8.5, 2), (7, 4.5), (5, 5),
              (7, 5.5), (8.5, 7), (8, 9), (6, 10), (3, 10), (1.5, 9)]]),
    "4": (10, [[(7.5, 0), (3, 7), (8.5, 7)], [(7.5, 0), (7.5, 10)],
              [(6, 10), (9, 10)]]),
    "5": (10, [[(1.5, 0.5), (8, 0.5)], [(1.5, 0.5), (1.5, 5)],
              [(1.5, 5), (5, 5), (8, 6), (8, 8.5), (6, 10), (3, 10),
               (1.5, 9)]]),
    "6": (10, [[(8, 1), (5.5, 0.5), (3, 1.5), (1.5, 4.5), (1.5, 7), (3, 9.5),
              (6, 10), (8, 8.5), (8.5, 6.5), (7, 5), (4.5, 5), (2.5, 6)]]),
    "7": (10, [[(1, 0.5), (9.5, 0.5)], [(9.5, 0.5), (4, 10)]]),
    "8": (10, [[(5, 0.5), (7.5, 1), (8.5, 2.5), (7, 4.5), (5, 5), (3, 4.5),
              (1.5, 2.5), (2.5, 1), (5, 0.5)],
              [(5, 5), (7.5, 5.5), (9, 7), (8, 9), (5.5, 10), (3, 9.5),
               (1, 7.5), (2, 5.5), (5, 5)]]),
    "9": (10, [[(5, 1), (7.5, 1.5), (8.5, 3.5), (7, 5.5), (5, 6), (3, 5.5),
              (1.5, 3.5), (2.5, 1.5), (5, 1)], [(8.5, 4), (8, 8), (6.5, 10)]]),
    " ": (5, []),
    ".": (5, [[(4.5, 9), (5.5, 8.5), (6.5, 9), (5.5, 9.5), (4.5, 9)]]),
    ",": (5, [[(4.5, 9), (5.5, 8.5), (6.5, 9), (5.5, 9.5), (4.5, 9)],
              [(5.5, 9.5), (5, 11), (3.5, 11.5)]]),
    ";": (5, [[(4.5, 4), (5.5, 3.5), (6.5, 4), (5.5, 4.5), (4.5, 4)],
              [(4.5, 9), (5.5, 8.5), (6.5, 9), (5.5, 9.5), (4.5, 9)],
              [(5.5, 9.5), (5, 11), (3.5, 11.5)]]),
    ":": (5, [[(4.5, 4), (5.5, 3.5), (6.5, 4), (5.5, 4.5), (4.5, 4)],
              [(4.5, 9), (5.5, 8.5), (6.5, 9), (5.5, 9.5), (4.5, 9)]]),
    "!": (6, [[(5, 0), (5, 7.5)],
              [(4.5, 9), (5.5, 8.5), (6.5, 9), (5.5, 9.5), (4.5, 9)]]),
    "?": (9, [[(2, 2), (4, 0.5), (7, 0.5), (8.5, 2), (7.5, 4), (5.5, 5.5),
              (5.5, 7)],
              [(4.5, 9), (5.5, 8.5), (6.5, 9), (5.5, 9.5), (4.5, 9)]]),
    "'": (5, [[(5, 0), (6.5, 1.5), (5.5, 3)]]),
    '"': (8, [[(3, 0), (4.5, 1.5), (3.5, 3)], [(7, 0), (8.5, 1.5), (7.5, 3)]]),
    "-": (9, [[(1, 6), (9, 6)]]),
    "–": (10, [[(1, 6), (9, 6)]]),
    "—": (11, [[(0.5, 6), (10.5, 6)]]),
    "/": (8, [[(8, 0), (3, 10)]]),
    "(": (7, [[(7, 0), (4, 2.5), (3, 5), (4, 7.5), (7, 10)]]),
    ")": (7, [[(1, 0), (4, 2.5), (5, 5), (4, 7.5), (1, 10)]]),
    "%": (11, [[(3, 0.5), (5, 1.5), (5, 3.5), (3, 4.5), (1.5, 3), (1.5, 1.5),
              (3, 0.5)],
              [(8, 5.5), (10, 6.5), (10, 8.5), (8, 9.5), (6.5, 8), (6.5, 6.5),
               (8, 5.5)],
              [(9.5, 0), (1, 10)]]),
    "+": (10, [[(5, 3), (5, 9)], [(2, 6), (8, 6)]]),
    "=": (10, [[(1.5, 4), (8.5, 4)], [(1.5, 7), (8.5, 7)]]),
    "$": (10, [[(8, 2), (6, 0.5), (3.5, 0.5), (2, 2), (1.5, 3.5), (3, 5),
              (6.5, 5.5), (8, 6.5), (7.5, 8.5), (5.5, 9.5), (3, 9.5),
              (1.5, 8.5)], [(5, 0), (5, 10.5)]]),
    "<": (9, [[(8, 0.5), (2, 5), (8, 9.5)]]),
    ">": (9, [[(1, 0.5), (7, 5), (1, 9.5)]]),
    "~": (10, [[(1, 6), (3, 4.5), (5, 5.5), (7, 7), (9, 6)]]),
    "_": (10, [[(1, 11), (9, 11)]]),
    "[": (7, [[(6, 0), (3, 0), (3, 10), (6, 10)]]),
    "]": (7, [[(1, 0), (4, 0), (4, 10), (1, 10)]]),
    "#": (10, [[(4, 0), (3, 10)], [(7, 0), (6, 10)], [(1, 3.5), (9, 3.5)],
              [(1, 6.5), (9, 6.5)]]),
    "&": (10, [[(8, 2.5), (6, 1), (3, 1), (1.5, 2.5), (2, 4.5), (5, 6),
              (8, 7.5), (8.5, 9), (7, 10), (5, 9.5), (3, 8.5), (2, 7),
              (1.5, 5)]]),
    "*": (9, [[(5, 0), (5, 10)], [(1, 3), (9, 7)], [(9, 3), (1, 7)]]),
    "•": (7, [[(5, 5.5), (6.5, 6.5), (5, 7.5), (3.5, 6.5), (5, 5.5)]]),
    "★": (10, [[(5, 3), (6, 5.5), (8.5, 5.5), (6.5, 7), (7.5, 9.5), (5, 8),
              (2.5, 9.5), (3.5, 7), (1.5, 5.5), (4, 5.5), (5, 3)]]),
    "£": (9, [[(8, 1.5), (6, 0.5), (3.5, 0.5), (2, 2), (2, 4.5)],
              [(1, 5.5), (7.5, 5.5)], [(1.5, 8), (8, 8)], [(2, 4.5), (2, 8)]]),
    "€": (10, [[(9, 1.5), (7, 0.5), (4, 0.5), (1.5, 2), (1, 5), (1.5, 8),
              (4, 9.5), (7, 9.5), (9, 8.5)], [(0.5, 4), (5.5, 4)],
              [(0.5, 6), (5.5, 6)]]),
    "₹": (10, [[(1.5, 0.5), (8.5, 0.5)], [(1.5, 0.5), (1.5, 5)],
              [(1.5, 1), (5, 0.5), (8, 1.5), (8, 3), (5, 4.5), (1.5, 4.5)],
              [(1.5, 6), (8, 6)], [(5, 5), (8.5, 10)]]),
    "é": (9, [[(8, 7), (6, 9), (3.5, 9.5), (1.5, 8), (1, 6), (2.5, 4),
              (5, 3.5), (7.5, 4.5), (8, 6.5)], [(1, 6.5), (8, 6.5)],
              [(6.5, 0), (8, 2)]]),
    "í": (7, [[(6, 0), (7.5, 2)], [(5, 3.5), (5, 10)], [(3.5, 10), (6.5, 10)]]),
}

# Hollow box for any character the font does not define.
FALLBACK_V = (11, [[(1, 0), (10, 0), (10, 10), (1, 10), (1, 0)]])


# ---------------------------------------------------------------- canvas
class Canvas(object):
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.buf = bytearray(w * h * 3)
        self.rect(0, 0, w, h, bg)

    def px(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i] = c[0]
            self.buf[i + 1] = c[1]
            self.buf[i + 2] = c[2]

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            return (self.buf[i], self.buf[i + 1], self.buf[i + 2])
        return (0, 0, 0)

    def blend(self, x, y, c, a):
        # Paint colour c over the current pixel with coverage a (0..255).
        if a <= 0 or not (0 <= x < self.w and 0 <= y < self.h):
            return
        if a >= 255:
            self.px(x, y, c)
            return
        i = (y * self.w + x) * 3
        inv = 255 - a
        self.buf[i] = (c[0] * a + self.buf[i] * inv) // 255
        self.buf[i + 1] = (c[1] * a + self.buf[i + 1] * inv) // 255
        self.buf[i + 2] = (c[2] * a + self.buf[i + 2] * inv) // 255

    def rect(self, x, y, w, h, c):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.buf[i] = c[0]
                self.buf[i + 1] = c[1]
                self.buf[i + 2] = c[2]

    def hline(self, x, y, w, c):
        self.rect(x, y, w, 1, c)

    def vline(self, x, y, h, c):
        self.rect(x, y, 1, h, c)

    def line(self, x0, y0, x1, y1, c, thick=1):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            if thick <= 1:
                self.px(x0, y0, c)
            else:
                self.rect(x0 - thick // 2, y0 - thick // 2, thick, thick, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, c, fill=True):
        if fill:
            for dy in range(-r, r + 1):
                dx = int(math.sqrt(max(0, r * r - dy * dy)))
                self.hline(cx - dx, cy + dy, 2 * dx + 1, c)
        else:
            x = 0
            y = r
            d = 3 - 2 * r
            while y >= x:
                for sx, sy in ((x, y), (y, x), (-x, y), (-y, x),
                               (x, -y), (y, -x), (-x, -y), (-y, -x)):
                    self.px(cx + sx, cy + sy, c)
                x += 1
                if d > 0:
                    y -= 1
                    d = d + 4 * (x - y) + 10
                else:
                    d = d + 4 * x + 6

    def arc(self, cx, cy, r, a0, a1, c, thick=2):
        steps = max(8, int(r * 2))
        prev = None
        for k in range(steps + 1):
            a = a0 + (a1 - a0) * k / steps
            x = int(cx + r * math.cos(a))
            y = int(cy + r * math.sin(a))
            if prev is not None:
                self.line(prev[0], prev[1], x, y, c, thick)
            prev = (x, y)

    def pill(self, x, y, w, h, c):
        r = h // 2
        self.rect(x + r, y, w - 2 * r, h, c)
        self.circle(x + r, y + r, r, c)
        self.circle(x + w - r - 1, y + r, r, c)

    def poly(self, pts, c):
        # Filled polygon via scanline fill.
        if not pts:
            return
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                self.hline(int(xs[k]), y, max(1, int(xs[k + 1]) - int(xs[k])), c)


# ------------------------------------------------------------------- text
# Text is the embedded vector serif font above. Each glyph is rendered
# once per (character, scale, bold) into a supersampled coverage mask
# and cached; drawing a string blends those masks onto the canvas.
# Vertical/diagonal strokes are full weight, horizontal strokes thinner
# (a Times-style contrast), fading to near-uniform at small sizes so
# hairlines stay visible. Default scale 0.6 is the small print; display
# text passes larger scales. One font serves every size.
SS = 3
CELL_H = 14  # units: cap top 0, baseline 10, descender bottom 13


def _thin(scale):
    return 0.7 + 0.3 * max(0.0, min(1.0, (1.5 - scale) / 1.5))


def _stamp(mask, mw, mh, cx, cy, offs):
    for dx, dy in offs:
        x = cx + dx
        y = cy + dy
        if 0 <= x < mw and 0 <= y < mh:
            mask[y * mw + x] = 255


def _stroke(mask, mw, mh, x0, y0, x1, y1, width):
    dx = x1 - x0
    dy = y1 - y0
    length = math.hypot(dx, dy)
    if length <= 0:
        return
    step = max(1.0, width / 4.0)
    steps = int(length / step) + 1
    r = width / 2.0
    ri = int(math.ceil(r))
    offs = []
    for ddy in range(-ri, ri + 1):
        ddx = int(math.sqrt(max(0.0, r * r - ddy * ddy)))
        for ddx2 in range(-ddx, ddx + 1):
            offs.append((ddx2, ddy))
    for k in range(steps + 1):
        t = k / steps
        _stamp(mask, mw, mh, int(round(x0 + dx * t)),
               int(round(y0 + dy * t)), offs)


_COV_CACHE = {}


def _vec_cov(ch, scale, bold):
    key = (ch, round(scale, 2), bold)
    got = _COV_CACHE.get(key)
    if got is not None:
        return got
    adv, strokes = FONTV.get(ch, FALLBACK_V)
    w = max(1, int(round(adv * scale)))
    h = max(1, int(round(CELL_H * scale)))
    mw, mh = (w + 1) * SS, (h + 1) * SS
    mask = bytearray(mw * mh)
    base = (2.0 if bold else 1.6) * scale * SS
    thin = _thin(scale)
    for poly in strokes:
        for a, b in zip(poly, poly[1:]):
            width = base
            if abs(b[0] - a[0]) >= 2 * abs(b[1] - a[1]):
                width = base * thin
            _stroke(mask, mw, mh, a[0] * scale * SS, a[1] * scale * SS,
                    b[0] * scale * SS, b[1] * scale * SS, width)
    cov = bytearray(w * h)
    area = SS * SS
    for oy in range(h):
        for ox in range(w):
            total = 0
            for sy in range(SS):
                base_i = (oy * SS + sy) * mw + ox * SS
                for sx in range(SS):
                    total += mask[base_i + sx]
            cov[oy * w + ox] = total // area
    out = (w, h, cov)
    _COV_CACHE[key] = out
    return out


def text_w(s, scale=0.6, spacing=1):
    if not s:
        return 0
    total = 0.0
    for ch in s:
        total += FONTV.get(ch, FALLBACK_V)[0] * scale
    return int(round(total + spacing * (len(s) - 1)))


def draw_text(cv, x, y, s, scale=0.6, c=INK, bold=False, spacing=1):
    if not s:
        return x
    cx = 0.0
    for ch in s:
        w, h, cov = _vec_cov(ch, scale, bold)
        for oy in range(h):
            row = oy * w
            for ox in range(w):
                a = cov[row + ox]
                if a:
                    cv.blend(int(x + cx) + ox, y + oy, c, a)
        cx += FONTV.get(ch, FALLBACK_V)[0] * scale + spacing
    return x + text_w(s, scale, spacing)


def draw_glyph(cv, x, y, ch, scale, c):
    draw_text(cv, x, y, ch, scale, c, False, 1)


def draw_text_c(cv, cx, y, s, scale=0.6, c=INK, bold=False, spacing=1):
    draw_text(cv, cx - text_w(s, scale, spacing) // 2, y, s, scale,
              c, bold, spacing)


def wrap(s, maxw, scale=0.6, spacing=1):
    words = s.split(" ")
    lines = []
    cur = ""
    for wd in words:
        trial = wd if not cur else cur + " " + wd
        if text_w(trial, scale, spacing) <= maxw or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


# ------------------------------------------------------- PNG file writer
# A PNG file is a signature followed by length-tagged chunks, each with
# a CRC32 over its tag and payload. Pixels go in as filter-0 scanlines
# (one leading zero byte per row) compressed with zlib.
def _png_sig():
    # PNG magic: 137 'P' 'N' 'G' CR LF 26 LF.
    return bytes([137, 80, 78, 71, 13, 10, 26, 10])


def _chunk(tag, data):
    body = tag + data
    return (struct.pack(">I", len(data)) + body +
            struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF))


def _png_bytes(cv):
    rows = []
    stride = cv.w * 3
    for r in range(cv.h):
        rows.append(b"\x00" + bytes(cv.buf[r * stride:(r + 1) * stride]))
    packed = b"".join(rows)
    # IHDR payload: width, height (4 bytes each), then bit depth 8,
    # colour type 2 (truecolour RGB), compression 0, filter 0, interlace 0.
    ihdr = struct.pack(">II", cv.w, cv.h) + bytes([8, 2, 0, 0, 0])
    return (_png_sig() + _chunk(b"IHDR", ihdr) +
            _chunk(b"IDAT", zlib.compress(packed, 6)) +
            _chunk(b"IEND", b""))


def write_png(path, cv):
    with open(path, "wb") as f:
        f.write(_png_bytes(cv))

# ------------------------------------------------------------- mini flags
def uk_flag(cv, x, y, w, h):
    cv.rect(x, y, w, h, (0, 36, 125))
    cv.line(x, y, x + w - 1, y + h - 1, WHITE, 3)
    cv.line(x + w - 1, y, x, y + h - 1, WHITE, 3)
    cv.rect(x + w // 2 - 4, y, 8, h, WHITE)
    cv.rect(x, y + h // 2 - 4, w, 8, WHITE)
    cv.rect(x + w // 2 - 2, y, 4, h, RED)
    cv.rect(x, y + h // 2 - 2, w, 4, RED)


def eu_flag(cv, x, y, w, h):
    cv.rect(x, y, w, h, (0, 51, 153))
    cx, cy = x + w // 2, y + h // 2
    for k in range(12):
        a = 2 * math.pi * k / 12 - math.pi / 2
        cv.circle(int(cx + 9 * math.cos(a)), int(cy + 6 * math.sin(a)), 1, YELLOW)


def id_flag(cv, x, y, w, h):
    cv.rect(x, y, w, h, GREY)
    cv.rect(x + 1, y + 1, w - 2, h // 2 - 1, RED)
    cv.rect(x + 1, y + h // 2, w - 2, h - h // 2 - 1, WHITE)


# ------------------------------------------------------------ story art
def art_nasdaq(cv, x, y):
    cv.rect(x, y, 116, 84, DARKBOX)
    draw_text(cv, x + 6, y + 5, "NASDAQ", 1, WHITE, bold=True)
    tops = [18, 24, 22, 30, 36, 34, 42, 48]
    for i, t in enumerate(tops):
        cx = x + 12 + i * 12
        col = (60, 180, 90) if i % 3 == 0 else (220, 70, 70)
        cv.rect(cx, y + t, 6, 14, col)
        cv.vline(cx + 3, y + t - 4, 22, col)
    cv.line(x + 8, y + 20, x + 108, y + 56, YELLOW, 2)
    draw_text(cv, x + 6, y + 64, "-5.28%", 2, WHITE, bold=True)


def art_peru(cv, x, y):
    cv.rect(x, y, 116, 84, PERU_BG)
    pts = [(x + 6, y + 42), (x + 20, y + 42), (x + 26, y + 30), (x + 32, y + 54),
           (x + 38, y + 42), (x + 50, y + 42), (x + 56, y + 22), (x + 62, y + 60),
           (x + 68, y + 42), (x + 82, y + 42), (x + 88, y + 34), (x + 94, y + 50),
           (x + 100, y + 42), (x + 110, y + 42)]
    for a, b in zip(pts, pts[1:]):
        cv.line(a[0], a[1], b[0], b[1], YELLOW, 2)
    cv.circle(x + 92, y + 16, 13, RED)
    draw_text_c(cv, x + 92, y + 12, "6.8", 0.8, WHITE, bold=True)
    draw_text(cv, x + 6, y + 68, "PERU \u2022 JUN\u00cdN", 1, WHITE, bold=True)


def art_ukeu(cv, x, y):
    cv.rect(x, y, 116, 84, PAPER)
    uk_flag(cv, x + 6, y + 5, 50, 28)
    eu_flag(cv, x + 60, y + 5, 50, 28)
    draw_text_c(cv, x + 58, y + 37, "100,000", 2, NAVY, bold=True, spacing=0)
    draw_text_c(cv, x + 58, y + 60, "youth visas a year", 0.6, NAVY)
    draw_text_c(cv, x + 58, y + 71, "UK-EU DEAL", 1, GOLD, bold=True)


def art_ideu(cv, x, y):
    cv.rect(x, y, 116, 84, PAPER)
    id_flag(cv, x + 6, y + 5, 50, 28)
    eu_flag(cv, x + 60, y + 5, 50, 28)
    draw_text_c(cv, x + 58, y + 37, "98.5%", 2, (0, 120, 80), bold=True,
                spacing=0)
    draw_text_c(cv, x + 58, y + 60, "of tariff lines", 0.7, INK)
    draw_text_c(cv, x + 58, y + 71, "IEU-CEPA", 1, TEAL, bold=True)


def art_cop(cv, x, y):
    cv.rect(x, y, 116, 84, (124, 169, 124))
    cv.circle(x + 58, y + 20, 14, WHITE)
    cv.circle(x + 58, y + 20, 14, NAVY, fill=False)
    cv.line(x + 58, y + 20, x + 58, y + 9, NAVY, 2)
    cv.line(x + 58, y + 20, x + 67, y + 24, NAVY, 2)
    draw_text_c(cv, x + 58, y + 40, "OVERTIME", 1, WHITE, bold=True)
    draw_text_c(cv, x + 58, y + 58, "fossil fuels", 1, RED, bold=True)
    cv.hline(x + 32, y + 64, 52, RED)
    draw_text_c(cv, x + 58, y + 71, "ANTALYA \u2022 COP31", 0.8, WHITE)


def art_poland(cv, x, y):
    cv.rect(x, y, 116, 84, PAPER)
    draw_text(cv, x + 6, y + 5, "POLAND", 1, NAVY, bold=True)
    top = [(x + 22, y + 22), (x + 92, y + 16), (x + 106, y + 30),
           (x + 62, y + 44), (x + 18, y + 42)]
    bot = [(x + 18, y + 42), (x + 62, y + 44), (x + 106, y + 30),
           (x + 98, y + 56), (x + 66, y + 68), (x + 34, y + 60),
           (x + 12, y + 48)]
    cv.poly(top, WHITE)
    cv.poly(bot, (220, 60, 70))
    cv.line(x + 22, y + 22, x + 92, y + 16, GREY, 1)
    cv.line(x + 92, y + 16, x + 106, y + 30, GREY, 1)
    cv.line(x + 106, y + 30, x + 98, y + 56, GREY, 1)
    cv.line(x + 98, y + 56, x + 66, y + 68, GREY, 1)
    cv.line(x + 66, y + 68, x + 34, y + 60, GREY, 1)
    cv.line(x + 34, y + 60, x + 12, y + 48, GREY, 1)
    cv.line(x + 12, y + 48, x + 22, y + 22, GREY, 1)
    for dx, dy in ((30, 34), (62, 30), (82, 48)):
        cv.circle(x + dx, y + dy, 3, YELLOW)
        cv.circle(x + dx, y + dy, 3, NAVY, fill=False)
    draw_text(cv, x + 6, y + 72, "3 impact sites", 0.65, NAVY, bold=True)


def art_cyclone(cv, x, y):
    cv.rect(x, y, 116, 84, STEEL)
    cx, cy = x + 58, y + 28
    cv.arc(cx, cy, 24, 0.6, 5.6, WHITE, 3)
    cv.arc(cx, cy, 16, 1.4, 6.4, WHITE, 3)
    cv.arc(cx, cy, 8, 2.2, 6.8, WHITE, 3)
    draw_text_c(cv, x + 58, y + 54, "~300,000", 1, WHITE, bold=True)
    draw_text_c(cv, x + 58, y + 72, "evacuated \u2022 Odisha", 0.6, WHITE)


def art_rahul(cv, x, y):
    cv.rect(x, y, 116, 84, GREEN)
    draw_text(cv, x + 8, y + 8, "13th", 1, WHITE, bold=True)
    draw_glyph(cv, x + 46, y + 7, "\u2605", 1, YELLOW)
    draw_text(cv, x + 58, y + 4, "100", 2, YELLOW, bold=True)
    cv.line(x + 34, y + 62, x + 48, y + 26, (210, 180, 130), 8)
    for dx in (66, 72, 78):
        cv.vline(x + dx, y + 42, 20, YELLOW)
    cv.circle(x + 96, y + 58, 5, RED)
    draw_text(cv, x + 6, y + 70, "Wellington", 1, WHITE, bold=True)


def art_riyadh(cv, x, y):
    cv.rect(x, y, 116, 84, (40, 40, 70))
    for bx, bh in ((6, 30), (20, 44), (36, 26), (52, 52), (70, 34), (86, 46), (100, 28)):
        cv.rect(x + bx, y + 70 - bh, 12, bh, (64, 64, 108))
        for wy in range(y + 70 - bh + 5, y + 66, 8):
            cv.px(x + bx + 3, wy, YELLOW)
            cv.px(x + bx + 8, wy, YELLOW)
    cv.poly([(x + 52, y + 18), (x + 58, y + 6), (x + 64, y + 18)], (90, 90, 140))
    cv.arc(x + 30, y + 16, 10, 3.4, 6.0, WHITE, 2)
    cv.arc(x + 82, y + 14, 10, 3.4, 6.0, WHITE, 2)
    draw_text(cv, x + 4, y + 72, "3 missiles intercepted", 0.55, WHITE, spacing=-1)


def art_gaza(cv, x, y):
    cv.rect(x, y, 116, 84, (245, 240, 225))
    mp = [(x + 20, y + 6), (x + 92, y + 4), (x + 102, y + 26),
          (x + 76, y + 50), (x + 42, y + 56), (x + 14, y + 34)]
    cv.poly(mp, (214, 192, 160))
    for i in range(len(mp)):
        a = mp[i]
        b = mp[(i + 1) % len(mp)]
        cv.line(a[0], a[1], b[0], b[1], TAN, 1)
    for dx, dy in ((34, 16), (58, 12), (76, 24), (48, 32), (68, 40), (88, 34)):
        cv.circle(x + dx, y + dy, 3, RED)
    draw_text(cv, x + 6, y + 58, "6 killed", 1, RED, bold=True)
    draw_text(cv, x + 6, y + 74, "1,600+ since truce", 0.6, INK)


ART = {"nasdaq": art_nasdaq, "peru": art_peru, "ukeu": art_ukeu,
       "ideu": art_ideu, "cop": art_cop, "poland": art_poland,
       "cyclone": art_cyclone, "rahul": art_rahul, "riyadh": art_riyadh,
       "gaza": art_gaza}

# --------------------------------------------------------------- content
STORIES = [
    ("AMERICAS \u2022 MARKETS", BLUE,
     "Wall Street plunges as AI sell-off deepens",
     "S&P 500 -3.70% to 6,910.39, Nasdaq -5.28% to 22,617.73. Nvidia fell 14% amid an accounting probe; a seventh straight S&P loss.",
     "AP; Reuters; Fox Business", "nasdaq"),
    ("AMERICAS \u2022 DISASTER", BLUE,
     "Peru shaken by magnitude 6.8 earthquake",
     "A deep quake in Jun\u00edn sent Lima residents into the streets. No casualties or major damage reported yet; USGS put it at 6.7.",
     "Reuters; AP; GFZ", "peru"),
    ("EUROPE \u2022 TRADE", PURPLE,
     "UK and EU seal landmark post-Brexit package",
     "Food trade eased, carbon markets linked, youth scheme of 100,000 visas a year. Burnham claims \u00a317bn a year; a tuition-fee row clouds rollout.",
     "PA/LBC; Brussels Times; EU Gov", "ukeu"),
    ("ASIA-PACIFIC \u2022 TRADE", TEAL,
     "Indonesia and EU sign landmark trade deal",
     "Signed in Brussels today after a decade of talks; up to 98.5% of tariff lines liberalised, 90.4% of Indonesian lines zero tariffs at once; start targeted for early 2027.",
     "ANTARA; Reuters; EU Council", "ideu"),
    ("GLOBAL \u2022 CLIMATE", GREEN,
     "COP31 runs into overtime in Antalya",
     "Nearly 200 nations argued past the deadline over a draft with no mention of fossil fuels. The EU warned it risked becoming a 'fossil summit'.",
     "The Guardian; Reuters; Al Jazeera", "cop"),
    ("EUROPE \u2022 SECURITY", PURPLE,
     "Missiles land in Poland; NATO chief heads to Warsaw",
     "A Kh-101 hit near Nowy Lipowiec; Warsaw says a second object was probably a missile, a third most likely a drone. Tusk: a provocation. Rutte arrives Saturday.",
     "Reuters; AFP; Kyiv Independent", "poland"),
    ("ASIA-PACIFIC \u2022 WEATHER", TEAL,
     "Cyclone Akvan hits Odisha; ~300,000 evacuated",
     "Landfall near Gopalpur on Friday, then the storm weakened. Nearly 300,000 people had been moved to 2,523 relief camps; dozens of trains were cancelled.",
     "The Quint; India.com; Newsbytes", "cyclone"),
    ("SPORT \u2022 CRICKET", PINK,
     "Rahul completes his SENA set in Wellington",
     "Rahul's 13th Test hundred (207 balls), the first by an Indian opener in all SENA countries. India were 344/2 at tea, 24 behind.",
     "ESPNcricinfo; IANS; ANI", "rahul"),
    ("MIDDLE EAST \u2022 SECURITY", TAN,
     "Saudi defences down three Houthi missiles over Riyadh",
     "Three ballistic missiles aimed at the capital were destroyed early Saturday. No damage or casualties reported; the Houthis said they targeted the PIF tower.",
     "Reuters; AFP; Arab News", "riyadh"),
    ("MIDDLE EAST \u2022 GAZA", TAN,
     "Six killed in Gaza strikes despite the ceasefire",
     "Four died in an airstrike near Bureij, one in a drone strike in Deir al-Balah, one north of Nuseirat. AFP tally: 1,600+ killed since the truce.",
     "AFP; Al Jazeera", "gaza"),
]

STATS = [
    ("-5.28%", "NASDAQ FALLS", TICKER),
    ("6.8", "PERU QUAKE", TAN),
    ("100,000", "UK-EU YOUTH VISAS / YR", PURPLE),
    ("~300,000", "EVACUATED, AKVAN", TEAL),
    ("250 ft", "TRUMP ARCH BLOCKED", STEEL),
    ("100", "RAHUL'S CENTURY", PINK),
]

CHIPS = [
    ("AMERICAS 10", BLUE), ("EUROPE 5", PURPLE), ("MIDDLE EAST 6", TAN),
    ("ASIA-PACIFIC 3", TEAL), ("SPORT 3", PINK), ("GLOBAL 3", GREEN),
]

BRIEFS = [
    [("Trump vows a 'tremendous tax' on US firms building AI data centres abroad; no rate or legal basis given", "Reuters; AP"),
     ("Virginia child dies of measles \u2014 the first US measles death of 2026; 220 cases in the state", "ABC News; VDH"),
     ("Nasdaq 100 down 10.4%, worst since March 2020; S&P 500 down 8.6%, worst since April 2025; VIX 35.89", "CNBC; MarketWatch"),
     ("Poland to give the US access to missile debris; three impact sites under investigation", "AFP; Reuters"),
     ("Syria, Jordan, Iraq and Lebanon sign agriculture pact in Beirut to boost food security", "Arab News; Shafaq News"),
     ("Coalition strikes Houthi sites in Sanaa, Saada, Taiz and Hodeidah after the hit on Riyadh's PIF tower", "Arab News; Reuters"),
     ("Jaiswal's 85 and a 130-run opening stand set up India's reply to New Zealand's 368", "Sportskeeda; India.com")],
    [("Second judge blocks Trump's 250-ft arch: Brinkema's injunction open-ended, Chutkan's order runs to 3 Dec", "AP; Reuters"),
     ("Nvidia's worst week since Oct 2008, down 23%, after Huang's 12 Nov resignation and an accounting probe", "CNN; AP"),
     ("Arch plaintiffs include the Kennedy family and Vietnam veterans; planning panel approved it 8-4", "AP; Bloomberg"),
     ("UK\u2013EU carbon-market link shields \u00a36.5bn of British exports from the EU's carbon border tax", "PA/LBC"),
     ("Signal blocks screenshots by default to stop AI agents reading your chats", "Reuters; Engadget"),
     ("Israel says it completed a rare ground incursion in central Gaza a day before Friday's strikes", "AFP"),
     ("Foreign investors pour a record \u20b91.22 lakh crore into Indian shares in November", "The Hindu BusinessLine; Reuters")],
    [("Palisades Fire: Rinderknecht convicted on two arson counts at retrial; sentencing 17 Mar 2027", "AP; Los Angeles Times"),
     ("Anthropic IPO fizzles: priced at $83, peaked at $115.10 on Thursday, closed Friday near $88.91", "Telegraph; SBS"),
     ("Denmark expels Russia's defence attach\u00e9 over alleged plot to kill rapper Kyivstoner; two Danes held", "Al Jazeera; Copenhagen Post"),
     ("At COP31, Panama threatens to walk out as a dozen-plus countries demand a fossil-fuel transition", "Al Jazeera"),
     ("Iraqi forces enter Kataib Hezbollah's Jurf al-Sakhar stronghold under a deal; HQ opens Saturday", "Reuters; Al Jazeera"),
     ("Antonelli fastest in Las Vegas qualifying (1:33.893) but a grid penalty hands pole to Verstappen", "RacingNews365; PlanetF1")],
]

TICKER_TEXT = ("Nasdaq's worst week since March 2020 \u2022 Peru M6.8 quake "
               "\u2022 UK\u2013EU deal sealed \u2022 Rahul completes SENA hundreds")
FOOTER_SRC = ("Sources: AP \u2022 Reuters \u2022 AFP \u2022 Al Jazeera \u2022 The Guardian "
              "\u2022 Arab News \u2022 ANTARA \u2022 EU Council \u2022 ESPNcricinfo \u2022 IANS "
              "\u2022 ANI \u2022 Formula1.com \u2022 CBS/ABC \u2022 Kyiv Independent \u2022 LBC/PA "
              "\u2022 Brussels Times \u2022 The Quint \u2022 Telegraph \u2022 SBS")
FOOTER_NOTE = ("Facts checked against live reports as of 21 Nov 2026. Figures are "
               "provisional and may change as stories develop; casualty and market "
               "numbers follow the cited agencies.")

# ------------------------------------------------------------------ build
def build(cv):
    # Masthead
    cv.rect(0, 0, W, 96, NAVY)
    draw_text(cv, 12, 10, "THE WORLD IN ONE DAY", 1, GOLD, bold=True)
    draw_text(cv, 12, 30, "SATURDAY, 21 NOVEMBER 2026", 3, WHITE, bold=True)
    draw_text(cv, 12, 72, "Thirty stories from a world that did not slow down",
              1, (210, 210, 225))
    cv.rect(880, 8, 132, 84, PAPER)
    draw_text_c(cv, 946, 14, "30", 4, NAVY, bold=True)
    draw_text_c(cv, 946, 56, "10 TOP STORIES", 0.7, NAVY, bold=True)
    draw_text_c(cv, 946, 70, "20 BRIEFS", 0.7, NAVY, bold=True)

    # Ticker
    cv.rect(0, 100, W, 22, TICKER)
    cv.pill(12, 104, 100, 14, PAPER)
    draw_text_c(cv, 62, 107, "TOP LINES", 0.9, TICKER, bold=True)
    draw_text(cv, 122, 107, TICKER_TEXT, 0.8, WHITE, spacing=0)

    # Stat strip
    for i, (num, label, col) in enumerate(STATS):
        tx = 8 + i * 169
        cv.rect(tx, 128, 163, 46, col)
        draw_text_c(cv, tx + 81, 134, num, 2, WHITE, bold=True)
        draw_text_c(cv, tx + 81, 160, label, 0.7, WHITE)

    # Region chips
    widths = [text_w(t, 1) + 16 for t, _ in CHIPS]
    total = sum(widths) + 8 * (len(CHIPS) - 1)
    cx = (W - total) // 2
    for (label, col), w in zip(CHIPS, widths):
        cv.pill(cx, 180, w, 16, col)
        draw_text_c(cv, cx + w // 2, 183, label, 1, WHITE, bold=True)
        cx += w + 8

    # Top stories: 2 columns x 5 rows
    for idx, (chip, col, head, body, src, kind) in enumerate(STORIES):
        col_i = idx % 2
        row_i = idx // 2
        x = 8 + col_i * 510
        y = 202 + row_i * 101
        cv.rect(x, y, 498, 96, BORDER)
        cv.rect(x + 1, y + 1, 496, 94, PAPER)
        ART[kind](cv, x + 6, y + 6)
        cw = text_w(chip, 1) + 16
        cv.pill(x + 130, y + 8, cw, 14, col)
        draw_text_c(cv, x + 130 + cw // 2, y + 11, chip, 1, WHITE, bold=True)
        ly = y + 26
        for ln in wrap(head, 360, 1):
            draw_text(cv, x + 130, ly, ln, 1, INK, bold=True)
            ly += 16
        ly = y + 58
        for ln in wrap(body, 360, 0.65):
            draw_text(cv, x + 130, ly, ln, 0.65, INK)
            ly += 8
        draw_text(cv, x + 130, y + 86, src, 0.6, SRC)

    # Briefs header
    draw_text(cv, 8, 710, "ALSO TODAY \u2014 20 MORE BRIEFS", 2, NAVY,
              bold=True)
    cv.rect(8, 738, 1008, 2, NAVY)

    # Briefs, 3 columns
    bar_cols = [TICKER, NAVY, TAN, TEAL, PURPLE, STEEL, PINK]
    col_ends = []
    for ci, col in enumerate(BRIEFS):
        bx = 8 + ci * 336
        by = 746
        for bi, (head, src) in enumerate(col):
            lines = wrap(head, 316, 0.6)
            bh = len(lines) * 8 + 8 + 5
            cv.rect(bx, by, 3, bh - 5, bar_cols[bi % len(bar_cols)])
            ly = by
            for ln in lines:
                draw_text(cv, bx + 8, ly, ln, 0.6, INK)
                ly += 8
            draw_text(cv, bx + 8, ly, src, 0.6, SRC)
            by += bh
        col_ends.append(by)

    # Footer
    fy = max(col_ends) + 8
    for ln in wrap(FOOTER_SRC, 1008, 0.6):
        draw_text(cv, 8, fy, ln, 0.6, NAVY)
        fy += 8
    for ln in wrap(FOOTER_NOTE, 1008, 0.6):
        draw_text(cv, 8, fy, ln, 0.6, GREY)
        fy += 8
    cv.rect(0, 1012, W, 12, NAVY)


def _out_dir():
    here = os.path.dirname(os.path.abspath(__file__))
    return os.environ.get("MAKEFUN_OUTPUT_DIR", here)


def main():
    cv = Canvas(W, H, CREAM)
    build(cv)
    write_png(os.path.join(_out_dir(), "entry.png"), cv)


if __name__ == "__main__":
    main()
