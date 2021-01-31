import sys
import tools
import board
import engine
import eval
import re

# WARNING: Deprecated - does not work 

def main():
    bd = board.Board()
    e = engine.Engine()
    bd.score = eval.evaluate(bd)

    line = input('Play as white? (y/n): ')
    while not line in 'yn' or len(line) != 1:
        line = input('Play as white? (y/n): ')
    white = line == 'y'
    sign = 1 if white else -1

    if not white:
        display_pos(bd, white=False, flip=True)
        print('Score: ', -sign * bd.score)
        e_move, score = e.search(bd)
        print('My move: ', tools.to_uci(e_move))
        bd = bd.move(e_move)


    while True:
        # Your move (must be pseudo-legal)
        display_pos(bd, white)
        print('Score: ', sign * bd.score)
        if bd.score < -eval.MATE_LOWER:
            print('You lose!')
            break
        move = input('Your move: ')
        if not white:
            move = tools.flip_uci_move(move)
        while not re.match('([a-h][1-8])'*2, move) or not tools.to_move(move) in bd.gen_moves():
            print('Must be valid move: ')
            for move in bd.gen_moves():
                display_move = tools.to_uci(move) if white else tools.flip_uci_move(tools.to_uci(move))
                print(display_move)
            move = input('Your move: ')
            if not white:
                move = tools.flip_uci_move(move)
        bd = bd.move(tools.to_move(move))


        # Display the effects of our move to us
        display_pos(bd, white, flip=True)
        print('Score: ', -sign * bd.score)
        if bd.score < -eval.MATE_LOWER:
            print('You win!')
            break

        # Engine move
        e_move, score = e.search(bd)
        display_move = tools.to_uci(e_move) if not white else tools.flip_uci_move(tools.to_uci(e_move))
        print('My move: ', display_move)
        bd = bd.move(e_move)


if __name__ == '__main__':
    main()
