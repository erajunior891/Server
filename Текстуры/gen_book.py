#!/usr/bin/env python3
"""
Генератор .grid для mc-asset
Книга "Скалковая Чума" в каноничной изометрии Minecraft (как оригинальная книга предметов)
Поддерживает 32x32 (book32.grid) и 128x128 (book128.grid).
"""

PALETTE = [
    ". = transparent",
    "K = #02060D",  # Глубокий чёрно-синий контур
    "k = #050E17",  # Глубокая тень кожи
    "b = #081827",  # Тёмная кожа скалка (основной тон)
    "B = #0F263C",  # Средний тон кожи
    "u = #173A5B",  # Светлый блик кожи/фаска
    "s = #07131F",  # Корешок темный
    "S = #14304B",  # Корешок светлый
    "p = #DDD4BA",  # Страницы светлые (пергамент)
    "P = #A89B7E",  # Страницы тень
    "d = #695F4B",  # Глубокий срез страниц
    "g = #7A5E28",  # Золото темное (оковы/уголки)
    "G = #C49E3F",  # Золото среднее
    "Y = #F7D872",  # Золото яркое (блик)
    "r = #63121E",  # Закладка темная
    "R = #A31F33",  # Закладка яркая
    "v = #004D5A",  # Скалк тёмный (жилы)
    "c = #00A6B8",  # Скалк бирюзовый
    "C = #00E8FA",  # Скалк яркий неоновый
    "w = #B3F9FF",  # Скалк ядро свечения
    "W = #FFFFFF",  # Чистый белый блик
]

# Каноничный 16x16 шаблон книги из ванильного Minecraft (по типам пикселей)
# . = пусто, K = контур, s = корешок, b = обложка, B = блик/тон, k = тень, p = страница, P = тень страницы, d = глубокая тень страницы
CANONICAL_16 = [
    "................",
    "........KKK.....",
    "......KKsBbK....",
    "....KKsbbbbbK...",
    "....sbbbbbbbbK..",
    "..KsbbbbbbbbbbK.",
    ".KsbbkbbbbkbbbKK",
    ".Kssbbkbbbbbbkd.",
    ".KKpbbbbbbkkPdP.",
    ".KspPpbbkkPdP.Kb",
    "..KspPpkPdP.KbKK",
    "...KspPdP.KbKK..",
    "....KspkKbKK....",
    ".....KkbKK......",
    "......KKK.......",
    "................",
]

def generate_32():
    W = H = 32
    grid = [['.'] * W for _ in range(H)]

    def set_px(x, y, ch):
        if 0 <= x < W and 0 <= y < H:
            grid[y][x] = ch

    # Масштабируем каноничную 16x16 геометрию в 32x32
    for y16, row in enumerate(CANONICAL_16):
        for x16, ch in enumerate(row):
            for dy in range(2):
                for dx in range(2):
                    px = x16 * 2 + dx
                    py = y16 * 2 + dy
                    # Текстурирование обложки и страниц
                    if ch == 'b':
                        val = 'b' if (px + py) % 3 != 0 else 'B'
                    elif ch == 'p':
                        val = 'p' if (px + py) % 2 == 0 else 'P'
                    elif ch == 'P':
                        val = 'P' if (px + py) % 2 == 0 else 'd'
                    elif ch == 's':
                        val = 's' if px <= 5 else 'k'
                    else:
                        val = ch
                    grid[py][px] = val

    # --- Сглаживание и фаска на верхне-левом ребре крышки ---
    for px, py in [(17, 3), (15, 4), (13, 5), (11, 6), (9, 7), (7, 8), (5, 9), (3, 10)]:
        if grid[py][px] in ('b', 'B'):
            set_px(px, py, 'u')

    # --- Детализация корешка слева (золотые рёбра переплёта) ---
    for py in [11, 14, 17]:
        if grid[py][1] != '.':
            set_px(1, py, 'G')
            set_px(2, py, 'Y')

    # --- Кованые золотые уголки в изометрии ---
    # Верхний угол
    set_px(18, 3, 'Y'); set_px(19, 3, 'G'); set_px(17, 4, 'G'); set_px(18, 4, 'g')
    # Правый угол
    set_px(27, 11, 'G'); set_px(28, 11, 'Y'); set_px(27, 12, 'Y'); set_px(26, 12, 'G'); set_px(26, 13, 'g')
    # Левый угол
    set_px(4, 11, 'G'); set_px(3, 12, 'Y'); set_px(4, 12, 'Y'); set_px(5, 12, 'G'); set_px(4, 13, 'g')
    # Нижний угол
    set_px(13, 20, 'G'); set_px(14, 20, 'Y'); set_px(13, 21, 'Y'); set_px(12, 21, 'G'); set_px(13, 22, 'g')

    # --- Скалковые жилы, расходящиеся от центра ---
    for vx, vy in [(12, 9), (11, 8), (20, 7), (21, 6), (11, 15), (10, 16), (21, 15), (22, 16)]:
        if grid[vy][vx] in ('b', 'B', 'k', 'u'): set_px(vx, vy, 'v')
    for vx, vy in [(13, 10), (19, 8), (12, 14), (20, 14)]:
        if grid[vy][vx] in ('b', 'B', 'k', 'u'): set_px(vx, vy, 'c')

    # --- Центральная скалковая руна / Око Катализатора в изометрии (16, 12) ---
    for rx, ry in [(16, 9), (14, 10), (18, 10), (12, 11), (20, 11), (13, 12), (19, 12),
                  (14, 13), (18, 13), (15, 14), (17, 14), (16, 15)]:
        if grid[ry][rx] in ('b', 'B', 'k', 'u'): set_px(rx, ry, 'v')

    for rx, ry in [(16, 10), (15, 11), (17, 11), (14, 12), (18, 12), (15, 13), (17, 13), (16, 14)]:
        set_px(rx, ry, 'c')

    # Светящееся ядро души
    set_px(15, 12, 'C'); set_px(17, 12, 'C')
    set_px(16, 11, 'w'); set_px(16, 13, 'w')
    set_px(16, 12, 'W')

    # --- Бордовая закладка-лента (ляссе), свисающая из страниц снизу ---
    ribbon = [(14, 21), (14, 22), (15, 22), (14, 23), (15, 23), (15, 24), (16, 24), (15, 25), (16, 25), (15, 26)]
    for rx, ry in ribbon:
        set_px(rx, ry, 'R')
    set_px(14, 24, 'r'); set_px(14, 25, 'r'); set_px(15, 27, 'R'); set_px(16, 27, '.')

    return grid

def save_grid(filename, grid):
    with open(filename, "wb") as f:
        f.write(b"[palette]\n")
        for p in PALETTE:
            f.write(p.encode("utf-8") + b"\n")
        f.write(b"\n[grid]\n")
        for row in grid:
            f.write("".join(row).encode("utf-8") + b"\n")
    print(f"Готово: {filename} ({len(grid)}x{len(grid[0])})")

if __name__ == "__main__":
    grid32 = generate_32()
    save_grid("book32.grid", grid32)