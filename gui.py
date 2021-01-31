#import PySimpleGUI as sg
import os
import sys
import pygame
import engine
import board
import tools
import eval

import random
import math

### CONSTANTS ###

# GAME SPECIFICATIONS
SQ_SIZE = 85
MARGIN = SQ_SIZE // 2
BD_HEIGHT = BD_WIDTH = INFO_HEIGHT = 8 * SQ_SIZE
INFO_WIDTH = 6 * SQ_SIZE
ENGINE_HEIGHT = 3 * SQ_SIZE
MOVES_HEIGHT = 4 * SQ_SIZE
WIN_HEIGHT = BD_HEIGHT + 2*MARGIN
WIN_WIDTH = BD_WIDTH + INFO_WIDTH + 3*MARGIN
OFFSET = MARGIN // 3
FPS = 60

# GAME STATES
MENU = "menu"
ANALYSIS = "analysis"
PLAYING = "playing"
WIN = "win"
LOSE = "lose"
RESIGN = "resign"
STALEMATE = "stalemate"
OVER = (WIN, LOSE, RESIGN, STALEMATE)

# END OF GAME MESSAGES
WIN_MSG = "Checkmate. You win!"
LOSE_MSG = "Checkmate. Engine wins!"
RESIGN_MSG = "Engine wins by resignation!"
STALEMATE_MSG = "Draw by stalemate"

# COLORS
ALPHA = 90
BLACK = (0,0,0)
BLACK_T = (0,0,0, ALPHA)
WHITE = (255, 255, 255)
WHITE_T = (255, 255, 255, ALPHA)
GRAY = (128, 128, 128)
LIGHT_GRAY = (220, 220, 220)
GREEN = (92, 219, 92)
YELLOW = (250, 218, 94)
YELLOW_T = (250, 218, 94, ALPHA)
GREEN = (0, 128, 0)
GREEN_T = (0, 100, 0, ALPHA)
DARK_GREEN = (85,107,47)
DARK_GREEN_T = (85,107,47,ALPHA)
RED = (255, 0, 0)
RED_T = (255, 0, 0, ALPHA)

CHESSCOM_COLORS = ((235, 235, 208), (119, 148, 85))

# LABELS
RANKS = ['8', '7', '6', '5', '4', '3', '2', '1']
FILES = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
TITLE = 'Chess'

