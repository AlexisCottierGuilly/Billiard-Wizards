import matplotlib.pyplot as plt
import numpy as np

import matplotlib.animation as animation
import matplotlib.patches as patches

"""
Instructions.
Create a rectangle (board viewed from the top, and some billiard balls)
To place the balls, we need to read the data.txt file
The data.txt file contains the following information:
1. The first line is the board information (for now, a rectangle)
    The data is stored like this: x1 y1 x2 y2 x3 y3 x4 y4
    - In the example, 2 vertex are given, so 4 points are given
2. Each other line is a simulation state
3. In each line, we get informations about all the balls in the frame
    - X, Y, Vx, Vy, R
    These values are separated by a space, and ball infos are separated by a space too

By reading these frames, we need to animate the simulation in a 2d matplotlib figure.
1. Create a function that will read the data.txt file and return a list of frames.
2. Assign a color for each ball index.
3. Do something so the animation runs in matplotlib (and loop)
"""

BOARD_SIZE = (100, 100)

SUB_FRAMES = 60
ANIMATION_SPEED = 1


def read_data(file_path):
    frames = []
    board = [] # format: [[(x1, y1), (x2, y2)], [(x3, y3), (x4, y4)], ...] # so a list of vertices
    with open(file_path, 'r') as file:
        i = 0
        for line in file:
            if line == "":
                continue
            if i == 0:
                data = line.strip().split(' ')
                for j in range(0, len(data), 2):
                    x = float(data[j])
                    y = float(data[j+1])
                    board.append((x, y))
            else:
                frame = []
                data = line.strip().split(' ')
                for i in range(0, len(data), 5):
                    x = float(data[i])
                    y = float(data[i+1])
                    vx = float(data[i+2])
                    vy = float(data[i+3])
                    r = float(data[i+4])
                    frame.append((x, y, vx, vy, r))
                frames.append(frame)
            i += 1
    return board, frames

def get_ball_color(i, max_i):
    # Assign a color to each ball index, forming a color gradient
    color = plt.cm.viridis(i / max_i)  # Using viridis colormap
    return color

def create_trail_items(ball, ax):
    color = plt.cm.viridis(0)  # Default color for the trail items
    r = ball.get_radius()
    tail = patches.Ellipse((0, 0), r * 2, r * 2, color=color, alpha=0)
    ax.add_patch(tail)
    # Create a list of the shapes
    shapes = [tail]
    return shapes

def update_trail_items(items, x, y, vx, vy, r, color):
    # Update the position of the trail items
    x = x * BOARD_SIZE[0]
    y = y * BOARD_SIZE[1]
    tail_scale = BOARD_SIZE[0] / 20, BOARD_SIZE[1] / 20

    line_width = r

    # Find tail angle to ajust the line after
    angle = np.arctan2(vy, vx)

    start = x, y
    length = np.sqrt(vx**2 + vy**2) * (BOARD_SIZE[0] / 35) * r + r
    end = x + (length / 2) * np.cos(angle), y + (length / 2) * np.sin(angle)

    for item in items:
        if isinstance(item, patches.Ellipse):
            item.set_alpha(0.25)
            item.set_center(end)
            item.set_height(line_width)
            item.set_width(length)
            item.set_color(color)
            item.set_angle(np.degrees(angle))

def get_board(board_vertices, size=(100, 100)):
    # Adapt the vertices to get the good size
    # The board an be any shape
    # The size is the size of the board in the figure (the min-max in x and min-max in y)

    # The board is a polygon, so we need to scale the vertices to fit the size
    
    min_x = min([v[0] for v in board_vertices])
    max_x = max([v[0] for v in board_vertices])
    min_y = min([v[1] for v in board_vertices])
    max_y = max([v[1] for v in board_vertices])
    # setup an offset to deal with negative coords (min should be 0 and max 1)
    offset_x = -min_x
    offset_y = -min_y
    min_x, max_x, min_y, max_y = min_x + offset_x, max_x + offset_x, min_y + offset_y, max_y + offset_y
    scale_x = size[0] / (max_x - min_x)
    scale_y = size[1] / (max_y - min_y)
    scale_multiplier = (scale_x, scale_y)
    # Scale the vertices
    scaled_vertices = [((v[0] + offset_x) * scale_x, (v[1] + offset_y) * scale_y) for v in board_vertices]
    
    # create polygon
    polygon = plt.Polygon(scaled_vertices, closed=True, edgecolor='white', facecolor='none')
    return polygon

