"""Community tic-tac-toe played through GitHub issues.

A move is an issue titled `ttt|move|<0-8>`; `ttt|reset` clears the board.
The workflow passes the issue in through environment variables, this script
updates gamestate.json and rewrites the board section of README.md.

    ISSUE_TITLE='ttt|move|4' ISSUE_USER=octocat ISSUE_NUMBER=1 python game.py
    python game.py --render     # only re-render README.md from gamestate.json
"""
import json
import os
import sys
from datetime import datetime, timezone
from urllib.parse import quote

STATE_FILE = 'gamestate.json'
README_FILE = 'README.md'
ASSETS = 'assets/ttt'
START_MARKER = '<!-- TTT:START -->'
END_MARKER = '<!-- TTT:END -->'
RECENT_LIMIT = 6

REPO = os.environ.get('GITHUB_REPOSITORY', 'adhilsalim/adhilsalim')
CELL_NAMES = ['top left', 'top', 'top right', 'left', 'center', 'right',
              'bottom left', 'bottom', 'bottom right']
LINES = [(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6)]


# --- State ---

def new_board(state):
    """Starts a fresh game, keeping the scoreboard and activity log."""
    state.update({
        'board': [''] * 9,
        'turn': 'X',
        'status': 'playing',  # playing | won | draw
        'winner': None,
        'winLine': None,
        'lastMove': None,
        'moveCount': 0,
        'game': state.get('game', 0) + 1,
    })
    return state


def load_state():
    state = {}
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            state = json.load(f)
    # Anything without a board is treated as a first run (e.g. the old highway state).
    if 'board' not in state:
        state = new_board({'stats': {'X': 0, 'O': 0, 'draw': 0}, 'recent': []})
    return state


def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)
        f.write('\n')


def log(state, user, issue, text):
    entry = {'user': user, 'issue': issue, 'text': text,
             'at': datetime.now(timezone.utc).strftime('%Y-%m-%d')}
    state['recent'] = ([entry] + state['recent'])[:RECENT_LIMIT]


def find_winner(board):
    for line in LINES:
        a, b, c = (board[i] for i in line)
        if a and a == b == c:
            return a, list(line)
    return None, None


# --- Commands ---

def play(state, cell, user, issue):
    """Applies a move. Returns (changed, reply message for the issue)."""
    if state['status'] != 'playing':
        return False, 'This game is already over. Use **Play again** on the profile to start a new one.'
    if state['board'][cell]:
        taken = state['board'][cell]
        return False, f'The {CELL_NAMES[cell]} square already has an **{taken}**. Pick an empty square.'

    mark = state['turn']
    state['board'][cell] = mark
    state['lastMove'] = cell
    state['moveCount'] += 1
    placed = f'placed **{mark}** {where(cell)}'

    winner, line = find_winner(state['board'])
    if winner:
        state.update(status='won', winner=winner, winLine=line)
        state['stats'][winner] += 1
        log(state, user, issue, f'{placed} and won game #{state["game"]} 🏆')
        return True, f'You {placed} and won the game! 🏆'
    if all(state['board']):
        state['status'] = 'draw'
        state['stats']['draw'] += 1
        log(state, user, issue, f'{placed}, ending game #{state["game"]} in a draw')
        return True, f'You {placed}. The board is full, so it\'s a draw.'

    state['turn'] = 'O' if mark == 'X' else 'X'
    log(state, user, issue, placed)
    return True, f'You {placed}. It\'s **{state["turn"]}**\'s turn now.'


def reset(state, user, issue):
    finished = state['status'] != 'playing'
    if not finished and state['moveCount'] == 0:
        return False, 'The board is already empty. Go ahead and make the first move!'
    new_board(state)
    log(state, user, issue, f'started game #{state["game"]}' if finished else f'reset the board (game #{state["game"]})')
    return True, 'Fresh board is ready. **X** goes first.'


def handle(state, title, user, issue):
    parts = title.strip().lower().split('|')
    if parts == ['ttt', 'reset']:
        return reset(state, user, issue)
    if len(parts) == 3 and parts[:2] == ['ttt', 'move'] and parts[2] in list('012345678'):
        return play(state, int(parts[2]), user, issue)
    return False, f'I couldn\'t read the move `{title}`. Please use the squares on the profile to play.'


