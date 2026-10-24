"""Generates the static SVG images used by the tic-tac-toe board.

Every image the README can show is pre-built here, so a move only changes
which image each cell points at. That sidesteps GitHub's image cache: the
files never change, only the README does.

Run once (and again after tweaking styles):  python make_assets.py
"""
import os

OUT_DIR = os.path.join('assets', 'ttt')
FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"

# Light colors first, dark colors in the media query. GitHub's own palette.
STYLE = """
.bg{fill:#f6f8fa}.bd{stroke:#d0d7de}.x{stroke:#cf222e}.o{stroke:#0969da}
.xf{fill:#cf222e}.of{fill:#0969da}.ghost{stroke:#8c959f}.t1{fill:#1f2328}.t2{fill:#59636e}
.winx{fill:#ffebe9}.wino{fill:#ddf4ff}.btn{fill:#f6f8fa}.primary{fill:#1f883d}.ptext{fill:#ffffff}
@media (prefers-color-scheme: dark){
.bg{fill:#161b22}.bd{stroke:#30363d}.x{stroke:#ff7b72}.o{stroke:#79c0ff}
.xf{fill:#ff7b72}.of{fill:#79c0ff}.ghost{stroke:#6e7681}.t1{fill:#e6edf3}.t2{fill:#9198a1}
.winx{fill:#3d1d20}.wino{fill:#0c2d4b}.btn{fill:#21262d}.primary{fill:#238636}
}
.draw{stroke-dasharray:1;animation:draw .45s ease-out both}
.draw2{animation-delay:.2s}
.pulse{animation:pulse 2.4s ease-in-out infinite}
@keyframes draw{from{stroke-dashoffset:1}to{stroke-dashoffset:0}}
@keyframes pulse{0%,100%{opacity:.12}50%{opacity:.32}}
"""


def svg(width, height, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}"><style>{STYLE}</style>{body}</svg>\n')


def mark_x(cx, cy, r, cls='x', width=12, animate=False):
    """Two strokes of an X centred on (cx, cy); r is half the X's size."""
    anim = ' draw' if animate else ''
    return (f'<path class="{cls}{anim}" pathLength="1" d="M{cx - r} {cy - r}L{cx + r} {cy + r}" '
            f'stroke-width="{width}" stroke-linecap="round" fill="none"/>'
            f'<path class="{cls}{anim} draw2" pathLength="1" d="M{cx + r} {cy - r}L{cx - r} {cy + r}" '
            f'stroke-width="{width}" stroke-linecap="round" fill="none"/>')


def mark_o(cx, cy, r, cls='o', width=12, animate=False):
    anim = ' draw' if animate else ''
    return (f'<circle class="{cls}{anim}" pathLength="1" cx="{cx}" cy="{cy}" r="{r}" '
            f'stroke-width="{width}" fill="none" transform="rotate(-90 {cx} {cy})"/>')


def cell(content='', bg='bg', border='bd', border_width=2, opacity=1):
    return svg(120, 120,
               f'<g opacity="{opacity}"><rect class="{bg} {border}" x="4" y="4" width="112" height="112" '
               f'rx="18" stroke-width="{border_width}"/>{content}</g>')


def build_cells():
    files = {}
    for m, draw_mark in (('x', mark_x), ('o', mark_o)):
        r = 22 if m == 'x' else 26
        files[f'cell-{m}.svg'] = cell(draw_mark(60, 60, r))
        # Last move: the mark draws itself in, with a dot in the corner.
        files[f'cell-{m}-last.svg'] = cell(draw_mark(60, 60, r, animate=True) +
                                           f'<circle class="{m}f" cx="98" cy="22" r="5"/>')
        files[f'cell-{m}-win.svg'] = cell(draw_mark(60, 60, r), bg=f'win{m}', border=m, border_width=4)
        # Empty cell showing a faint, pulsing preview of whoever moves next.
        files[f'cell-empty-{m}.svg'] = cell(f'<g class="pulse">{draw_mark(60, 60, r, cls="ghost")}</g>')
    files['cell-empty-off.svg'] = cell(opacity=0.55)
    return files


def status(icon, title, subtitle):
    return svg(372, 76,
               '<rect class="bg bd" x="2" y="2" width="368" height="72" rx="18" stroke-width="2"/>'
               f'{icon}'
               f'<text class="t1" x="88" y="34" font-family="{FONT}" font-size="22" font-weight="700">{title}</text>'
               f'<text class="t2" x="88" y="56" font-family="{FONT}" font-size="14">{subtitle}</text>')


def build_status():
    x_icon, o_icon = mark_x(44, 38, 13, width=8), mark_o(44, 38, 16, width=8)
    both = mark_x(34, 38, 9, width=6) + mark_o(56, 38, 10, width=6)
    return {
        'status-turn-x.svg': status(x_icon, 'X to play', 'Click any empty square to place an X'),
        'status-turn-o.svg': status(o_icon, 'O to play', 'Click any empty square to place an O'),
        'status-win-x.svg': status(x_icon, 'X wins!', 'Three in a row. Start a new game below'),
        'status-win-o.svg': status(o_icon, 'O wins!', 'Three in a row. Start a new game below'),
        'status-draw.svg': status(both, "It's a draw", 'Board is full. Start a new game below'),
    }


def button(label, primary=False):
    fill, text, border = ('primary', 'ptext', '') if primary else ('btn', 't1', 'bd')
    return svg(184, 44,
               f'<rect class="{fill} {border}" x="1" y="1" width="182" height="42" rx="12" stroke-width="1.5"/>'
               f'<text class="{text}" x="92" y="28" text-anchor="middle" font-family="{FONT}" '
               f'font-size="15" font-weight="600">{label}</text>')


def build_buttons():
    return {
        'btn-reset.svg': button('↻  Reset board'),
        'btn-new.svg': button('▶  Play again', primary=True),
    }


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    files = {**build_cells(), **build_status(), **build_buttons()}
    for name, content in files.items():
        with open(os.path.join(OUT_DIR, name), 'w') as f:
            f.write(content)
    print(f'Wrote {len(files)} images to {OUT_DIR}/')


if __name__ == '__main__':
    main()