"""
This is the plan :)
1. Get the current and next positions, radius, and velocity of each ball
2. Calculate the distance between the current and next positions
3. Calculate the direction of the movement (dx, dy)
4. Calculate the speed of the ball (magnitude of the velocity vector)
5. Calculate the time it takes to reach the next position (distance / speed)
6. Calculate the number of frames needed to reach the next position (time / interval)
7. Calculate the step size for each frame (dx / num_frames, dy / num_frames)
8. Update the ball position in each frame using the step size
9. Use the FuncAnimation to create the animation
10. Make sure to loop the animation
"""

def update(frame1, frame2, percentage):
    # using NB_OF_TRAIL_ELEMENTS, loop in a list of [(ball, trail_items)]

    modified_patches = []
    # fill it with the shape above
    nb_balls = len(ball_patches) / (NB_OF_TRAIL_ELEMENTS + 1)
    elems_per_ball = NB_OF_TRAIL_ELEMENTS + 1
    for i in range(int(nb_balls)):
        modified_patches.append((ball_patches[i * elems_per_ball], ball_patches[i * elems_per_ball + 1:i * elems_per_ball + elems_per_ball]))

    for i, ball_info in enumerate(modified_patches):
        ball = ball_info[0]
        trail_items = ball_info[1]
        x1, y1, vx1, vy1, r1 = frame1[i]
        x2, y2, vx2, vy2, r2 = frame2[i]

        # Interpolate the position, radius and velocities of the ball
        x = x1 + percentage * (x2 - x1)
        y = y1 + percentage * (y2 - y1)
        r = r1 + percentage * (r2 - r1)
        vx = vx1 + percentage * (vx2 - vx1)
        vy = vy1 + percentage * (vy2 - vy1)

        ball.set_center((x * BOARD_SIZE[0], y * BOARD_SIZE[1]))
        ball.set_radius(r)
        ball.set_alpha(1)

        speed = np.sqrt(vx**2 + vy**2)
        color = plt.cm.viridis(speed) / np.sqrt(2)
        ball.set_color(color)

        # Update trail elements
        update_trail_items(trail_items, x, y, vx, vy, r, color)

    return ball_patches

def animate(i):
    # Get the current and next frames
    # The i can be somewere between two frames (see SUB_FRAMES)
    frame1_index = i // SUB_FRAMES
    frame2_index = (i // SUB_FRAMES + 1) % len(frames)
    percentage = (i % SUB_FRAMES) / SUB_FRAMES

    update(frames[frame1_index], frames[frame2_index], percentage)
    return ball_patches

balls = []
ball_colors = []

board_vertices, frames = read_data('data.txt')
num_balls = len(frames[0])
for i in range(num_balls):
    ball_colors.append(get_ball_color(i, num_balls))

# IN DARK MODE

plt.style.use('dark_background')
fig, ax = plt.subplots()
ax.set_xlim(0, BOARD_SIZE[0])
ax.set_ylim(0, BOARD_SIZE[1])
ax.set_aspect('equal')
ax.set_facecolor('black')
ax.set_xticks([])
ax.set_yticks([])
ax.set_title('Billiard Simulation', color='white')
ax.set_xlabel('X-axis', color='white')
ax.set_ylabel('Y-axis', color='white')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_visible(False)
ax.spines['bottom'].set_visible(False)

# Create a rectangle to represent the board
#board = plt.Rectangle((0, 0), 100, 100, linewidth=1, edgecolor='white', facecolor='none')
#ax.add_patch(board)

board = get_board(board_vertices, size=BOARD_SIZE)
ax.add_patch(board)

# Create a list to hold the ball patches
ball_patches = []
NB_OF_TRAIL_ELEMENTS = 1
for i in range(num_balls):
    ball = plt.Circle((0, 0), 1, color=ball_colors[i])
    ax.add_patch(ball)
    trail = create_trail_items(ball, ax)
    ball_patches.append(ball)
    for t in trail:
        ball_patches.append(t)

# Create the animation and update it
interval = 1000 / 60 / ANIMATION_SPEED
number_of_frames = len(frames) * SUB_FRAMES
ani = animation.FuncAnimation(fig, animate, frames=number_of_frames, interval=interval, blit=True)
ani.event_source.start()

plt.show()
