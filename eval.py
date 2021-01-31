# Inspired by Sunfish.

import numpy as np

### PARAMETERS ###

piece = { 'P': 100, 'N': 300, 'B': 340, 'R': 490, 'Q': 950, 'K': 60000 }

# TODO: Make endgame and opening/middle game charts
pst = {
    'P': (   0,   0,   0,   0,   0,   0,   0,   0,
            78,  83,  86,  73, 102,  82,  85,  90,
             7,  29,  21,  44,  40,  31,  44,   7,
           -17,  16,  -2,  15,  14,   0,  15, -13,
           -26,   3,  10,   9,   6,   1,   0, -23,
           -22,   9,   5, -11, -10,  -2,   3, -19,
           -31,   8,  -7, -37, -36, -14,   3, -31,
             0,   0,   0,   0,   0,   0,   0,   0),
    'N': ( -66, -53, -75, -75, -10, -55, -58, -70,
            -3,  -6, 100, -36,   4,  62,  -4, -14,
            10,  67,   1,  74,  73,  27,  62,  -2,
            24,  24,  45,  37,  33,  41,  25,  17,
            -1,   5,  31,  21,  22,  35,   2,   0,
           -18,  10,  13,  22,  18,  15,  11, -14,
           -23, -15,   2,   0,   2,   0, -23, -20,
           -74, -23, -26, -24, -19, -35, -22, -69),
    'B': ( -59, -78, -82, -76, -23,-107, -37, -50,
           -11,  20,  35, -42, -39,  31,   2, -22,
            -9,  39, -32,  41,  52, -10,  28, -14,
            25,  17,  20,  34,  26,  25,  15,  10,
            13,  10,  17,  23,  17,  16,   0,   7,
            14,  25,  24,  15,   8,  25,  20,  15,
            19,  20,  11,   6,   7,   6,  20,  16,
            -7,   2, -15, -12, -14, -15, -10, -10),
    'R': (  35,  29,  33,   4,  37,  33,  56,  50,
            55,  29,  56,  67,  55,  62,  34,  60,
            19,  35,  28,  33,  45,  27,  25,  15,
             0,   5,  16,  13,  18,  -4,  -9,  -6,
           -28, -35, -16, -21, -13, -29, -46, -30,
           -42, -28, -42, -25, -25, -35, -26, -46,
           -53, -38, -31, -26, -29, -43, -44, -53,
           -30, -24, -18,   5,  -2, -18, -31, -32),
    'Q': (   6,   1,  -8,-104,  69,  24,  88,  26,
            14,  32,  60, -10,  20,  76,  57,  24,
            -2,  43,  32,  60,  72,  63,  43,   2,
             1, -16,  22,  17,  25,  20, -13,  -6,
           -14, -15,  -2,  -5,  -1, -10, -20, -22,
           -30,  -6, -13, -11, -16, -11, -16, -27,
           -36, -18,   0, -19, -15, -15, -21, -38,
           -39, -30, -31, -13, -31, -36, -34, -42),
    'K': (   4,  54,  47, -99, -99,  60,  83, -62,
           -32,  10,  55,  56,  56,  55,  10,   3,
           -62,  12, -57,  44, -67,  28,  37, -31,
           -55,  50,  11,  -4, -19,  13,   0, -49,
           -55, -43, -52, -28, -51, -47,  -8, -50,
           -47, -42, -43, -79, -64, -32, -29, -32,
            -4,   3, -14, -50, -57, -18,  13,   4,
            17,  30,  -3, -14,   6,  -1,  40,  18),
}

# Checkmate conditions
MATE_LOWER = piece['K'] - 10*piece['Q']
MATE_UPPER = piece['K'] + 10*piece['Q']

# Pad tables and join piece and pst dictionaries
for k, table in pst.items():
    padrow = lambda row: (0,) + tuple(x+piece[k] for x in row) + (0,)
    pst[k] = sum((padrow(table[i*8:i*8+8]) for i in range(8)), ())
    pst[k] = (0,)*20 + pst[k] + (0,)*20



### EVALUATION ###

# Evaluates positional/material advantage of a position
def evaluate(board):
    if board.checkmate():
        return -MATE_UPPER
    if board.stalemate():
        return 0

    white, black = 0, 1
    score = 0
    bishops = [0, 0]
    file_pawns = [np.zeros(8), np.zeros(8)]
    file_control = [np.zeros(8), np.zeros(8)]
    num_doubled = [0, 0]

    for pos, piece in enumerate(board.pos):
        file = (pos % 10) - 1
        if piece.isupper():
            score += pst[piece][pos]
            if piece == 'B':
                bishops[white] += 1
            if piece == 'P':
                if file_pawns[white][file] >= 1:
                    num_doubled[white] += 1
                file_pawns[white][file] += 1
            if piece in 'RQ':
                file_control[white][file] += 1
        elif piece.islower():
            score -= pst[piece.swapcase()][119 - pos]
            if piece == 'b':
                bishops[black] += 1
            if piece == 'p':
                if file_pawns[black][file] >= 1:
                    num_doubled[black] += 1
                file_pawns[black][file] = 1
            if piece in 'rq':
                file_control[black][file] += 1

    # Bishop pair bonus (higher bonus if position is more open)
    if bishops[white] >= 2:
        score += 20
    if bishops[black] >= 2:
        score -= 20

    # Doubled pawns penalty (will also penalize for tripled pawns)
    score += (num_doubled[black] - num_doubled[white]) * 30

    # (Semi) open file control
    for file in range(8):
        control = file_control[white][file] - file_control[black][file]
        # White
        if control > 0:
            if file_pawns[white][file] == 0:
                score += (2 - min(2, file_pawns[black][file])) * 25
        elif control < 0:
            if file_pawns[black][file] == 0:
                score -= (2 - min(2, file_pawns[white][file])) * 25

    # King safety

    # If up material, prefer trades


    return score

def evaluate_move(board, move):

    frm, to = move.frm, move.to
    frm_piece, to_piece = board.pos[frm], board.pos[to]
    init_score = evaluate(board)
    # To avoid infinite recursion
    final_score = -evaluate(board.move(move, update=False))
    score = final_score - init_score

    # # Opponent king just castled through check. Strongly disincentivize
    # if abs(to - board.kp) < 2:
    #     score += pst['K'][119 - frm]

    return score

# Used the least valuable attacker - most valuable victim heuristic
def evaluate_capture(board, capture):
    if not capture.is_capture:
        raise ValueError("Move must be a capture!")

    frm, to = capture.frm, capture.to
    att, vic = board.pos[frm], board.pos[to].upper()
    return pst[vic][to] - pst[att][frm]
