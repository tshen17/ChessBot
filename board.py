# Inspired by Sunfish. First-time engine mainly to get familiar with methodology.

import tools
import eval
from collections import namedtuple

### GLOBAL CONSTANTS ###

A8, H8, A2, H2, A1, E1, H1 = 21, 28, 81, 88, 91, 95, 98

# Starting board position
init_pos = (
    '         \n'
    '         \n'
    ' rnbqkbnr\n'
    ' pppppppp\n'
    ' ........\n'
    ' ........\n'
    ' ........\n'
    ' ........\n'
    ' PPPPPPPP\n'
    ' RNBQKBNR\n'
    '         \n'
    '         \n'
)

# Possible directions of moves for each piece.
U, D, L, R = -10, 10, -1, 1
directions = {
    'P': (U, U+U, U+L, U+R),
    'N': (R+R+U, R+R+D, D+D+R, D+D+L, L+L+D, L+L+U, U+U+L, U+U+R),
    'B': (R+U, R+D, L+D, L+U),
    'R': (U, D, L, R),
    'Q': (U, D, L, R, R+U, R+D, L+D, L+U),
    'K': (U, D, L, R, R+U, R+D, L+D, L+U),
}

### HELPER FUNCTIONS ###

def insert(pos, i, p):
    return pos[:i] + p + pos[i+1:]


### BOARD ###

Move = namedtuple("Move", "frm to is_capture is_castle")
Pin = namedtuple("Pin", "sq dir")
Check = namedtuple("Check", "sq, piece")

