import os
import re
import glob
import argparse

import imageio
import numpy as np
from PIL import Image as img

columns = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
rows = ['1', '2', '3', '4', '5', '6', '7', '8']

bk = img.open('./images/bk.png')
bq = img.open('./images/bq.png')
bb = img.open('./images/bb.png')
bn = img.open('./images/bn.png')
br = img.open('./images/br.png')
bp = img.open('./images/bp.png')

wk = img.open('./images/wk.png')
wq = img.open('./images/wq.png')
wb = img.open('./images/wb.png')
wn = img.open('./images/wn.png')
wr = img.open('./images/wr.png')
wp = img.open('./images/wp.png')

def get_moves_from_pgn(file_path):
    with open(file_path) as pgn:
        data = pgn.read()
        data = re.sub(r'\{.*?\}', '', data) # Removes pgn comments
        moves = re.findall(r'[a-h]x?[a-h]?[1-8]=?[BKNRQ]?|O-O-?O?|[BKNRQ][a-h1-8]?[a-h1-8]?x?[a-h][1-8]',data)
        return [move.replace('x','') for move in moves]


def coordinates_of_square(square):
    c = columns.index(square[0])
    r = 7 - rows.index(square[1])
    if reverse:
        return ((7 - c) * 60, (7 - r) * 60)
    else:
        return (c * 60, r * 60)


def clear(crd):
    if (crd[0] + crd[1]) % 120 == 0:
        board_image.paste(white_square, crd, white_square)
    else:
        board_image.paste(black_square, crd, black_square)


def update(move, is_white_turn):
    if 'O' in move:
        castle(move, is_white_turn)

    elif '=' in move:
        promotion(move, is_white_turn)

    else:
        destination_square = move[-2:]
        if (move.islower()):
            piece_type = ('w' if is_white_turn else 'b') + 'p'
            coming_square = find_pawn(move, is_white_turn)
        else:
            piece_type = ('w' if is_white_turn else 'b') + move[0].lower()
            coming_square = find_non_pawn(move, destination_square, piece_type)
        update_board(coming_square, destination_square, piece_type)

        to = coordinates_of_square(destination_square)
        frm = coordinates_of_square(coming_square)

        clear(frm)
        if board[destination_square] != '':
            clear(to)

        exec('board_image.paste({0},to,{0})'.format(piece_type))


def check_knight_move(sqr1, sqr2):
    v = abs(columns.index(sqr1[0]) - columns.index(sqr2[0]))
    if v == 1:
        return abs(rows.index(sqr1[1]) - rows.index(sqr2[1])) == 2
    elif v == 2:
        return abs(rows.index(sqr1[1]) - rows.index(sqr2[1])) == 1
    return False


def check_line(sqr1, sqr2):
    c1 = sqr1[0]
    c2 = sqr2[0]
    r1 = int(sqr1[1])
    r2 = int(sqr2[1])
    if r1 == r2:
        i1 = columns.index(c1)
        i2 = columns.index(c2)
        return all(board[columns[i] + str(r1)] == '' for i in range(min(i1, i2) + 1, max(i1, i2)))
    elif c1 == c2:
        return all(board[c1 + str(i)] == '' for i in range(min(r1, r2) + 1, max(r1, r2)))
    return False


def check_diagonal(sqr1, sqr2):
    c1 = columns.index(sqr1[0])
    c2 = columns.index(sqr2[0])
    r1 = int(sqr1[1])
    r2 = int(sqr2[1])
    if abs(c1 - c2) == abs(r1 - r2):
        if c1 > c2 and r1 > r2 or c2 > c1 and r2 > r1:
            min_c = min(c1, c2)
            min_r = min(r1, r2)
            return all(board[columns[min_c+i] + str(min_r + i)] == '' for i in range(1, abs(c1-c2)))

        elif c1 > c2 and r2 > r1:
            return all(board[columns[c2 + i] + str(r2 - i)] == '' for i in range(1, c1 - c2))

        else:
            return all(board[columns[c2 - i] + str(r2 + i)] == '' for i in range(1, c2 - c1))
    return False


