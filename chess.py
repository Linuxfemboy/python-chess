#!/usr/bin/env python3
# Tap-to-move chess board for e-ink. Manual mode: no rules are enforced.
# Tap a piece, then tap the square to move it to. Tap the same piece again to cancel.
# Castling: move the king, then the rook. Promotion/en passant: edit by moving pieces by hand.
import tkinter as tk

SQ = 110                       # square size in pixels
LIGHT, DARK = "#ffffff", "#b5b5b5"
FONT = "DejaVu Sans"
USE_LETTERS = False            # set True if the piece symbols show up as empty boxes

START = [
    "rnbqkbnr",
    "pppppppp",
    "........",
    "........",
    "........",
    "........",
    "PPPPPPPP",
    "RNBQKBNR",
]
GLYPH = {"K": "\u2654", "Q": "\u2655", "R": "\u2656", "B": "\u2657", "N": "\u2658", "P": "\u2659",
         "k": "\u265a", "q": "\u265b", "r": "\u265c", "b": "\u265d", "n": "\u265e", "p": "\u265f"}

board = [list(r) for r in START]
history = []
sel = None


def name(r, c):
    return "abcdefgh"[c] + str(8 - r)


root = tk.Tk()
root.title("Chess")
canvas = tk.Canvas(root, width=8 * SQ, height=8 * SQ, highlightthickness=0)
canvas.pack()
status = tk.Label(root, text="Tap a piece, then a square", font=(FONT, 16))
status.pack()
bar = tk.Frame(root)
bar.pack(pady=4)


def draw():
    canvas.delete("all")
    for r in range(8):
        for c in range(8):
            x, y = c * SQ, r * SQ
            fill = LIGHT if (r + c) % 2 == 0 else DARK
            canvas.create_rectangle(x, y, x + SQ, y + SQ, fill=fill, outline="")
            p = board[r][c]
            if p != ".":
                text = p if USE_LETTERS else GLYPH[p]
                canvas.create_text(x + SQ // 2, y + SQ // 2, text=text,
                                   font=(FONT, int(SQ * 0.6)))
    if sel:
        r, c = sel
        canvas.create_rectangle(c * SQ + 3, r * SQ + 3, (c + 1) * SQ - 3, (r + 1) * SQ - 3,
                                outline="black", width=6)


def click(e):
    global sel
    c, r = e.x // SQ, e.y // SQ
    if not (0 <= r < 8 and 0 <= c < 8):
        return
    if sel is None:
        if board[r][c] != ".":
            sel = (r, c)
    elif sel == (r, c):
        sel = None
    else:
        sr, sc = sel
        history.append([row[:] for row in board])
        board[r][c], board[sr][sc] = board[sr][sc], "."
        status.config(text=name(sr, sc) + " -> " + name(r, c))
        sel = None
    draw()


def undo():
    global sel
    if history:
        board[:] = history.pop()
        sel = None
        status.config(text="Undone")
        draw()


def reset():
    global sel
    board[:] = [list(r) for r in START]
    history.clear()
    sel = None
    status.config(text="New game")
    draw()


tk.Button(bar, text="Undo", font=(FONT, 16), command=undo).pack(side="left", padx=12)
tk.Button(bar, text="Reset", font=(FONT, 16), command=reset).pack(side="left", padx=12)
canvas.bind("<Button-1>", click)
draw()
root.mainloop()
