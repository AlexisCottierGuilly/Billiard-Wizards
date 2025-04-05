import matplotlib.pyplot as plt
import numpy as np

import matplotlib.animation as animation
import matplotlib.patches as patches

import matplotlib as mpl
import matplotlib.font_manager as fm

from matplotlib.widgets import Button

fe = fm.FontEntry(
    fname='Spinnaker-Regular.ttf',
    name='Spinnaker')
fm.fontManager.ttflist.insert(0, fe)
mpl.rcParams['font.family'] = fe.name

BOARD_SIZE = (100, 100)

SUB_FRAMES = 60
ANIMATION_SPEED = 1
PAUSE_BUTTON_PATH = "icons/pause.png"
PLAY_BUTTON_PATH = "icons/play.png"

play_img = plt.imread(PLAY_BUTTON_PATH)
pause_img = plt.imread(PAUSE_BUTTON_PATH)

need_to_pause = False
need_to_play = False

click_start = None


class Ball(plt.Circle):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.trail_items = []
        self.selected = False

        self.dx = 0
        self.dy = 0
    
    def select(self):
        self.selected = True
        self.set_edgecolor('red')
        self.set_linewidth(3)
    def unselect(self):
        self.selected = False
        self.set_edgecolor('black')
        self.set_linewidth(0)


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
    end = x + (arrow_length / 2) * np.cos(angle), y + (arrow_length / 2) * np.sin(angle)

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
    
    polygon = plt.Polygon(scaled_vertices, closed=True, edgecolor='saddlebrown', facecolor='darkgreen', alpha=0.5)
    polygon.set_linewidth(5)
    return polygon


def update(frame1, frame2, percentage):
    for i, ball in enumerate(balls):
        trail_items = ball.trail_items
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

        ball.vx, ball.vy = vx, vy

        if ball.selected:
            ball.select()
        else:
            ball.unselect()

        update_trail_items(trail_items, x, y, vx, vy, r, color)

    return ball_patches


def animate(i):
    global need_to_pause, need_to_play
    frame1_index = i // SUB_FRAMES
    frame2_index = (i // SUB_FRAMES + 1) % len(frames)
    percentage = (i % SUB_FRAMES) / SUB_FRAMES

    if frame2_index < frame1_index:
        percentage = 1

    update(frames[frame1_index], frames[frame2_index], percentage)

    if need_to_pause:
        ani.event_source.stop()
        need_to_pause = False
    if need_to_play:
        ani.event_source.start()
        need_to_play = False

    return ball_patches


def process_force_modification(ball, mouse_pos):
    mx, my = mouse_pos
    x, y = ball.get_center()
    dx = mx - x
    dy = my - y

    multiplier = 0.05

    angle = np.arctan2(dy, dx)
    distance = np.sqrt(dx**2 + dy**2)

    ball.vx = np.cos(angle) * distance * multiplier
    ball.vy = np.sin(angle) * distance * multiplier


def pause_request():
    global need_to_pause
    need_to_pause = True
def play_request():
    global need_to_play
    need_to_play = True


def on_press(event):
    global is_paused
    if event.key == ' ':  # la barre d'espace pour la pause/reprise
        toggle_animation(event)
    if event.key == 'r':
        for ball in balls:
            if ball.selected:
                ball.unselect()
            else:
                ball.select()
        fig.canvas.draw()


def on_mouse_press(event):
    global click_start
    if event.inaxes:
        click_start = (event.xdata, event.ydata)


def on_mouse_release(event):
    global click_start
    click_start = None


def on_mouse_drag(event):
    if click_start is not None and event.inaxes:
        did_find_selected_ball = False
        for ball in balls:
            if ball.selected:
                did_find_selected_ball = True
                process_force_modification(ball, (event.xdata, event.ydata))
                update_trail_items(ball.trail_items, ball.get_center()[0], ball.get_center()[1], ball.vx, ball.vy, ball.get_radius(), ball.get_facecolor())
        if did_find_selected_ball:
            fig.canvas.draw()


def toggle_animation(event):
    global is_paused
    if is_paused:
        ani.event_source.start()
        button_ax.images[0].set_data(pause_img)
        fig.canvas.draw()
        play_request()
    else:
        ani.event_source.stop()
        button_ax.images[0].set_data(play_img)
        fig.canvas.draw()
        pause_request()
    is_paused = not is_paused


balls = []
ball_colors = []

is_paused = False

board_vertices, frames = read_data('data.txt')
num_balls = len(frames[0])
for i in range(num_balls):
    ball_colors.append(get_ball_color(i, num_balls))

plt.style.use('dark_background')
fig, ax = plt.subplots()

# fig.patch.set_facecolor('#151515')
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

# Create an axis for the image button in center of the figure (bottom)
button_ax = fig.add_axes([0.48, 0.02, 0.075, 0.075], frameon=False)
pause_button = Button(button_ax, '', color='black', hovercolor='gray')  # empty label

# Load the image
button_ax.imshow(pause_img)
button_ax.axis('off')  # Hide ticks and axes for a clean look
pause_button.on_clicked(toggle_animation)

ball_patches = []
NB_OF_TRAIL_ELEMENTS = 1
for i in range(num_balls):
    ball = Ball((0, 0), 1, color=ball_colors[i])
    ax.add_patch(ball)
    trail = create_trail_items(ball, ax)
    ball.trail_items = trail
    balls.append(ball)
    ball_patches.append(ball)
    for t in trail:
        ball_patches.append(t)

interval = 1000 / 60 / ANIMATION_SPEED
number_of_frames = len(frames) * SUB_FRAMES
ani = animation.FuncAnimation(fig, animate, frames=number_of_frames, interval=interval, blit=False)
ani.event_source.start()

fig.canvas.mpl_connect('button_press_event', on_mouse_press)
fig.canvas.mpl_connect('button_release_event', on_mouse_release)
fig.canvas.mpl_connect('motion_notify_event', on_mouse_drag)

plt.show()
