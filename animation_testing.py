import matplotlib.pyplot as plt
import numpy as np

import matplotlib.animation as animation
import matplotlib.patches as patches

import matplotlib as mpl
import matplotlib.font_manager as fm

fe = fm.FontEntry(
    fname='Spinnaker-Regular.ttf',
    name='Spinnaker')
fm.fontManager.ttflist.insert(0, fe)
mpl.rcParams['font.family'] = fe.name

BOARD_SIZE = (100, 100)

SUB_FRAMES = 60
ANIMATION_SPEED = 1


def read_data(file_path):
    frames = []
    board = []  # list of vertices
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
                    r = float(data[i+4]) * 1.5
                    frame.append((x, y, vx, vy, r))
                frames.append(frame)
            i += 1
    return board, frames


def get_ball_color(i, max_i):
    color = plt.cm.viridis(i / max_i)
    return color


def create_trail_items(ball, ax):
    color = plt.cm.viridis(0)
    r = ball.get_radius()
    
    # Create an arrow
    arrow_length = r * 2
    arrow_width = r / 2
    arrow = patches.Arrow(0, 0, arrow_length, 0, width=arrow_width, color=color, alpha=0)
    ax.add_patch(arrow)
    shapes = [arrow]
    return shapes


def update_trail_items(items, x, y, vx, vy, r, color):
    x = x * BOARD_SIZE[0]
    y = y * BOARD_SIZE[1]

    line_width = r
    angle = np.arctan2(vy, vx)

    arrow_length = 2 * np.sqrt(vx**2 + vy**2) * (BOARD_SIZE[0] / 35) * r + r
    end = x - (arrow_length / 2) * np.cos(angle), y - (arrow_length / 2) * np.sin(angle)

    for item in items:
        if isinstance(item, patches.Arrow):
            item.set_alpha(0.5)
            item.set_data(x, y, (end[0] - x), (end[1] - y), width=line_width*2)
            item.set_color(color)


def get_board(board_vertices, size=(100, 100)):
    min_x = min([v[0] for v in board_vertices])
    max_x = max([v[0] for v in board_vertices])
    min_y = min([v[1] for v in board_vertices])
    max_y = max([v[1] for v in board_vertices])

    offset_x = -min_x
    offset_y = -min_y
    min_x, max_x, min_y, max_y = min_x + offset_x, max_x + offset_x, min_y + offset_y, max_y + offset_y
    scale_x = size[0] / (max_x - min_x)
    scale_y = size[1] / (max_y - min_y)
    scale_multiplier = (scale_x, scale_y)
    
    scaled_vertices = [((v[0] + offset_x) * scale_x, (v[1] + offset_y) * scale_y) for v in board_vertices]
    
    polygon = plt.Polygon(scaled_vertices, closed=True, edgecolor='white', facecolor='none')
    return polygon


def update(frame1, frame2, percentage):
    modified_patches = []
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

        update_trail_items(trail_items, x, y, vx, vy, r, color)

    return ball_patches


def animate(i):
    frame1_index = i // SUB_FRAMES
    frame2_index = (i // SUB_FRAMES + 1) % len(frames)
    percentage = (i % SUB_FRAMES) / SUB_FRAMES

    update(frames[frame1_index], frames[frame2_index], percentage)
    return ball_patches


def on_press(event):
    global is_paused
    if event.key == ' ':  # la barre d'espace pour la pause/reprise
        if is_paused:
            ani.event_source.start()
            is_paused = False
            print("Reprise de l'animation !")
        else:
            ani.event_source.stop()
            is_paused = True
            print("Animation en pause...")


balls = []
ball_colors = []

is_paused = False

board_vertices, frames = read_data('data.txt')
num_balls = len(frames[0])
for i in range(num_balls):
    ball_colors.append(get_ball_color(i, num_balls))

plt.style.use('dark_background')
fig, ax = plt.subplots()

fig.patch.set_facecolor('#151515')
fig.canvas.mpl_connect('key_press_event', on_press)

ax.set_xlim(-1, BOARD_SIZE[0] + 1)
ax.set_ylim(-1, BOARD_SIZE[1] + 1)
ax.set_aspect('equal')
ax.set_facecolor('black')
ax.set_xticks([])
ax.set_yticks([])
ax.set_title('Billiard Simulation', color='white', fontsize=20)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_visible(False)
ax.spines['bottom'].set_visible(False)

board = get_board(board_vertices, size=BOARD_SIZE)
ax.add_patch(board)

# Pause/Play button at the bottom right of the screen
pause_button = patches.Rectangle((BOARD_SIZE[0] - 1, 0), 1, 1, color='white', alpha=0.5)
ax.add_patch(pause_button)
ax.text(BOARD_SIZE[0] - 0.5, 0.5, 'Pause', color='white', fontsize=12, ha='center', va='center')

ball_patches = []
NB_OF_TRAIL_ELEMENTS = 1
for i in range(num_balls):
    ball = plt.Circle((0, 0), 1, color=ball_colors[i])
    ax.add_patch(ball)
    trail = create_trail_items(ball, ax)
    ball_patches.append(ball)
    for t in trail:
        ball_patches.append(t)

interval = 1000 / 60 / ANIMATION_SPEED
number_of_frames = len(frames) * SUB_FRAMES
ani = animation.FuncAnimation(fig, animate, frames=number_of_frames, interval=interval, blit=True)
ani.event_source.start()

plt.show()
