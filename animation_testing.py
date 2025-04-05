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

SUB_FRAMES = 1
animation_speed = 1
PAUSE_BUTTON_PATH = "icons/pause.png"
PLAY_BUTTON_PATH = "icons/play.png"

play_img = plt.imread(PLAY_BUTTON_PATH)
pause_img = plt.imread(PAUSE_BUTTON_PATH)

need_to_pause = False
need_to_play = False

click_start = None
last_click = None

shift_pressed = False

# Data
centers_of_mass = []


class Ball(plt.Circle):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.trail_items = []
        self.selected = False
        self.dragged = False

        self.dx = 0
        self.dy = 0

        self.x = 0
        self.y = 0
    
    def drag(self):
        self.dragged = True
        self.set_edgecolor('blue')
        self.set_linewidth(2)
    def undrag(self):
        self.dragged = False
        self.set_edgecolor('black')
        self.set_linewidth(0)
    
    def select(self):
        self.selected = True
        self.set_edgecolor('red')
        self.set_linewidth(3)
    def unselect(self):
        self.selected = False
        self.set_edgecolor('black')
        self.set_linewidth(0)
    
    def move(self, dx, dy):
        current_x, current_y = self.get_center()
        new_x = current_x + dx
        new_y = current_y + dy
        self.set_center((new_x, new_y))
        self.x = new_x / BOARD_SIZE[0]
        self.y = new_y / BOARD_SIZE[1]


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

    # Create a path to trace the trail of the ball
    trail_path = mpl.path.Path([(ball.x, ball.y)], closed=False)
    patch = patches.PathPatch(trail_path, edgecolor='orange', facecolor='none', lw=2, alpha=0.15)
    ax.add_patch(patch)

    shapes = [arrow, patch]
    return shapes


def update_trail_items(items, x, y, vx, vy, r, color, first_update=False):
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
        elif isinstance(item, patches.PathPatch):
            # add a new vertex to the path (if it is not already at the end)
            path = item.get_path()
            vertices = path.vertices
            if len(vertices) > 0 and (vertices[-1][0] == x and vertices[-1][1] == y):
                vertices[-1] = (x, y)
            else:
                vertices = np.vstack((vertices, (x, y)))
            path.vertices = vertices
            if first_update:
                path.vertices = path.vertices[1:]
            item.set_path(path)


def get_board_elements(board_vertices, size=(100, 100)):
    polygons = []
    remaining_vertices = [[board_vertices[2 * i], board_vertices[2 * i+1]] for i in range(round(len(board_vertices) / 2))]
    i = 0
    while len(remaining_vertices) > 0:
        vertex = remaining_vertices[0]
        polygon, remaining_vertices = get_polygon_with_vertex(vertex, remaining_vertices)
        polygons.append(polygon)

        i += 1
        if i > 100:
            print("Too many iterations")
            break
    
    min_x = min([v[0] for v in board_vertices])
    max_x = max([v[0] for v in board_vertices])
    min_y = min([v[1] for v in board_vertices])
    max_y = max([v[1] for v in board_vertices])

    offset_x = -min_x
    offset_y = -min_y
    min_x, max_x, min_y, max_y = min_x + offset_x, max_x + offset_x, min_y + offset_y, max_y + offset_y
    scale_x = size[0] / (max_x - min_x)
    scale_y = size[1] / (max_y - min_y)

    # Create the polygons
    polygon_patches = []
    for polygon in polygons:
        vertices = [v[0] for v in polygon]
        scaled_vertices = [((v[0] + offset_x) * scale_x, (v[1] + offset_y) * scale_y) for v in vertices]

        polygon_patch = plt.Polygon(scaled_vertices, closed=True, edgecolor='#4d3615', facecolor='#264d15', alpha=1)
        polygon_patch.set_linewidth(5)
        polygon_patches.append(polygon_patch)
    
    return polygon_patches