def where(cell):
    return 'in the center' if cell == 4 else f'in the {CELL_NAMES[cell]}'


# --- README rendering ---

def issue_link(title):
    return f'https://github.com/{REPO}/issues/new?template=tic_tac_toe.md&title={quote(title, safe="")}'


def image(name, alt, width):
    return f'<img src="{ASSETS}/{name}" alt="{alt}" width="{width}">'


def cell_html(state, i):
    mark = state['board'][i]
    playing = state['status'] == 'playing'
    if mark:
        variant = ('-win' if state['winLine'] and i in state['winLine']
                   else '-last' if i == state['lastMove'] else '')
        return image(f'cell-{mark.lower()}{variant}.svg', f'{mark} {CELL_NAMES[i]}', 104)
    if not playing:
        return image('cell-empty-off.svg', f'empty {CELL_NAMES[i]}', 104)
    img = image(f'cell-empty-{state["turn"].lower()}.svg', f'Place {state["turn"]} {where(i)}', 104)
    return f'<a href="{issue_link(f"ttt|move|{i}")}">{img}</a>'


def render_section(state):
    if state['status'] == 'won':
        banner = image(f'status-win-{state["winner"].lower()}.svg', f'{state["winner"]} wins', 372)
    elif state['status'] == 'draw':
        banner = image('status-draw.svg', 'Draw', 372)
    else:
        banner = image(f'status-turn-{state["turn"].lower()}.svg', f'{state["turn"]} to play', 372)

    # Cells sit on one line per row with no whitespace between them, so they render as a grid.
    rows = '\n<br>\n'.join(''.join(cell_html(state, r * 3 + c) for c in range(3)) for r in range(3))

    if state['status'] == 'playing':
        button = f'<a href="{issue_link("ttt|reset")}">{image("btn-reset.svg", "Reset board", 184)}</a>'
    else:
        button = f'<a href="{issue_link("ttt|reset")}">{image("btn-new.svg", "Play again", 184)}</a>'

    s = state['stats']
    score = (f'Game #{state["game"]} · move {state["moveCount"]} &nbsp;|&nbsp; '
             f'X wins {s["X"]} · O wins {s["O"]} · draws {s["draw"]}')

    recent = '\n'.join(
        f'- <img src="https://github.com/{e["user"]}.png?size=40" width="20" height="20" alt=""> '
        f'[@{e["user"]}](https://github.com/{e["user"]}) {e["text"]} · '
        f'<sub>[#{e["issue"]}](https://github.com/{REPO}/issues/{e["issue"]}) · {e["at"]}</sub>'
        for e in state['recent']
    ) or '- Nobody has played yet. Be the first!'

    return f"""{START_MARKER}
<p align="center">{banner}</p>

<p align="center">
{rows}
</p>

<p align="center">{button}</p>

<p align="center"><sub>{score}</sub></p>

#### Recent moves
{recent}
{END_MARKER}"""


def write_readme(state):
    with open(README_FILE) as f:
        readme = f.read()
    start, end = readme.find(START_MARKER), readme.find(END_MARKER)
    if start == -1 or end == -1:
        sys.exit(f'{README_FILE} is missing the {START_MARKER} / {END_MARKER} markers.')
    readme = readme[:start] + render_section(state) + readme[end + len(END_MARKER):]
    with open(README_FILE, 'w') as f:
        f.write(readme)


def main():
    state = load_state()
    if '--render' not in sys.argv:
        changed, message = handle(state, os.environ.get('ISSUE_TITLE', ''),
                                  os.environ.get('ISSUE_USER', 'someone'),
                                  int(os.environ.get('ISSUE_NUMBER', 0)))
        print(message)
        result_file = os.environ.get('TTT_RESULT_FILE')
        if result_file:
            with open(result_file, 'w') as f:
                f.write(message + '\n')
        if not changed:
            return
    save_state(state)
    write_readme(state)


if __name__ == '__main__':
    main()
