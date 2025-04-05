import random
import math

"""
The objective is to save some random simulation frames (very simply) in
the data.txt file.
The data.txt file contains the following information:
1. The first line is the board information (for now, a rectangle)
    The data is stored like this: x1 y1 x2 y2 x3 y3 x4 y4
    - In the example, 2 vertex are given, so 4 points are given
2. Each other line is a simulation state
3. In each line, we get informations about all the balls in the frame
    - X, Y, Vx, Vy, R
    These values are separated by a space, and ball infos are separated by a space too

So choose a certain random number of balls
Set radius, position and velocity randomly

Generate more frames with random (very random) variations of values
Note that, the positions are always between 0 and 1 (in x and y)

Let's to this!
"""

# Constants
NUM_BALLS = random.randint(2, 5)
NUM_FRAMES = random.randint(5, 10)

frames = [] # List to store the frames [[frame1], [frame2], ...], frame ex. [ball1, ball2, ...], ball ex. [x, y, vx, vy, r]
board = []

def random_board():
    # randomly generate a board with a certain number of points
    # for now, a rectangle
    board = []  # list of vertex ([[(x1, y1), (x2, y2)], [(x3, y3), (x4, y4)], ...])
    # for testing, do a rectangle
    board = [
        [(0, 0), (1, 0)],  # bottom edge
        [(1, 0), (1, 1)],  # right edge
        [(1, 1), (0, 1)],  # top edge
        [(0, 1), (0, 0)],  # left edge
    ]

    # make a hexagon
    board = [
       [(-0.5, -math.sqrt(3)/2), (0.5, -math.sqrt(3)/2)],  # bottom edge
         [(0.5, -math.sqrt(3)/2), (1, 0)],  # right edge
         [(1, 0), (0.5, math.sqrt(3)/2)],  # top edge
         [(0.5, math.sqrt(3)/2), (-0.5, math.sqrt(3)/2)],  # left edge
         [(-0.5, math.sqrt(3)/2), (-1, 0)],  # left edge
         [(-1, 0), (-0.5, -math.sqrt(3)/2)],  # bottom edge
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
    # depending on the speeds of the balls, and ensuring they don't go out of limits,
    # create a new frame with random variations of the last frame
    new_frame = []
    for ball in last_frame:
        r = ball[4]  # radius remains the same
        x = random.uniform(r/100, 1 - r/100)  # random position
        y = random.uniform(r/100, 1 - r/100)
        vx = ball[2] + random.uniform(-0.5, 0.5)  # random variation
        vy = ball[3] + random.uniform(-0.5, 0.5)  # random variation
        new_frame.append([x, y, vx, vy, r])
    return new_frame

def save_to_file(_board, _frames, filename='data.txt'):
    # clear file and write down as explained above
    with open(filename, 'w') as file:
        # write the board information with spaces
        # really random enormous shape (open in the center and no crossings)
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