def get_polygon_with_vertex(vertex, remaining_vertices):
    new_remaining_vertices = remaining_vertices
    polygon = [vertex]
    current_vertex = vertex
    remaining_vertices.remove(vertex)

    i = 0
    while True:
        found_next = False
        returns_to_start = False
        for vertex in remaining_vertices:
            if vertex[0] == current_vertex[1]:
                if vertex[1] == polygon[0][0]:
                    returns_to_start = True
                polygon.append(vertex)
                current_vertex = vertex
                new_remaining_vertices.remove(vertex)
                found_next = True
                break
        if not found_next or returns_to_start:
            break

        i += 1
        if i > 100:
            break
    
    return polygon, new_remaining_vertices


def update(frame1, frame2, percentage, first_update=False):
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
        ball.x, ball.y = x, y

        if ball.selected:
            ball.select()
        else:
            ball.unselect()

        update_trail_items(trail_items, x, y, vx, vy, r, color, first_update)

    return ball_patches


def calculate_centers_of_mass(frames):
    global centers_of_mass
    centers_of_mass = []
    for frame in frames:
        x_sum = 0
        y_sum = 0
        for ball in frame:
            x_sum += ball[0]
            y_sum += ball[1]
        centers_of_mass.append((x_sum / len(frame), y_sum / len(frame)))

    save_center_of_mass()