class Game:
    def __init__(self):
        os.environ['SDL_VIDEO_CENTERED'] = '1'
        pygame.init()
        pygame.font.init()
        pygame.display.set_caption(TITLE)

        self.screen = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
        self.clock = pygame.time.Clock()

        # Images
        self.bg = pygame.transform.smoothscale(pygame.image.load('imgs/bg.jpeg').convert(), (WIN_WIDTH, WIN_HEIGHT))
        self.dark_sq = pygame.transform.smoothscale(pygame.image.load('imgs/med_sq.jpg').convert(), (BD_WIDTH, BD_HEIGHT))
        self.light_sq = pygame.transform.smoothscale(pygame.image.load('imgs/light_sq.jpg').convert(), (BD_WIDTH, BD_HEIGHT))
        pieces = pygame.transform.smoothscale(pygame.image.load('imgs/pieces.png').convert(), (6 * SQ_SIZE, 2 * SQ_SIZE))
        self.pieces = {
            'K': pygame.Surface.subsurface(pieces, (0, 0, SQ_SIZE, SQ_SIZE)),
            'Q': pygame.Surface.subsurface(pieces, (SQ_SIZE, 0, SQ_SIZE, SQ_SIZE)),
            'B': pygame.Surface.subsurface(pieces, (2*SQ_SIZE, 0, SQ_SIZE, SQ_SIZE)),
            'N': pygame.Surface.subsurface(pieces, (3*SQ_SIZE, 0, SQ_SIZE, SQ_SIZE)),
            'R': pygame.Surface.subsurface(pieces, (4*SQ_SIZE, 0, SQ_SIZE, SQ_SIZE)),
            'P': pygame.Surface.subsurface(pieces, (5*SQ_SIZE, 0, SQ_SIZE, SQ_SIZE)),
            'k': pygame.Surface.subsurface(pieces, (0, SQ_SIZE, SQ_SIZE, SQ_SIZE)),
            'q': pygame.Surface.subsurface(pieces, (SQ_SIZE, SQ_SIZE, SQ_SIZE, SQ_SIZE)),
            'b': pygame.Surface.subsurface(pieces, (2*SQ_SIZE, SQ_SIZE, SQ_SIZE, SQ_SIZE)),
            'n': pygame.Surface.subsurface(pieces, (3*SQ_SIZE, SQ_SIZE, SQ_SIZE, SQ_SIZE)),
            'r': pygame.Surface.subsurface(pieces, (4*SQ_SIZE, SQ_SIZE, SQ_SIZE, SQ_SIZE)),
            'p': pygame.Surface.subsurface(pieces, (5*SQ_SIZE, SQ_SIZE, SQ_SIZE, SQ_SIZE)),
        }
        self.random = pygame.transform.smoothscale(pygame.image.load('imgs/random.png').convert_alpha(), (SQ_SIZE, SQ_SIZE))
        self.flip = pygame.transform.smoothscale(pygame.image.load('imgs/flip_icon.png').convert_alpha(), (SQ_SIZE // 2, SQ_SIZE // 2))
        self.resign = pygame.transform.smoothscale(pygame.image.load('imgs/resign.png').convert_alpha(), (SQ_SIZE // 2, SQ_SIZE // 2))
        self.play_again = pygame.transform.smoothscale(pygame.image.load('imgs/play_again.png').convert_alpha(), (SQ_SIZE // 2, SQ_SIZE // 2))
        self.analysis = pygame.transform.smoothscale(pygame.image.load('imgs/analysis.png').convert_alpha(), (SQ_SIZE, SQ_SIZE))

        # Buttons initialized
        self.init_buttons()

        # Fonts
        self.board_font = pygame.font.SysFont('Helvetica', SQ_SIZE // 5, bold=True)
        self.moves_font = pygame.font.SysFont('Helvetica', SQ_SIZE // 6, bold=True)
        self.info_font = pygame.font.SysFont('Helvetica', SQ_SIZE // 4, bold=True)

        # Sounds
        self.move_fx = pygame.mixer.Sound("sounds/move.wav")
        self.start_game_fx = pygame.mixer.Sound("sounds/game_start.wav")
        self.horse_fx = pygame.mixer.Sound("sounds/horse.wav")
        self.capture_fx = pygame.mixer.Sound("sounds/capture.wav")

        # Starting game state
        self.init_game_state()


        self.dragging = False


    '''
    Stores the button variables in the game to improve efficiency
    '''
    def init_buttons(self):
        # Flip button
        flip_rect = self.flip.get_rect()
        flip_rect.center = (2*MARGIN + BD_WIDTH + SQ_SIZE // 2, WIN_HEIGHT - MARGIN - SQ_SIZE // 2)
        self.flip_button = flip_rect

        resign_rect = self.resign.get_rect()
        resign_rect.center = (2*MARGIN + BD_WIDTH + SQ_SIZE + SQ_SIZE // 2, WIN_HEIGHT - MARGIN - SQ_SIZE // 2)
        self.resign_button = resign_rect

        again_rect = self.resign.get_rect()
        again_rect.center = (2*MARGIN + BD_WIDTH + INFO_WIDTH // 2, MARGIN + INFO_HEIGHT // 2)
        self.play_again_button = again_rect

        analysis_rect = self.analysis.get_rect()
        analysis_rect.center = (2*MARGIN + BD_WIDTH + 3 * SQ_SIZE, MARGIN + INFO_HEIGHT // 4)
        self.analysis_button = analysis_rect

        white = self.pieces['K']
        white_rect = white.get_rect()
        white_rect.center = (2*MARGIN + BD_WIDTH + SQ_SIZE + SQ_SIZE // 2, MARGIN + INFO_HEIGHT // 2 + SQ_SIZE // 2)
        self.white_button = white_rect

        black = self.pieces['k']
        black_rect = black.get_rect()
        black_rect.center = (2*MARGIN + BD_WIDTH + 4 * SQ_SIZE + SQ_SIZE // 2, MARGIN + INFO_HEIGHT // 2 + SQ_SIZE // 2)
        self.black_button = black_rect

        random_rect = self.random.get_rect()
        random_rect.center = (2*MARGIN + BD_WIDTH + 3 * SQ_SIZE, MARGIN + INFO_HEIGHT // 2 + SQ_SIZE // 2)
        self.rand_button = random_rect

    '''
    Sets all the relevant game variables internally to the starting state
    '''
    def init_game_state(self):
        self.board = board.Board()
        self.hist = [self.board]
        self.hist_ind = 0
        self.engine = engine.Engine()
        self.moves = []

        self.state = MENU
        self.user_is_white = True
        self.from_sq = None
        self.to_sq = None
        self.selecting = False
        self.deselect_next = False
        self.is_flipped = False
        self.white_to_move = True








    '''
    Main draw function. Renders all visual aspects of the game.
    '''
    def draw(self, update=True):
        # Fill the background
        self.screen.blit(self.bg, (0,0))

        self.draw_board()
        self.draw_info()

        if self.state != MENU:
            self.highlight_squares()
            self.draw_pieces()

        if self.state == WIN:
            self.draw_endgame_popup(WIN_MSG)
        elif self.state == LOSE:
            self.draw_endgame_popup(LOSE_MSG)
        elif self.state == STALEMATE:
            self.draw_endgame_popup(STALEMATE_MSG)
        elif self.state == RESIGN:
            self.draw_endgame_popup(RESIGN_MSG)

        if update:
            pygame.display.flip()


    '''
    Draws the static board and labels on the sides
    '''
    def draw_board(self):
        # Draw labels
        for i in range(8):
            j = 7 - i if self.is_flipped else i
            rank = self.board_font.render(RANKS[j], True, GRAY)
            file = self.board_font.render(FILES[j], True, GRAY)

            rank_rect = rank.get_rect()
            rank_rect.center = (MARGIN - OFFSET, MARGIN + i * SQ_SIZE + SQ_SIZE // 2)
            self.screen.blit(rank, rank_rect)
            file_rect = file.get_rect()
            file_rect.center = (MARGIN + i * SQ_SIZE + SQ_SIZE // 2, WIN_HEIGHT - MARGIN + OFFSET)
            self.screen.blit(file, file_rect)

        # Draw squares
        for row in range(8):
            for col in range(8):
                x = SQ_SIZE * col + MARGIN
                y = SQ_SIZE * row + MARGIN

                square = self.dark_sq if (row + col) % 2 != 0 else self.light_sq

                # Create sprite from large board
                square = pygame.Surface.subsurface(square, (col * SQ_SIZE, row * SQ_SIZE, SQ_SIZE, SQ_SIZE))
                self.screen.blit(square, pygame.Rect(x,y, SQ_SIZE, SQ_SIZE))

    '''
    Draw the pieces onto the board. Should occur after board is drawn
    '''
    def draw_pieces(self):
        # Draw pieces. Logic to orient pieces in right direction
        pos = self.board.pos if (not self.is_flipped and self.white_to_move) or (not self.white_to_move and self.is_flipped) else self.board.flip().pos
        if self.is_flipped:
            pos = pos.swapcase()

        for sq, piece in enumerate(pos):
            if piece.isspace() or piece == '.':
                continue
            piece_img = self.pieces[piece]

            # Converting internal board representation to visual representation
            col, row = tools.int_to_vis(sq)

            # If the user has clicked down on a piece, piece should simulate dragging
            if self.dragging and (col, row) == self.from_sq:
                self.screen.blit(piece_img, pygame.Rect(self.x - SQ_SIZE // 2, self.y - SQ_SIZE // 2, SQ_SIZE, SQ_SIZE))
            else:
                x = SQ_SIZE * col + MARGIN
                y = SQ_SIZE * row + MARGIN
                self.screen.blit(piece_img, pygame.Rect(x,y,SQ_SIZE, SQ_SIZE))


    '''
    Highlights all squares on the board
    '''
    def highlight_squares(self):
        # Highlight last move
        if self.hist_ind > 0:
            move = self.moves[self.hist_ind - 1]
            frm, to = move.frm, move.to
            if (not self.is_flipped and self.white_to_move) or (not self.white_to_move and self.is_flipped):
                frm = 119 - frm
                to = 119 - to
            frm = tools.int_to_vis(frm)
            col, row = frm
            self.highlight(col, row, mode="MOVE")

            to = tools.int_to_vis(to)
            col, row = to
            self.highlight(col, row, mode="MOVE")

        # Highlight king if in check
        if self.board.in_check:
            king_pos = self.board.pos.find('K')
            if king_pos < 0:
                print(self.board.pos)
                raise ValueError('Invalid board position reached.')
            if (self.is_flipped or not self.white_to_move) and (self.white_to_move or not self.is_flipped):
                king_pos = 119 - king_pos
            king_pos = tools.int_to_vis(king_pos)
            col, row = king_pos
            self.highlight(col, row, mode="CHECK")


        # When actively clicking on squares
        if self.selecting:
            col, row = self.from_sq

            # Highlight from_sq
            self.highlight(col, row, mode="SEL", border=True)

            # Highlight all possible squares selected piece can move to
            flip = (self.is_flipped or not self.white_to_move) and (self.white_to_move or not self.is_flipped)
            from_sq = tools.vis_to_int(self.from_sq)
            if flip:
                from_sq = 119 - from_sq

            # Only highlight legal moves
            to_squares = []
            for move in self.board.gen_legal_moves():
                if move.frm == from_sq:
                    to_squares.append(move.to)
            for to_sq in to_squares:
                col, row = tools.int_to_vis(to_sq) if not flip else tools.int_to_vis(119 - to_sq)
                if self.board.pos[to_sq] == '.':
                    self.highlight(col, row, mode="EMPTY")
                else:
                    self.highlight(col, row, mode="CAPTURE")


            if self.dragging and MARGIN <= self.x <= BD_WIDTH + MARGIN and MARGIN <= self.y <= BD_HEIGHT + MARGIN:
                col = (self.x - MARGIN) // SQ_SIZE
                row = (self.y - MARGIN) // SQ_SIZE
                if (col, row) != self.from_sq:
                    self.highlight(col, row, mode="SEL", border=True)



    '''
    Highlights a square on the board for a specific purpose
    '''
    def highlight(self, col, row, mode="SEL", border=False, thickness=3):
        x = SQ_SIZE * col + MARGIN
        y = SQ_SIZE * row + MARGIN

        # Clear existing highlight (if any)
        sq = self.dark_sq if (col + row) % 2 != 0 else self.light_sq
        sq = pygame.Surface.subsurface(sq, (col * SQ_SIZE, row * SQ_SIZE, SQ_SIZE, SQ_SIZE))
        self.screen.blit(sq, pygame.Rect(col * SQ_SIZE + MARGIN, row * SQ_SIZE + MARGIN, SQ_SIZE, SQ_SIZE))

        shading = pygame.Surface((SQ_SIZE, SQ_SIZE), pygame.SRCALPHA)
        if mode == "MOVE":
            shading.fill(YELLOW_T)
        elif mode == "CHECK":
            shading.fill(RED_T)
        elif mode == "SEL":
            shading.fill(DARK_GREEN_T)
        elif mode == "EMPTY":
            circ = pygame.draw.circle(shading, DARK_GREEN_T, (SQ_SIZE//2, SQ_SIZE//2), SQ_SIZE//8)
        elif mode == "CAPTURE":
            shading.fill(DARK_GREEN_T)
        self.screen.blit(shading, (x,y))
        if border:
            pygame.draw.rect(self.screen, WHITE, (x,y, SQ_SIZE, SQ_SIZE), thickness, border_radius=1)


    '''
    Draws the info board to the right of the board.
    '''
    def draw_info(self):
        # Draw
        pygame.draw.rect(self.screen, LIGHT_GRAY, (2*MARGIN + BD_WIDTH, MARGIN, INFO_WIDTH, INFO_HEIGHT))
        move_num_width = SQ_SIZE // 2
        move_cell_height = SQ_SIZE // 3
        move_cell_width = SQ_SIZE

        # Menu option
        if self.state == MENU:
            # Write text
            text = self.info_font.render("Play as:", True, BLACK)
            rect = text.get_rect()
            x = 2*MARGIN + BD_WIDTH + INFO_WIDTH // 2
            y = MARGIN + INFO_HEIGHT // 2 - SQ_SIZE
            rect.center = (x + move_num_width // 2, y + move_cell_height // 2)
            self.screen.blit(text, rect)

            # Draw buttons
            self.screen.blit(self.analysis, self.analysis_button)
            self.screen.blit(self.pieces['K'], self.white_button)
            self.screen.blit(self.random, self.rand_button)
            self.screen.blit(self.pieces['k'], self.black_button)

        # While playing or analysis
        elif self.state in (PLAYING, ANALYSIS):
            # Draw moves
            for i, move in enumerate(self.moves):
                move_num = i // 2 + 1
                if i % 2 == 0:
                    # Move number
                    num = self.moves_font.render(str(move_num) + '.', True, BLACK)
                    num_rect = num.get_rect()
                    x = 2*MARGIN + BD_WIDTH
                    y = MARGIN + (move_num - 1)*move_cell_height
                    #if self.state == ANALYSIS: y += ENGINE_HEIGHT
                    num_rect.center = (x + move_num_width // 2, y + move_cell_height // 2)
                    #pygame.draw.rect(self.screen, GRAY, (x,y, move_num_width, move_cell_height))
                    self.screen.blit(num, num_rect)

                    move = self.moves_font.render(tools.to_uci(move), True, BLACK)
                    rect = move.get_rect()
                    x = 2*MARGIN + BD_WIDTH + move_num_width
                    y = MARGIN + (move_num - 1)*move_cell_height
                    #if self.state == ANALYSIS: y += ENGINE_HEIGHT
                    rect.center = (x + move_cell_width // 2, y + move_cell_height // 2)
                    #pygame.draw.rect(self.screen, WHITE, (x,y, move_cell_width, move_cell_height))
                    self.screen.blit(move, rect)
                else:
                    move = self.moves_font.render(tools.to_uci(tools.flip_move(move)), True, BLACK)
                    rect = move.get_rect()
                    x = 2*MARGIN + BD_WIDTH + move_num_width + move_cell_width
                    y = MARGIN + (move_num - 1)*move_cell_height
                    #if self.state == ANALYSIS: y += ENGINE_HEIGHT
                    rect.center = (x + move_cell_width // 2, y + move_cell_height // 2)
                    #pygame.draw.rect(self.screen, WHITE, (x,y, move_cell_width, move_cell_height))
                    self.screen.blit(move, rect)

            # Draw in-game icons
            self.screen.blit(self.flip, self.flip_button)
            if self.state == PLAYING:
                self.screen.blit(self.resign, self.resign_button)

        # Game ends
        elif self.state in OVER:
            self.screen.blit(self.play_again, self.play_again_button)

    '''
    Draw endgame pop-up
    '''
    def draw_endgame_popup(self, text):
        text = self.info_font.render(text, True, BLACK)
        rect = text.get_rect()
        x = MARGIN + BD_WIDTH // 2
        y = MARGIN + BD_HEIGHT // 2
        rect.center = (x,y)
        pygame.draw.rect(self.screen, WHITE, rect.inflate(rect.width / 2, rect.height / 2))
        self.screen.blit(text, rect)









    '''
    Animates a move in the GUI
    '''
    def animate_move(self, start, end, fps=5):
        # Animate move (only if piece was not dragged to destination square)
        x1, y1 = start
        x2, y2 = end
        dist = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        frames = round(dist * fps)

        # Previous square
        from_sq = self.dark_sq if (x1 + y1) % 2 != 0 else self.light_sq
        from_sq = pygame.Surface.subsurface(from_sq, (x1 * SQ_SIZE, y1 * SQ_SIZE, SQ_SIZE, SQ_SIZE))

        # Piece
        pos = self.board.pos if (not self.is_flipped and self.white_to_move) or (not self.white_to_move and self.is_flipped) else self.board.flip().pos
        if self.is_flipped:
            pos = pos.swapcase()
        piece = pos[tools.vis_to_int(start)]

        # Check if move was castling
        castling = False
        X1, X2 = 0, 2
        if (piece == 'K' or piece == 'k') and abs(x2 - x1) == 2:
            castling = True
            if x2 > x1:
                X1, X2 = 7, 5
                if x2 == X2:
                    X2 -= 1
            elif x2 == X2:
                X2 += 1
            rook = pos[tools.vis_to_int((X1, y1))]
            rook_sq = self.dark_sq if (X1 + y1) % 2 != 0 else self.light_sq
            rook_sq = pygame.Surface.subsurface(rook_sq, (X1 * SQ_SIZE, y1 * SQ_SIZE, SQ_SIZE, SQ_SIZE))
            print(rook)

        for i in range(frames):
            coord = ( (x1 + i * (x2 - x1)/ frames) * SQ_SIZE + MARGIN, (y1 + i * (y2 - y1)/ frames) * SQ_SIZE + MARGIN)

            # Re-draw board
            self.draw_board()

            # Add highlighting to to_sq
            self.highlight(x2, y2, mode="MOVE")

            # Add pieces
            self.draw_pieces()

            # Erase piece from from_sq and highlight it
            self.screen.blit(from_sq, pygame.Rect(x1 * SQ_SIZE + MARGIN, y1 * SQ_SIZE + MARGIN, SQ_SIZE, SQ_SIZE))
            self.highlight(x1, y1, mode="MOVE")

            # Draw moving piece
            if piece not in self.pieces:
                raise ValueError(piece, " not a valid piece!")
            self.screen.blit(self.pieces[piece], coord)

            if castling:
                rook_coord = ( (X1 + i * (X2 - X1)/ frames) * SQ_SIZE + MARGIN, y1 * SQ_SIZE + MARGIN)
                self.screen.blit(rook_sq, pygame.Rect(X1 * SQ_SIZE + MARGIN, y1 * SQ_SIZE + MARGIN, SQ_SIZE, SQ_SIZE))
                self.screen.blit(self.pieces[rook], rook_coord)

            pygame.display.flip()
            self.clock.tick(FPS)

    '''
    Handles all internal state changes when a move is made. (i.e. in Board). If move is passed, then a move was made
    and the board will be updated. Otherwise, a move was not yet made and the board will advance in the history if
    possible.
    '''
    def make_move(self, move=None):
        if move:
            # Update internal board
            self.hist_ind = len(self.hist)
            self.board = self.hist[self.hist_ind-1].move(move)
            self.moves.append(move)
            self.hist.append(self.board)
            self.white_to_move = not self.white_to_move
            self.from_sq = None
            self.selecting = False

            # Checks whether game is over
            if self.board.checkmate():
                print("Checkmate!")
                if (self.white_to_move and self.user_is_white) or (not self.white_to_move and not self.user_is_white):
                    print("You lose!")
                    self.state = LOSE
                else:
                    print("You win!")
                    self.state = WIN
            if self.board.stalemate():
                print("Stalemate!")
                self.state = STALEMATE
        else:
            if self.hist_ind < len(self.hist) - 1:
                self.hist_ind += 1
                self.white_to_move = not self.white_to_move
            self.board = self.hist[self.hist_ind]
            move = self.moves[self.hist_ind - 1]

        # Sound
        if move.is_capture:
            pygame.mixer.Sound.play(self.capture_fx)
        elif move.is_castle:
            print("Castling sound")
            # No castling sound yet
        else:
            pygame.mixer.Sound.play(self.move_fx)


    '''
    Goes backward in history.
    '''
    def unmake_move(self):
        pygame.mixer.Sound.play(self.move_fx)
        if self.hist_ind > 0:
            self.hist_ind -= 1
            self.white_to_move = not self.white_to_move
        self.board = self.hist[self.hist_ind]








    '''
    Main loop for rendering GUI
    '''
    def run(self):
        running = True
        while running:
            self.x, self.y = pygame.mouse.get_pos()

            # Check if engine's turn to make a move. Hacky way for now - white_to_move variable is changed when in hist
            if self.state == PLAYING and ((self.user_is_white and len(self.hist) % 2 == 0) or (not self.user_is_white and len(self.hist) % 2 == 1)):
                print("Engine is calculating...")
                move, score = self.engine.search(self.board)
                # Bring to present position internally (not visually, since we are not updating)
                while self.hist_ind < len(self.hist) - 1:
                    self.make_move()

                vis_move = move if (not self.is_flipped and self.white_to_move) or (not self.white_to_move and self.is_flipped) else tools.flip_move(move)
                self.animate_move(tools.int_to_vis(vis_move.frm), tools.int_to_vis(vis_move.to))
                self.make_move(move)
                print("Checks: ", self.board.checks)
                print("Pins: ", self.board.pins)
                print("Score: ", -score if self.user_is_white else score)
                print("-----------------")

            # Check for human moves
            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.state == MENU:
                        if self.analysis_button.collidepoint((self.x, self.y)):
                            self.user_is_white = True
                            self.is_flipped = False
                            self.state = ANALYSIS
                            print("Analysis mode!")
                        elif self.white_button.collidepoint((self.x, self.y)):
                            self.user_is_white = True
                            self.is_flipped = False
                            self.state = PLAYING
                            pygame.mixer.Sound.play(self.start_game_fx)
                            print("Playing as white!")
                        elif self.rand_button.collidepoint((self.x, self.y)):
                            rand = random.uniform(0, 1)
                            print(rand)
                            if rand < 0.5:
                                self.user_is_white = True
                                self.is_flipped = False
                                print("Playing as white!")
                            else:
                                self.user_is_white = False
                                self.is_flipped = True
                                print("Playing as black!")
                            self.state = PLAYING
                            pygame.mixer.Sound.play(self.start_game_fx)
                        elif self.black_button.collidepoint((self.x, self.y)):
                            self.user_is_white = False
                            self.is_flipped = True
                            self.state = PLAYING
                            pygame.mixer.Sound.play(self.start_game_fx)
                            print("Playing as black!")
                    if self.state in OVER:
                        if self.play_again_button.collidepoint((self.x, self.y)):
                            self.init_game_state()


                    elif self.state in (PLAYING, ANALYSIS):
                        if self.flip_button.collidepoint((self.x, self.y)):
                            self.is_flipped = not self.is_flipped
                            print("Flipped board!")
                        if self.state == PLAYING and self.resign_button.collidepoint((self.x, self.y)):
                            print("Resigned!")
                            self.state = RESIGN

                        # Game is at current position in history, and click within board bounds
                        elif self.hist_ind == len(self.hist) - 1 and MARGIN <= self.x <= BD_WIDTH + MARGIN and MARGIN <= self.y <= BD_HEIGHT + MARGIN:
                            #print("Clicked inside board!")

                            # Coordinates of square clicked
                            sq_x = (self.x - MARGIN) // SQ_SIZE
                            sq_y = (self.y - MARGIN) // SQ_SIZE
                            from_sq = (sq_x, sq_y)

                            # Check if clicked square is part of any valid move
                            pos = tools.vis_to_int(from_sq)
                            if (self.is_flipped or not self.white_to_move) and (self.white_to_move or not self.is_flipped):
                                pos = 119 - pos
                            valid_selection = False
                            for move in self.board.gen_legal_moves():
                                if move.frm == pos:
                                    valid_selection = True

                            # If not currently selecting and square is not part of any valid move, we are in selecting mode
                            if not self.selecting and valid_selection:
                                self.from_sq = from_sq
                                self.selecting = True
                                self.dragging = True
                                #print("Selecting")

                            # If we are in selecting mode, the square we are over is the to_square for the move
                            elif self.selecting:
                                #print("Choosing square to move to!")
                                self.to_sq = (sq_x, sq_y)
                                x, y = tools.vis_to_int(self.from_sq), tools.vis_to_int(self.to_sq)
                                # This capture detection needs to be optimized
                                capture = self.board.pos[y].islower() or (self.board.pos[x] == 'P' and y-x in (board.U + board.L, board.U + board.R))
                                castle = self.board.pos[x] == 'K' and abs(y - x) == 2
                                move = board.Move(x, y, capture, castle)
                                move = move if (not self.is_flipped and self.white_to_move) or (not self.white_to_move and self.is_flipped) else tools.flip_move(move)
                                #print("Proposed move: ", self.from_sq, self.to_sq)
                                if move in self.board.gen_legal_moves():
                                    print("Valid move!")
                                    self.animate_move(self.from_sq, self.to_sq)
                                    self.make_move(move)
                                    print("Checks: ", self.board.checks)
                                    print("Pins: ", self.board.pins)
                                    print("Score: ", eval.evaluate(self.board) if self.white_to_move else -eval.evaluate(self.board))
                                    print("-----------------")
                                    self.dragging = False
                                else:
                                    #print("Invalid move chosen while selecting. Deselecting if released incorrectly.")
                                    self.deselect_next = True
                                    self.dragging = True
                elif event.type == pygame.MOUSEBUTTONUP:
                    self.dragging = False
                    if self.state in (PLAYING, ANALYSIS) and self.hist_ind == len(self.hist) - 1:
                        if self.from_sq and MARGIN <= self.x <= BD_WIDTH + MARGIN and MARGIN <= self.y <= BD_HEIGHT + MARGIN:
                            #print("Released inside board!")

                            # Coordinates of square clicked
                            sq_x = (self.x - MARGIN) // SQ_SIZE
                            sq_y = (self.y - MARGIN) // SQ_SIZE
                            self.to_sq = (sq_x, sq_y)
                            x, y = tools.vis_to_int(self.from_sq), tools.vis_to_int(self.to_sq)
                            capture = self.board.pos[y].islower() or (self.board.pos[x] == 'P' and y-x in (board.U + board.L, board.U + board.R))
                            castle = self.board.pos[x] == 'K' and abs(y - x) == 2
                            move = board.Move(x, y, capture, castle)
                            move = move if (not self.is_flipped and self.white_to_move) or (not self.white_to_move and self.is_flipped) else tools.flip_move(move)
                            #print("Proposed move: ", self.from_sq, self.to_sq)
                            if move in self.board.gen_legal_moves():
                                print("Valid move!")
                                self.make_move(move)
                                print("Checks: ", self.board.checks)
                                print("Pins: ", self.board.pins)
                                print("Score: ", eval.evaluate(self.board) if self.white_to_move else -eval.evaluate(self.board))
                                print("-----------------")
                            else:
                                print("Invalid move!")
                                if self.deselect_next:
                                    #print("Deselecting")
                                    self.selecting = False
                                    self.from_sq = None
                                    self.deselect_next = False

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        self.unmake_move()

                    if event.key == pygame.K_RIGHT:
                        self.make_move()

                elif event.type == pygame.QUIT:
                    running = False

            # Draw screen
            self.draw()

            # Delay
            self.clock.tick(FPS)

        pygame.quit()



if __name__ == '__main__':
    Game().run()
