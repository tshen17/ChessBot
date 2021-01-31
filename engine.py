#printimport board
import eval
import tools
import time
from collections import namedtuple

Node = namedtuple("Node", "lower upper")

MAX_TIME = 30
MAX_DEPTH = 4
TABLE_SIZE = 1e7
STEP_SIZE = 10
QS_LIMIT = 200



class Engine:
    def __init__(self):
        self.tp_score = {}
        self.tp_move = {}
        self.killer = {}

    # Function to update killer move dict (two moves at each depth)
    def add_killer(self, move, depth):
        if depth not in self.killer:
            self.killer[depth] = Node(None, None)
        node = self.killer[depth]
        if move not in node:
            self.killer[depth] = Node(move, node.lower)


    # Alpha-beta pruning algorithm with transposition table. Pseudo-code from http://people.csail.mit.edu/plaat/mtdf.html#abmem
    def alphabeta(self, board, alpha, beta, depth, ply=0):
        #print(alpha, beta, depth)
        # tools.display_pos(board)

        # If leaf node (depth = 0), return position score
        if depth == 0:
            return eval.evaluate(board)

        best_move = None
        node = self.tp_score.get((board, depth), Node(-eval.MATE_UPPER, eval.MATE_UPPER))

        # Check if node is in transposition table
        if (board, depth) in self.tp_score:
            #print("Found board at depth " + str(depth) + " in transposition table!")
            if node.lower >= beta: return node.lower
            if node.upper <= alpha: return node.upper
            alpha = max(alpha, node.lower)
            beta = min(beta, node.upper)

        # Move ordering scheme
        def moves():
            move_func = lambda x: eval.evaluate_move(board, x)
            capture_func = lambda x: eval.evaluate_capture(board, x)

            hash = self.tp_move.get(board)
            killer = self.killer[depth] if depth in self.killer else None
            skipped_moves = []

            # Hash moves (guaranteed to be legal)
            if hash:
                #print("Found hash move ", tools.to_uci(hash))
                skipped_moves.append(hash)
                yield hash

            # Captures
            for capture in sorted(board.gen_legal_captures(), key=capture_func, reverse=True):
                if capture not in skipped_moves:
                    skipped_moves.append(capture)
                    yield capture

            # Killer moves (legality check is slow - could be faster?)
            if killer:
                if killer.lower and killer.lower not in skipped_moves:
                    if not killer.lower in board.gen_legal_moves():
                        print("Killer move not legal!")
                    else:
                        skipped_moves.append(killer.lower)
                        yield killer.lower
                if killer.upper and killer.upper not in skipped_moves:
                    if not killer.upper in board.gen_legal_moves():
                        print("Killer move not legal!")
                    else:
                        skipped_moves.append(killer.lower)
                        yield killer.upper

            # All other moves
            for move in sorted(board.gen_legal_moves(), key=move_func, reverse=True):
                if move in skipped_moves:
                    continue
                yield move



        score = -eval.MATE_UPPER
        # Retain original value of alpha
        a = alpha

        # Evaluate
        for move in moves():
            #print("Considering move ", tools.to_uci(move))
            move_score = -self.alphabeta(board.move(move), -beta, -a, depth - 1, ply+1)
            if move_score > score:
                #print("New best move ", tools.to_uci(move), " with score ", move_score)
                score = move_score
                if len(self.tp_move) > TABLE_SIZE:
                    #print("Clearing tp_move")
                    self.tp_move.clear()
                self.tp_move[board] = move
            a = max(a, score)

            # Beta cutoff
            if a >= beta:
                # Update killer moves if move is non-capture
                if not move.is_capture:
                    self.add_killer(move, depth)
                break

        # Check if the game has ended
        if board.checkmate():
            score = -eval.MATE_UPPER
        elif board.stalemate():
            score = 0

        if len(self.tp_score) > TABLE_SIZE:
            #print("Clearing tp_score")
            self.tp_score.clear()
        if score <= alpha:
            self.tp_score[board, depth] = Node(node.lower, score)
        elif score > alpha and score < beta:
            self.tp_score[board, depth] = Node(score, score)
        else:
            self.tp_score[board, depth] = Node(score, node.upper)

        return score

    def mtdf(self, board, f, depth):
        g = f
        lower, upper = -eval.MATE_UPPER, eval.MATE_UPPER
        while lower < upper:
            beta = g + STEP_SIZE if g == lower else g
            g = self.alphabeta(board, beta-STEP_SIZE, beta, depth)
            if g < beta:
                upper = g
            else:
                lower = g
        return g

    # Iterative deepening framework
    def search(self, board, moves=1):
        f = 0
        for depth in range(1, MAX_DEPTH):
            start = time.time()
            f = self.mtdf(board, f, depth)
            print("Finished depth " + str(depth) + " in time ", time.time() - start)
            if time.time() - start > MAX_TIME:
                print("Search timed out at depth ", depth)
                break

        return self.tp_move.get(board), self.tp_score.get((board, depth)).lower