def animate(i):
    global need_to_pause, need_to_play, centers_of_mass
    frame1_index = i // SUB_FRAMES
    frame2_index = (i // SUB_FRAMES + 1) % len(frames)
    percentage = (i % SUB_FRAMES) / SUB_FRAMES

    if frame2_index < frame1_index:
        percentage = 1
    
    if i == 0:
        for ball in balls:
            path_trail = ball.trail_items[1]
            path = path_trail.get_path()
            path.vertices = np.array([[ball.x * BOARD_SIZE[0], ball.y * BOARD_SIZE[1]]])
            path_trail.set_path(path)

    update(frames[frame1_index], frames[frame2_index], percentage, i==0)

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

    multiplier = 0.1

    angle = np.arctan2(-dy, -dx)
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
    global is_paused, animation_speed
    if event.key == ' ':  # la barre d'espace pour la pause/reprise
        toggle_animation(event)
    if event.key == 'r':
        reset_animation()
    if event.key == 'shift':
        global shift_pressed
        shift_pressed = True
    if event.key == 'p':
        save_center_of_mass()
    if event.key == '=':
        animation_speed *= 2
        set_animation_speed(animation_speed)
    if event.key == '-':
        animation_speed /= 2
        set_animation_speed(animation_speed)

def on_release(event):
    global shift_pressed
    if event.key == 'shift':
        shift_pressed = False


def on_mouse_press(event):
    global click_start, last_click
    if event.inaxes:
        click_start = (event.xdata, event.ydata)
        last_click = click_start
        
        for ball in balls:
            # try if the click is in the ball's circle
            radius = ball.get_radius()
            x, y = ball.get_center()
            if (event.xdata - x)**2 + (event.ydata - y)**2 <= radius**2:
                if shift_pressed:
                    ball.select()
                else:
                    ball.drag()
        
        fig.canvas.draw()


def on_mouse_release(event):
    global click_start, last_click
    click_start = None
    last_click = None

    for ball in balls:
        ball.unselect()
        ball.undrag()
    fig.canvas.draw()


def on_mouse_drag(event):
    global click_start, last_click
    if click_start is not None and event.inaxes:
        did_find_selected_ball = False
        for ball in balls:
            if ball.selected or (ball.dragged and last_click is not None):
                did_find_selected_ball = True
                if ball.selected:
                    process_force_modification(ball, (event.xdata, event.ydata))
                elif ball.dragged:
                    dx, dy = event.xdata - last_click[0], event.ydata - last_click[1]
                    ball.move(dx, dy)
                update_trail_items(ball.trail_items, ball.x, ball.y, ball.vx, ball.vy, ball.get_radius(), ball.get_facecolor())
        if did_find_selected_ball:
            fig.canvas.draw()
    
        last_click = (event.xdata, event.ydata)


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


def set_animation_speed(speed=1):
    global ani
    ani.event_source.stop()
    ani.event_source.interval = 1000 / 60 / speed
    ani.event_source.start()


def start_animation(figure, anim_function, nb_frames, interval, blit=False):
    global ani
    ani = animation.FuncAnimation(figure, anim_function, frames=nb_frames, interval=interval, blit=blit)  
    ani.event_source.start()


def reset_animation():
    global ani
    ani.event_source.stop()
    start_animation(fig, animate, number_of_frames, interval, blit=False)


def save_center_of_mass():
    with open('center_of_mass_data.txt', 'w') as file:
        x_line = ""
        y_line = ""
        for i, center in enumerate(centers_of_mass):
            x_line += f"{center[0]} {i} "
            y_line += f"{center[1]} {i} "
        file.write(x_line + "\n")
        file.write(y_line + "\n")


balls = []
ball_colors = []

is_paused = False

board_vertices, frames = read_data('data.txt')
num_balls = len(frames[0])
for i in range(num_balls):
    ball_colors.append(get_ball_color(i, num_balls))

calculate_centers_of_mass(frames)

plt.style.use('dark_background')
fig, ax = plt.subplots()

# fig.patch.set_facecolor('#151515')

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

board_elements = get_board_elements(board_vertices, size=BOARD_SIZE)
for elem in board_elements:
    ax.add_patch(elem)

# Create an axis for the image button in center of the figure (bottom)
button_ax = fig.add_axes([0.475, 0.02, 0.075, 0.075], frameon=False)
pause_button = Button(button_ax, '', color='black', hovercolor='gray')  # empty label

# Load the image
button_ax.imshow(pause_img, alpha=0.5)
button_ax.axis('off')  # Hide ticks and axes for a clean look
pause_button.on_clicked(toggle_animation)

ball_patches = []
NB_OF_TRAIL_ELEMENTS = 2
for i in range(num_balls):
    ball = Ball((0, 0), 1, color=ball_colors[i])
    ax.add_patch(ball)
    trail = create_trail_items(ball, ax)
    ball.trail_items = trail
    ball.set_zorder(10)
    balls.append(ball)
    ball_patches.append(ball)
    for t in trail:
        ball_patches.append(t)

interval = 1000 / 60 / animation_speed
number_of_frames = len(frames) * SUB_FRAMES
#ani = animation.FuncAnimation(fig, animate, frames=number_of_frames, interval=interval, blit=False)
#ani.event_source.start()
start_animation(fig, animate, number_of_frames, interval, blit=False)

fig.canvas.mpl_connect('key_press_event', on_press)
fig.canvas.mpl_connect('key_release_event', on_release)
fig.canvas.mpl_connect('button_press_event', on_mouse_press)
fig.canvas.mpl_connect('button_release_event', on_mouse_release)
fig.canvas.mpl_connect('motion_notify_event', on_mouse_drag)

def convert_to_array(s_template):
    numbers = [int(i) for i in s_template.split()]
    grouped = [list(numbers[i:i + 4]) for i in range(0, len(numbers), 4)]
    max_value = max(max(group) for group in grouped)
    normalized = [[x / max_value for x in group] for group in grouped]
    return normalized

#print(convert_to_array("689 141 784 154 784 154 875 192 875 192 949 252 949 252 999 313 999 313 1022 391 1022 391 1031 467 1031 467 1018 553 1018 553 986 626 986 626 936 680 936 680 869 728 869 728 799 757 616 763 536 741 536 741 445 683 445 683 395 605 395 605 371 509 371 509 376 408 376 408 399 328 399 328 432 267 432 267 495 202 495 202 575 158 575 158 689 141 799 757 716 771 716 771 616 763"))

plt.show()
