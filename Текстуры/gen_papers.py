#!/usr/bin/env python3
r"""
Генератор .grid для mc-asset
Сборище / стопка бумаги 32x32 со строками текста по наклону листа бумаги (\)
"""

PALETTE = [
    ". = transparent",
    "K = #1A1A1A",
    "k = #383838",
    "D = #1A1A1A",
    "d = #555555",
    "s = #9E9E9E",
    "p = #D6D6D6",
    "w = #EEEEEE",
    "W = #FFFFFF",
]

GRID_ROWS = [
    "................................",
    "................................",
    "................................",
    "...................WWW..........",
    "..................WWppWW........",
    "................WWwwsWppWW......",
    "...............WwwwwDwwwwppWW...",
    ".............WWwwwDwwDwwwspppW..",
    "...........WwwwwDwwDwwDwwswwwwpW",
    ".........WWwwwDwwDwwDwwwwwswspwk",
    ".......WWwwwDwwDwwDwwwwwDwwswssk",
    "......WwwwDwwDwwDwwwwwDwwDwsssKk",
    "....WWwwDwwDwwDwwwwwDwwDwwwwsppk",
    "...WwwwwwDwwDwwwwwDwwDwwDwwDspk.",
    "...pkwwDwwDwwwwwDwwDwwDwwwwkwkK.",
    ".kpppkwwDwwwwwDwwDwwwwwwwpkpwk..",
    ".KkpppkwwDwwDwwDwwDwwDwkkpksK...",
    "..KppppwwwwwwDwwwwwwwwwkkpkkK...",
    "...kppppkwwDwwwwwDwwkpkkKK......",
    "...KkpppwwwwDwwDwwwkkkkKK.......",
    "...dKkpppkwwwDwwwwpkpkKK........",
    "....ddkppwkwwwwwkkkkK...........",
    "......KkpppkwwpkpkKK............",
    ".......dppppwkkkkK..............",
    "........dpppkpkKK...............",
    "........KkppkkK.................",
    ".........KkkKK..................",
    "..........KK....................",
    "................................",
    "................................",
    "................................",
    "................................",
]

if __name__ == "__main__":
    with open("papers32.grid", "wb") as f:
        f.write(b"[palette]\n")
        for p in PALETTE:
            f.write(p.encode("utf-8") + b"\n")
        f.write(b"\n[grid]\n")
        for r in GRID_ROWS:
            f.write(r.encode("utf-8") + b"\n")
    print("papers32.grid успешно сгенерирован со строками по диагонали (\\).")
