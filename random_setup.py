import random
import math

# Constants
NUM_BALLS = random.randint(2, 5)
NUM_FRAMES = random.randint(5, 10)

# List to store the frames [[frame1], [frame2], ...], frame ex. [ball1, ball2, ...], ball ex. [x, y, vx, vy, r]
frames = []
board = []

def random_board():
    board = []  # list of vertex ([[(x1, y1), (x2, y2)], [(x3, y3), (x4, y4)], ...])

    board = [
        [(0, 0), (1, 0)],  # bottom edge
        [(1, 0), (1, 1)],  # right edge
        [(1, 1), (0, 1)],  # top edge
        [(0, 1), (0, 0)],  # left edge
    ]

    return board

def initialize_frame():
    frame = []
    for _ in range(NUM_BALLS):
        x = random.uniform(0, 1)
        y = random.uniform(0, 1)
        vx = random.uniform(-1, 1)
        vy = random.uniform(-1, 1)
        r = random.uniform(0.5, 2)
        ball_info = [x, y, vx, vy, r]
        frame.append(ball_info)
    return frame

def new_frame(last_frame):
    new_frame = []
    for ball in last_frame:
        r = ball[4]
        x = random.uniform(r/100, 1 - r/100)
        y = random.uniform(r/100, 1 - r/100)
        vx = ball[2] + random.uniform(-0.5, 0.5)
        vy = ball[3] + random.uniform(-0.5, 0.5)
        new_frame.append([x, y, vx, vy, r])
    return new_frame

def save_to_file(_board, _frames, filename='data.txt'):
    with open(filename, 'w') as file:
        board_str = ' '.join([' '.join(map(str, point)) for edge in _board for point in edge])
        file.write(board_str + '\n')
        for frame in _frames:
            frame_str = ' '.join([' '.join(map(str, ball)) for ball in frame])
            file.write(frame_str + '\n')

board = random_board()
frames.append(initialize_frame())
for _ in range(NUM_FRAMES - 1):
    frames.append(new_frame(frames[-1]))

save_to_file(board, frames)