def update_board(frm, to, piece_type):
    board[frm] = ''
    board[to] = piece_type


def find_non_pawn(move, to, piece):
    if len(move) == 5:
        return move[1:3]

    p = piece[1]
    indicator = '' if len(move) == 3 else move[1]

    if p == 'r':
        return next(sq for sq, pt in board.items() if pt == piece and indicator in sq and check_line(sq, to))
    elif p == 'b':
        return next(sq for sq, pt in board.items() if pt == piece and indicator in sq and check_diagonal(sq, to))
    elif p == 'n':
        return next(sq for sq, pt in board.items() if pt == piece and indicator in sq and check_knight_move(sq, to))
    else:
        return next(sq for sq, pt in board.items() if pt == piece and indicator in sq and (check_line(sq, to) or check_diagonal(sq, to)))


def find_pawn(move, is_white_turn):
    piece_type = 'wp' if is_white_turn else 'bp'
    c = move[-2]
    r = int(move[-1])

    if len(move) == 2:
        if is_white_turn:
            comes_from = c + next(str(i) for i in range(r, 0, -1) if board[c + str(i)] == piece_type)
        else:
            comes_from = c + next(str(i) for i in range(r, 9) if board[c + str(i)] == piece_type)
    else:
        if board[move[-2:]] != '':
            if is_white_turn:
                comes_from = move[0] + str(r - 1)
            else:
                comes_from = move[0] + str(r + 1)
        # En Passant
        else:
            if is_white_turn:
                next_pawn_square = c + str(r - 1)
            else:
                next_pawn_square = c + str(r + 1)

            clear(coordinates_of_square(next_pawn_square))
            board[next_pawn_square] = ''
            comes_from = move[0] + next_pawn_square[-1]

    return comes_from


def castle(move, is_white_turn):
    row = '1' if is_white_turn else '8'
    t = 'w' if is_white_turn else 'b'
    k = 'e' + row
    if move.count('O') == 2:
        r = 'h' + row
        k_to = 'g' + row
        r_to = 'f' + row
    else:
        r = 'a' + row
        k_to = 'c' + row
        r_to = 'd' + row

    update_board(k, k_to, t + 'k')
    update_board(r, r_to, t + 'r')

    clear(coordinates_of_square(r))
    clear(coordinates_of_square(k))

    exec('board_image.paste({0},coordinates_of_square({1}),{0})'.format(t + 'k', 'k_to'))
    exec('board_image.paste({0},coordinates_of_square({1}),{0})'.format(t + 'r', 'r_to'))


def promotion(move, is_white_turn):
    piece_type = 'w' + move[-1].lower() if is_white_turn else 'b' + move[-1].lower()

    if is_white_turn:
        frm = move[0] + "7"
    else:
        frm = move[0] + "2"

    update_board(frm, move[-4:-2], piece_type)

    to = coordinates_of_square(move[-4:-2])

    clear(coordinates_of_square(frm))
    if len(move) == 5:
        clear(to)

    exec('board_image.paste({0},to,{0})'.format(piece_type))


def create_gif(file_name, out_name, duration, output_dir):
    global board
    board =  {'a8': 'br', 'b8': 'bn', 'c8': 'bb', 'd8': 'bq', 'e8': 'bk', 'f8': 'bb', 'g8': 'bn', 'h8': 'br',
              'a7': 'bp', 'b7': 'bp', 'c7': 'bp', 'd7': 'bp', 'e7': 'bp', 'f7': 'bp', 'g7': 'bp', 'h7': 'bp',
              'a6': '', 'b6': '', 'c6': '', 'd6': '', 'e6': '', 'f6': '', 'g6': '', 'h6': '',
              'a5': '', 'b5': '', 'c5': '', 'd5': '', 'e5': '', 'f5': '', 'g5': '', 'h5': '',
              'a4': '', 'b4': '', 'c4': '', 'd4': '', 'e4': '', 'f4': '', 'g4': '', 'h4': '',
              'a3': '', 'b3': '', 'c3': '', 'd3': '', 'e3': '', 'f3': '', 'g3': '', 'h3': '',
              'a2': 'wp', 'b2': 'wp', 'c2': 'wp', 'd2': 'wp', 'e2': 'wp', 'f2': 'wp', 'g2': 'wp', 'h2': 'wp',
              'a1': 'wr', 'b1': 'wn', 'c1': 'wb', 'd1': 'wq', 'e1': 'wk', 'f1': 'wb', 'g1': 'wn', 'h1': 'wr'}

    images = [np.array(board_image)]
    moves = get_moves_from_pgn(file_name)

    for i,move in enumerate(moves):
        update(move, (i + 1) % 2)
        images.append(np.array(board_image))

    for i in range(3):
        images.append(np.array(board_image))

    imageio.mimsave(output_dir + '/' + out_name, images, duration=duration)


