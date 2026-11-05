#!/usr/bin/env python3
# Tap-to-move chess for e-ink, with the real rules.
# Tap a piece to see its legal moves (dots = move, ring = capture), then tap a square.
# Handles check, checkmate, stalemate, castling, en passant, promotion and draws.
# Pure Python + Tkinter, no extra packages.

START = "rnbqkbnr" "pppppppp" + "." * 32 + "PPPPPPPP" "RNBQKBNR"
KN = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
KG = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
ROOK = [(-1, 0), (1, 0), (0, -1), (0, 1)]
BISH = [(-1, -1), (-1, 1), (1, -1), (1, 1)]


def new_state():
    return {"b": list(START), "turn": "w", "castle": "KQkq", "ep": None, "half": 0, "full": 1}


def name(i):
    return "abcdefgh"[i % 8] + str(8 - i // 8)


def attacked(b, sq, by):
    """Is square sq attacked by side `by` ('w' or 'b')?"""
    r, c = divmod(sq, 8)
    white = by == "w"
    pr = r + 1 if white else r - 1
    pawn = "P" if white else "p"
    for dc in (-1, 1):
        if 0 <= pr < 8 and 0 <= c + dc < 8 and b[pr * 8 + c + dc] == pawn:
            return True
    for pieces, ch in ((KN, "N" if white else "n"), (KG, "K" if white else "k")):
        for dr, dc in pieces:
            rr, cc = r + dr, c + dc
            if 0 <= rr < 8 and 0 <= cc < 8 and b[rr * 8 + cc] == ch:
                return True
    rook, bish, queen = ("R", "B", "Q") if white else ("r", "b", "q")
    for dirs, kinds in ((ROOK, (rook, queen)), (BISH, (bish, queen))):
        for dr, dc in dirs:
            rr, cc = r + dr, c + dc
            while 0 <= rr < 8 and 0 <= cc < 8:
                p = b[rr * 8 + cc]
                if p != ".":
                    if p in kinds:
                        return True
                    break
                rr += dr
                cc += dc
    return False


def add_pawn(out, fr, to, promote):
    if promote:
        for pc in "qrbn":
            out.append((fr, to, pc))
    else:
        out.append((fr, to, ""))


def pseudo(s):
    b, white = s["b"], s["turn"] == "w"
    out = []
    for i in range(64):
        p = b[i]
        if p == "." or p.isupper() != white:
            continue
        r, c = divmod(i, 8)
        k = p.lower()
        if k == "p":
            d = -1 if white else 1
            start = 6 if white else 1
            last = 0 if white else 7
            r1 = r + d
            if 0 <= r1 < 8:
                if b[r1 * 8 + c] == ".":
                    add_pawn(out, i, r1 * 8 + c, r1 == last)
                    if r == start and b[(r + 2 * d) * 8 + c] == ".":
                        out.append((i, (r + 2 * d) * 8 + c, ""))
                for dc in (-1, 1):
                    cc = c + dc
                    if 0 <= cc < 8:
                        t = r1 * 8 + cc
                        if b[t] != "." and b[t].isupper() != white:
                            add_pawn(out, i, t, r1 == last)
                        elif t == s["ep"]:
                            out.append((i, t, ""))
        elif k in "nk":
            for dr, dc in (KN if k == "n" else KG):
                rr, cc = r + dr, c + dc
                if 0 <= rr < 8 and 0 <= cc < 8:
                    t = rr * 8 + cc
                    if b[t] == "." or b[t].isupper() != white:
                        out.append((i, t, ""))
        else:
            dirs = (ROOK if k in "rq" else []) + (BISH if k in "bq" else [])
            for dr, dc in dirs:
                rr, cc = r + dr, c + dc
                while 0 <= rr < 8 and 0 <= cc < 8:
                    t = rr * 8 + cc
                    if b[t] == ".":
                        out.append((i, t, ""))
                    else:
                        if b[t].isupper() != white:
                            out.append((i, t, ""))
                        break
                    rr += dr
                    cc += dc
    return out


def castles(s):
    b, white = s["b"], s["turn"] == "w"
    home = 56 if white else 0
    king, rook = ("K", "R") if white else ("k", "r")
    foe = "b" if white else "w"
    out = []
    if b[home + 4] != king or attacked(b, home + 4, foe):
        return out
    ks, qs = ("K", "Q") if white else ("k", "q")
    if (ks in s["castle"] and b[home + 7] == rook and b[home + 5] == "." and b[home + 6] == "."
            and not attacked(b, home + 5, foe) and not attacked(b, home + 6, foe)):
        out.append((home + 4, home + 6, ""))
    if (qs in s["castle"] and b[home] == rook and all(b[home + x] == "." for x in (1, 2, 3))
            and not attacked(b, home + 3, foe) and not attacked(b, home + 2, foe)):
        out.append((home + 4, home + 2, ""))
    return out


def apply(s, m):
    fr, to, promo = m
    b = s["b"][:]
    p = b[fr]
    white = p.isupper()
    cap = b[to] != "."
    castle = s["castle"]
    ep = None
    if p.lower() == "p":
        if to == s["ep"]:
            b[to + (8 if white else -8)] = "."
            cap = True
        if abs(to - fr) == 16:
            ep = (fr + to) // 2
    b[to] = (promo.upper() if white else promo) if promo else p
    b[fr] = "."
    if p.lower() == "k" and abs(to - fr) == 2:
        if to > fr:
            b[to - 1], b[to + 1] = b[to + 1], "."
        else:
            b[to + 1], b[to - 2] = b[to - 2], "."
    for sq, ch in ((60, "K"), (60, "Q"), (63, "K"), (56, "Q"), (4, "k"), (4, "q"), (7, "k"), (0, "q")):
        if fr == sq or to == sq:
            castle = castle.replace(ch, "")
    return {"b": b, "turn": "b" if white else "w", "castle": castle, "ep": ep,
            "half": 0 if (p.lower() == "p" or cap) else s["half"] + 1,
            "full": s["full"] + (0 if white else 1)}


def in_check(s):
    white = s["turn"] == "w"
    return attacked(s["b"], s["b"].index("K" if white else "k"), "b" if white else "w")


def legal(s):
    white = s["turn"] == "w"
    me, foe = ("K", "b") if white else ("k", "w")
    out = []
    for m in pseudo(s) + castles(s):
        n = apply(s, m)
        if not attacked(n["b"], n["b"].index(me), foe):
            out.append(m)
    return out


def too_few_pieces(s):
    rest = [p for p in s["b"] if p not in ".Kk"]
    return not rest or (len(rest) == 1 and rest[0].lower() in "bn")


def describe(s, moves):
    """Returns (text, game_over)."""
    side = "White" if s["turn"] == "w" else "Black"
    other = "Black" if s["turn"] == "w" else "White"
    chk = in_check(s)
    if not moves:
        if chk:
            return "CHECKMATE - " + other + " wins", True
        return "Stalemate - draw", True
    if s["half"] >= 100:
        return "Draw (50-move rule)", True
    if too_few_pieces(s):
        return "Draw (not enough pieces)", True
    return side + " to move" + ("  -  CHECK!" if chk else ""), False


# ---------------------------------------------------------------- UI

def main():
    import tkinter as tk

    SQ = 110
    LIGHT, DARK = "#ffffff", "#b5b5b5"
    FONT = "DejaVu Sans"
    USE_LETTERS = False  # set True if the piece symbols show up as empty boxes
    GLYPH = {"K": "\u2654", "Q": "\u2655", "R": "\u2656", "B": "\u2657", "N": "\u2658", "P": "\u2659",
             "k": "\u265a", "q": "\u265b", "r": "\u265c", "b": "\u265d", "n": "\u265e", "p": "\u265f"}

    g = {"state": new_state(), "sel": None, "pending": None, "last": "-", "hist": []}
    g["moves"] = legal(g["state"])
    g["text"], g["over"] = describe(g["state"], g["moves"])

    root = tk.Tk()
    root.title("Chess")
    cv = tk.Canvas(root, width=8 * SQ, height=8 * SQ, highlightthickness=0)
    cv.pack()
    status = tk.Label(root, text="", font=(FONT, 18, "bold"))
    status.pack()
    lastlbl = tk.Label(root, text="", font=(FONT, 14))
    lastlbl.pack()
    bar = tk.Frame(root)
    bar.pack(pady=4)

    def glyph(p):
        return p if USE_LETTERS else GLYPH[p]

    def draw():
        s = g["state"]
        b = s["b"]
        cv.delete("all")
        for i in range(64):
            r, c = divmod(i, 8)
            x, y = c * SQ, r * SQ
            cv.create_rectangle(x, y, x + SQ, y + SQ, fill=LIGHT if (r + c) % 2 == 0 else DARK, outline="")
            if b[i] != ".":
                cv.create_text(x + SQ // 2, y + SQ // 2, text=glyph(b[i]), font=(FONT, int(SQ * 0.6)))
        if in_check(s):
            k = b.index("K" if s["turn"] == "w" else "k")
            x, y = (k % 8) * SQ, (k // 8) * SQ
            cv.create_rectangle(x + 4, y + 4, x + SQ - 4, y + SQ - 4, outline="black", width=5, dash=(10, 6))
        sel = g["sel"]
        if sel is not None:
            x, y = (sel % 8) * SQ, (sel // 8) * SQ
            cv.create_rectangle(x + 3, y + 3, x + SQ - 3, y + SQ - 3, outline="black", width=6)
            for fr, to, _ in g["moves"]:
                if fr != sel:
                    continue
                cx, cy = (to % 8) * SQ + SQ // 2, (to // 8) * SQ + SQ // 2
                if b[to] != "." or (b[sel].lower() == "p" and to == s["ep"]):
                    cv.create_oval(cx - 46, cy - 46, cx + 46, cy + 46, outline="black", width=5)
                else:
                    cv.create_oval(cx - 13, cy - 13, cx + 13, cy + 13, fill="black", outline="black")
        if g["pending"]:
            white = s["turn"] == "w"
            cv.create_rectangle(2 * SQ, 3 * SQ, 6 * SQ, 4 * SQ, fill="white", outline="black", width=5)
            for n, pc in enumerate("qrbn"):
                cv.create_text(2 * SQ + n * SQ + SQ // 2, 3 * SQ + SQ // 2,
                               text=glyph(pc.upper() if white else pc), font=(FONT, int(SQ * 0.6)))
        status.config(text=g["text"])
        lastlbl.config(text="Move " + str(s["full"]) + "   Last: " + g["last"])

    def play(m):
        s = g["state"]
        g["hist"].append((s, g["last"]))
        g["last"] = name(m[0]) + "-" + name(m[1]) + ("=" + m[2].upper() if m[2] else "")
        g["state"] = apply(s, m)
        g["moves"] = legal(g["state"])
        g["text"], g["over"] = describe(g["state"], g["moves"])

    def click(e):
        c, r = e.x // SQ, e.y // SQ
        if not (0 <= r < 8 and 0 <= c < 8) or g["over"]:
            return
        i = r * 8 + c
        s = g["state"]
        if g["pending"]:
            fr, to = g["pending"]
            g["pending"] = None
            if r == 3 and 2 <= c <= 5:
                play((fr, to, "qrbn"[c - 2]))
            draw()
            return
        p = s["b"][i]
        mine = p != "." and p.isupper() == (s["turn"] == "w")
        sel = g["sel"]
        if sel is None or mine:
            g["sel"] = None if i == sel else (i if mine else None)
        else:
            ms = [m for m in g["moves"] if m[0] == sel and m[1] == i]
            g["sel"] = None
            if ms:
                if ms[0][2]:
                    g["pending"] = (sel, i)
                else:
                    play(ms[0])
        draw()

    def undo():
        if g["hist"]:
            g["state"], g["last"] = g["hist"].pop()
            g["moves"] = legal(g["state"])
            g["text"], g["over"] = describe(g["state"], g["moves"])
            g["sel"] = g["pending"] = None
            draw()

    def reset():
        g.update(state=new_state(), sel=None, pending=None, last="-", hist=[])
        g["moves"] = legal(g["state"])
        g["text"], g["over"] = describe(g["state"], g["moves"])
        draw()

    tk.Button(bar, text="Undo", font=(FONT, 16), command=undo).pack(side="left", padx=12)
    tk.Button(bar, text="New game", font=(FONT, 16), command=reset).pack(side="left", padx=12)
    cv.bind("<Button-1>", click)
    draw()
    root.mainloop()


if __name__ == "__main__":
    main()
        
