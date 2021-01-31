import eval
import board
import re
import sys

WHITE, BLACK = range(2)

FEN_INITIAL = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'

def parseFEN(fen):
    """ Parses a string in Forsyth-Edwards Notation into a board """
    pos, color, castling, enpas, _hclock, _fclock = fen.split()
    pos = re.sub(r'\d', (lambda m: '.'*int(m.group(0))), pos)
    pos = list(21*' ' + '  '.join(pos.split('/')) + 21*' ')
    pos[9::10] = ['\n']*12
    #if color == 'w': board[::10] = ['\n']*12
    #if color == 'b': board[9::10] = ['\n']*12
    pos = ''.join(pos)
    wqc = 'Q' in castling
    wkc = 'K' in castling
    bkc = 'k' in castling
    bqc = 'q' in castling
    ep = sunfish.parse(enpas) if enpas != '-' else 0
    bd = board.Board(pos, 0, wkc, wqc, bkc, bqc, 0, ep)
    score = eval.evaluate(bd)
    bd.score = score
    return bd if color == 'w' else board.flip()

def display_pos(bd, white=True, flip=False):
    if flip:
        bd = bd.flip()
    uni_pieces = {'R':'♜', 'N':'♞', 'B':'♝', 'Q':'♛', 'K':'♚', 'P':'♟',
                  'r':'♖', 'n':'♘', 'b':'♗', 'q':'♕', 'k':'♔', 'p':'♙', '.':'·'}

    for p in bd.pos[board.A8-1 :board.H1 + 1]:
        if p.isspace():
            print(p, end='')
        else:
            if not white:
                p = p.swapcase()
            print(uni_pieces[p], end=' ')
    print('\n---------------')

# WARNING - Deprecated
def flip_uci_move(move):
    frm, to = tools.to_move(move)
    return tools.to_uci((119 - frm, 119 - to))

def flip_move(move):
    frm, to = move.frm, move.to
    return board.Move(119 - frm, 119 - to, move.is_capture, move.is_castle)

def num_to_alg(num):
    rank = str(10 - num//10)
    file = chr(ord('a') - 1 + num % 10)
    return file + rank

def alg_to_num(alg):
    rank = (10 - (ord(alg[1]) - 48)) * 10
    file = (ord(alg[0]) - 96)
    return rank + file

def to_uci(move):
    frm, to = move.frm, move.to
    return num_to_alg(frm) + num_to_alg(to)

# WARNING - Deprecated
def to_move(uci):
    frm = uci[0:2]
    to = uci[2:4]
    return (alg_to_num(frm), alg_to_num(to))

def insert(pos, i, p):
    return pos[:i] + p + pos[i+1:]

def int_to_vis(pos):
    return (pos % 10 - 1, pos // 10 - 2)

def vis_to_int(sq):
    col, row = sq
    return 20 + row * 10 + (col + 1)


# Disable buffering
class Unbuffered(object):
    def __init__(self, stream):
        self.stream = stream
    def write(self, data):
        self.stream.write(data)
        self.stream.flush()
        sys.stderr.write(data)
        sys.stderr.flush()
    def __getattr__(self, attr):
        return getattr(self.stream, attr)