def process_file(pgn, duration, output_dir):
    basename = os.path.basename(pgn)
    name = basename[:-4] + '.gif'
    if name in os.listdir('.'):
        print("gif with name %s already exists." % name)
    else:
        print('Creating ' + name, end='.... ')
        create_gif(pgn, name, duration, output_dir)
        print('done')


def generate_board():
    global board_image
    board_image = img.new('RGB', (480, 480))

    for i in range(0, 480, 60):
        for j in range(0, 480, 60):
            clear((i, j))

    for i in range(0, 8):
        if reverse:
            board_image.paste(wp, (60 * i, 60), wp)
            board_image.paste(bp, (60 * i, 360), bp)
        else:
            board_image.paste(bp, (60 * i, 60), bp)
            board_image.paste(wp, (60 * i, 360), wp)

    for i,p in enumerate(['r', 'n', 'b']):
        if reverse:
            exec("board_image.paste(w{0}, ({1}, 0), w{0})".format(p, i * 60))
            exec("board_image.paste(b{0}, ({1}, 420), b{0})".format(p, 420 - i * 60))
            exec("board_image.paste(b{0}, ({1}, 420), b{0})".format(p, i * 60))
            exec("board_image.paste(w{0}, ({1}, 0), w{0})".format(p, 420 - i * 60))
        else:
            exec("board_image.paste(b{0}, ({1}, 0), b{0})".format(p, i * 60))
            exec("board_image.paste(w{0}, ({1}, 420), w{0})".format(p, 420 - i * 60))
            exec("board_image.paste(w{0}, ({1}, 420), w{0})".format(p, i * 60))
            exec("board_image.paste(b{0}, ({1}, 0), b{0})".format(p, 420 - i * 60))

    if reverse:
        board_image.paste(wk, (180, 0), wk)
        board_image.paste(wq, (240, 0), wq)
        board_image.paste(bk, (180, 420), bk)
        board_image.paste(bq, (240, 420), bq)
    else:
        board_image.paste(wk, (240, 420), wk)
        board_image.paste(wq, (180, 420), wq)
        board_image.paste(bk, (240, 0), bk)
        board_image.paste(bq, (180, 0), bq)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--path', help='Path to the pgn file/folder', default=os.getcwd() + '/')
    parser.add_argument('-d', '--delay', help='Delay between moves in seconds', default=0.4)
    parser.add_argument('-o', '--out', help='Name of the output folder', default=os.getcwd())
    parser.add_argument('-r', '--reverse', help='Reverse board', action='store_true')
    parser.add_argument('--black-square-color', help='Color of black squares in hex', default='#4B7399')
    parser.add_argument('--white-square-color', help='Color of white squares in hex', default='#EAE9D2')
    args = parser.parse_args()

    to_rgb = lambda h:tuple(int(h[i:i+2], 16) for i in (0, 2 ,4))

    global reverse
    reverse = args.reverse

    global white_square
    white_square = img.new('RGBA', (60, 60), to_rgb(args.white_square_color.lstrip('#')))

    global black_square
    black_square = img.new('RGBA', (60, 60), to_rgb(args.black_square_color.lstrip('#')))

    generate_board()

    if os.path.isfile(args.path):
        process_file(args.path, args.delay, args.out)

    elif os.path.isdir(args.path):
        for pgn in glob.glob(args.path + '*.pgn'):
            process_file(pgn, args.delay, args.out)


if __name__ == '__main__':
    main()