class Board:
    def __init__(self, pos=init_pos, wkc=True, wqc=True, bkc=True, bqc=True, kp=0, ep=0, checks=[], in_check=False, pins=[]):
        self.pos = pos
        self.wkc = wkc
        self.wqc = wqc
        self.bkc = bkc
        self.bqc = bqc
        self.kp = kp
        self.ep = ep
        self.checks = checks
        self.in_check = in_check
        self.pins = pins

    # Pseudo-legal move generator. Assumes that white is to move.
    def gen_moves(self):
        for frm, frm_piece in enumerate(self.pos):
            if not frm_piece.isupper():
                continue
            for dir in directions[frm_piece]:
                to = frm
                while A8 <= to <= H1:
                    to += dir
                    to_piece = self.pos[to]
                    capture = to_piece.islower()

                    # No off-board moves. For ray pieces, stop if blocked by own piece in that direction.
                    if to_piece.isspace() or to_piece.isupper():
                        break

                    # Pawn moves
                    if frm_piece == 'P':
                        if dir == U and to_piece != '.':
                            break
                        elif dir == U+U:
                            # Piece on to square, piece in between blocking, or pawn has already moved from 2nd rank
                            if to_piece != '.' or self.pos[frm + U] != '.' or frm < A2:
                                break
                        elif dir in (U+L, U+R):
                            if not to_piece.islower() and to != self.ep:
                                break
                            else:
                                capture = True

                    yield Move(frm, to, capture, False)

                    # Non-ray pieces only one move in direction. For ray pieces, no more further moves if last move is capture.
                    if frm_piece in 'PNK' or to_piece.islower():
                        break

                    # Castling
                    if frm_piece == 'R':
                        if frm == A1 and self.pos[to + R] == 'K' and self.wqc:
                            yield Move(to+R, to+L, False, True)
                        if frm == H1 and self.pos[to + L] == 'K' and self.wkc:
                            yield Move(to+L, to+R, False, True)

    def gen_legal_moves(self):
        moves = self.gen_moves()
        king_pos = self.pos.find('K')
        if king_pos < 0:
            print("King does not exist on board!")
            return
        king = self.pos[king_pos]

        # If in double check, can only consider king moves (cannot castle)
        if len(self.checks) > 1:
            for move in moves:
                if move.frm == king_pos and move.to - move.frm in directions['K']:
                    if self.move(move, flip=False).in_check:
                        continue
                    else:
                        yield move

        # If in check from one piece, must block attacking piece (if possible), capture it, or move king
        elif self.in_check:
            pos, piece = self.checks[0]

            # Finding squares to move pieces to block check. Knights, pawns, and king checks cannot be blocked.
            block_sqs = []
            if piece in 'brq':
                # Find direction of piece
                dir = 0
                if king_pos % 10 < pos % 10:
                    dir += R
                if king_pos % 10 > pos % 10:
                    dir += L
                if king_pos // 10 < pos // 10:
                    dir += D
                if king_pos // 10 > pos // 10:
                    dir += U

                to = king_pos
                while to != pos and not self.pos[to].isspace():
                    to += dir
                    block_sqs.append(to)

            for move in moves:
                legal = True
                # All pinned non-king pieces must move in direction of pin (to continue blocking)
                for pin in self.pins:
                    if move.frm == pin.sq:
                        dir = pin.dir
                        diff = move.to - move.frm
                        # Piece cannot move in pin direction (i.e. knight pinned by bishop cannot move)
                        if not dir in directions[self.pos[move.frm]]:
                            legal = False
                        # Pinned piece must move in pin direction
                        if not (diff % abs(dir) == 0 and abs(diff / dir) < 8):
                            legal = False

                if not legal:
                    continue

                # King moves (cannot castle)
                if move.frm == king_pos and move.to - move.frm in directions['K']:
                    if self.move(move, flip=False).in_check:
                        continue
                    else:
                        yield move
                # Moves that block check (not including king)
                elif move.to in block_sqs:
                    yield move

                # Capture checking piece
                elif move.to == pos:
                    yield move

        # Not currently in check
        else:
            for move in moves:
                legal = True
                # All pinned non-king pieces must move in direction of pin (to continue blocking)
                for pin in self.pins:
                    if move.frm == pin.sq:
                        dir = pin.dir
                        diff = move.to - move.frm
                        # Piece cannot move in pin direction (i.e. knight pinned by bishop cannot move)
                        if not dir in directions[self.pos[move.frm]]:
                            legal = False
                        # Pinned piece must move in pin direction
                        if not (diff % abs(dir) == 0 and abs(diff / dir) < 8):
                            legal = False

                # King moves
                if move.frm == king_pos:
                    # King moves into check
                    if self.move(move, flip=False).in_check:
                        legal = False

                    # Cannot castle through check
                    dir = move.to - move.frm
                    if move.is_castle and self.move(Move(move.frm, move.frm + dir // 2, False, True), flip=False).in_check:
                        legal = False

                if legal:
                    yield move

    # Generates all legal captures
    def gen_legal_captures(self):
        for move in self.gen_legal_moves():
            if move.is_capture:
                yield move

    # Finds all checks and pins in a position
    def find_checks_and_pins(self):
        # Local variables
        pins = []
        checks = []

        king_pos = self.pos.find('K')
        # For now, engine may explore lines that take the king so so error is raised.
        if king_pos < 0:
            return

        # Checks from enemy king (disallows illegal king moves)
        for dir in directions['K']:
            to = king_pos + dir
            to_piece = self.pos[to]
            # In check
            if to_piece == 'k':
                checks.append(Check(to, to_piece))

        # Checks from pawns (cannot pin)
        for dir in [U + L, U + R]:
            to = king_pos + dir
            to_piece = self.pos[to]
            # In check
            if to_piece == 'p':
                checks.append(Check(to, to_piece))

        # Checks from knights (cannot pin)
        for dir in directions['N']:
            to = king_pos + dir
            to_piece = self.pos[to]
            # In check
            if to_piece == 'n':
                checks.append(Check(to, to_piece))

        # Checks / pins from bishops or queens
        for dir in directions['B']:
            to = king_pos
            possible_pin = None
            while A8 <= to <= H1:
                to += dir
                to_piece = self.pos[to]

                if to_piece.isspace():
                    break

                if to_piece == '.':
                    continue
                elif to_piece.isupper():
                    if not possible_pin:
                        possible_pin = Pin(to, dir)
                    else:
                        # There is no pin or check in this direction since more than one friendly
                        break
                elif to_piece.islower():
                    # Piece that can attack
                    if to_piece == 'b' or to_piece == 'q':
                        # Encountered possible pin is now confirmed pinned piece.
                        if possible_pin:
                            pins.append(possible_pin)
                            break
                        # No pieces blocking attack. You are in check.
                        else:
                            # Only one piece can check in one direction
                            checks.append(Check(to, to_piece))
                            break
                    # If encountered enemy piece that cannot attack, then there is no possible pin or check in this direction
                    else:
                        break

        # Checks / pins from rooks or queens
        for dir in directions['R']:
            to = king_pos
            possible_pin = None
            while A8 <= to <= H1:
                to += dir
                to_piece = self.pos[to]

                if to_piece.isspace():
                    break

                if to_piece == '.':
                    continue
                elif to_piece.isupper():
                    if not possible_pin:
                        possible_pin = Pin(to, dir)
                    else:
                        # There is no pin or check in this direction since more than one friendly
                        break
                elif to_piece.islower():
                    # Piece that can attack
                    if to_piece == 'r' or to_piece == 'q':
                        # Encountered possible pin is now confirmed pinned piece.
                        if possible_pin:
                            pins.append(possible_pin)
                            break
                        # No pieces blocking attack. You are in check.
                        else:
                            checks.append(Check(to, to_piece))
                            break
                    # If encountered enemy piece that cannot attack, then there is no possible pin or check in this direction
                    else:
                        break

        # Assign
        self.checks = checks
        self.in_check = len(checks) > 0
        self.pins = pins

    def checkmate(self):
        # Hacky way to check if generator is empty
        return next(self.gen_legal_moves(), -1) == -1 and self.in_check

    def stalemate(self):
        # Hacky way to check if generator is empty
        return next(self.gen_legal_moves(), -1) == -1 and not self.in_check

    def flip(self):
        kp = 119 - self.kp if self.kp else 0
        ep = 119 - self.ep if self.ep else 0
        board = Board(self.pos[::-1].swapcase(), self.bkc, self.bqc, self.wkc, self.wqc, kp, ep)
        board.find_checks_and_pins()
        return board

    def dup(self):
        return Board(self.pos, self.wkc, self.wqc, self.bkc, self.bqc, self.kp, self.ep, self.checks, self.in_check, self.pins)

    # Returns new Board instance reflecting position after move. Original board instance does not change position
    def move(self, move, flip=True, update=True):
        frm, to = move.frm, move.to
        frm_piece, to_piece = self.pos[frm], self.pos[to]

        # Local variables
        pos = self.pos
        wkc, wqc, bkc, bqc = self.wkc, self.wqc, self.bkc, self.bqc
        kp = ep = 0

        # Move
        pos = insert(pos, frm, '.')
        pos = insert(pos, to, frm_piece)

        # Adjusting castling rights
        if frm == A1:
            wqc = False
        if frm == H1:
            wkc = False
        if to == A8:
            bqc = False
        if to == H8:
            bkc = False

        # Castling
        if frm_piece == 'K':
            wqc = wkc = False
            if abs(frm - to) == 2:
                # In-between square
                kp = (frm + to) // 2
                pos = insert(pos, kp, 'R')
                if frm > to:
                    pos = insert(pos, A1, '.')
                else:
                    pos = insert(pos, H1, '.')

        # Pawns
        if frm_piece == 'P':
            # Promotion (does not assume underpromotions)
            if A8 <= to <= H8:
                pos = insert(pos, to, 'Q')

            # En passant capture
            if to == self.ep:
                pos = insert(pos, to + D, '.')

            # Double move
            if to - frm == U + U:
                ep = frm + U

        board = Board(pos, wkc, wqc, bkc, bqc, kp, ep)
        if flip:
            return board.flip()
        else:
            board.find_checks_and_pins()
            return board
