import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.path import Path
from matplotlib.patches import PathPatch
import random

# --- Création du poisson ---
def get_fish_path(scale=1.0):
    verts = [
        (0, 0),            # Nez
        (-0.06, 0.03),     # Haut du corps
        (-0.10, 0),        # Queue
        (-0.06, -0.03),    # Bas du corps
        (0, 0)             # Retour au nez
    ]
    verts = np.array(verts) * scale
    codes = [Path.MOVETO, Path.LINETO, Path.LINETO, Path.LINETO, Path.CLOSEPOLY]
    return Path(verts, codes)

# --- Classe Fish, les danseurs de l'océan ---
class Fish:
    def __init__(self, ax, position, velocity, scale=1.0, color='steelblue'):
        self.ax = ax
        self.position = np.array(position, dtype=float)
        self.velocity = np.array(velocity, dtype=float)
        self.scale = scale
        self.base_path = get_fish_path(scale)
        self.patch = PathPatch(self.base_path, facecolor=color, lw=0)
        ax.add_patch(self.patch)
    
    def update(self, fishes, shark, dt=1.0):
        # Paramètres de perception
        perception_radius = 0.5
        sigma = perception_radius / 10.0  # sigma = 0.05
        max_turn = np.pi / 12  # 15° par frame
        
        alignment = np.zeros(2)
        cohesion = np.zeros(2)
        separation = np.zeros(2)
        total_weight = 0
        
        # Influence des autres poissons
        for other in fishes:
            if other is self:
                continue
            distance = np.linalg.norm(other.position - self.position)
            if distance < perception_radius:
                weight = np.exp(- (distance ** 2) / (2 * sigma ** 2))
                alignment += other.velocity * weight
                cohesion += other.position * weight
                separation += (self.position - other.position) / (distance + 1e-5) * weight
                total_weight += weight
        
        if total_weight > 0:
            alignment = (alignment / total_weight - self.velocity) * 0.05
            cohesion = ((cohesion / total_weight) - self.position) * 0.05
            separation = separation * 0.02
            acceleration = alignment + cohesion + separation
        else:
            acceleration = np.zeros(2)
        
        # Influence du requin qui inspire la peur 😱🦈
        if shark.active:
            fear_radius = 0.5
            vec_to_shark = self.position - shark.position
            distance_to_shark = np.linalg.norm(vec_to_shark)
            if distance_to_shark < fear_radius:
                # Une force de répulsion forte, qui décroît doucement
                fear_strength = np.exp(- (distance_to_shark ** 2) / (2 * (fear_radius/3)**2))
                repulsion = (vec_to_shark / (distance_to_shark + 1e-5)) * 0.15 * fear_strength
                acceleration += repulsion
        
        # Calcul de la nouvelle vélocité avec limitation de virage
        v_old = self.velocity.copy()
        v_new = self.velocity + acceleration
        
        angle_old = np.arctan2(v_old[1], v_old[0])
        angle_new = np.arctan2(v_new[1], v_new[0])
        angle_diff = (angle_new - angle_old + np.pi) % (2 * np.pi) - np.pi
        if np.abs(angle_diff) > max_turn:
            angle_new = angle_old + np.sign(angle_diff) * max_turn
            speed = np.linalg.norm(v_new)
            v_new = speed * np.array([np.cos(angle_new), np.sin(angle_new)])
        
        # Limitation de la vitesse
        max_speed = 0.005
        speed = np.linalg.norm(v_new)
        if speed > max_speed:
            v_new = (v_new / speed) * max_speed
        
        if np.linalg.norm(v_new) < 1e-4:
            v_new += (np.random.rand(2) - 0.5) * 1e-3
        
        self.velocity = v_new
        self.position = (self.position + self.velocity * dt) % 1.0

    def draw(self):
        angle = np.arctan2(self.velocity[1], self.velocity[0])
        c, s = np.cos(angle), np.sin(angle)
        R = np.array([[c, -s], [s, c]])
        verts = self.base_path.vertices.copy()
        transformed_verts = (verts @ R.T) + self.position
        self.patch.set_path(Path(transformed_verts, self.base_path.codes))

# --- Classe Shark, le maître de la terreur ---
class Shark:
    def __init__(self, ax, position, scale=0.5, color='gray'):
        self.ax = ax
        self.position = np.array(position, dtype=float)
        self.scale = scale
        self.active = False
        self.base_path = self.get_shark_path(scale)
        self.patch = PathPatch(self.base_path, facecolor=color, lw=0)
        ax.add_patch(self.patch)
    
    def get_shark_path(self, scale=1.0):
        # Une forme de requin simple et stylisée (triangle allongé)
        verts = [
            (0.2, 0),               # Pointe avant
            (-0.2, 0.12),           # Haut du corps
            (-0.2, -0.12),          # Bas du corps
            (0.2, 0)                # Retour à la pointe
        ]
        verts = np.array(verts) * scale
        codes = [Path.MOVETO, Path.LINETO, Path.LINETO, Path.CLOSEPOLY]
        return Path(verts, codes)
    
    def draw(self):
        # Le requin est toujours orienté vers la droite pour la simplicité
        # Il suit la position de la souris
        new_path = Path(self.base_path.vertices + self.position, self.base_path.codes)
        self.patch.set_path(new_path)

# --- Configuration de la figure et du fond sombre ---
fig, ax = plt.subplots(figsize=(8, 8))
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.set_aspect('equal')
fig.patch.set_facecolor('midnightblue')
ax.set_facecolor('midnightblue')
plt.axis('off')

# Palette de couleurs sobres pour les poissons
colors = ['steelblue', 'cadetblue', 'slategray', 'mediumslateblue', 'mediumaquamarine']

# Création des poissons
num_fishes = 30
fishes = []
for _ in range(num_fishes):
    pos = np.random.rand(2)
    angle = np.random.rand() * 2 * np.pi
    vel = np.array([np.cos(angle), np.sin(angle)]) * 0.002
    color = random.choice(colors)
    fishes.append(Fish(ax, pos, vel, scale=0.35, color=color))

# Création du requin (inactif par défaut)
shark = Shark(ax, position=[0.5, 0.5], scale=0.5, color='dimgray')

# --- Gestion des événements souris pour contrôler le requin ---
def on_press(event):
    if event.inaxes != ax:
        return
    shark.active = True
    shark.position = np.array([event.xdata, event.ydata])
    shark.draw()

def on_motion(event):
    if shark.active and event.inaxes == ax:
        shark.position = np.array([event.xdata, event.ydata])
        shark.draw()

def on_release(event):
    shark.active = False

fig.canvas.mpl_connect('button_press_event', on_press)
fig.canvas.mpl_connect('motion_notify_event', on_motion)
fig.canvas.mpl_connect('button_release_event', on_release)

# --- Animation ---
def animate(frame):
    for fish in fishes:
        fish.update(fishes, shark)
        fish.draw()
    # Dessiner le requin si actif, sinon le cacher en le plaçant hors champ
    if shark.active:
        shark.draw()
    else:
        shark.patch.set_visible(False)
    return [fish.patch for fish in fishes] + [shark.patch]

anim = animation.FuncAnimation(fig, animate, frames=1000, interval=20, blit=True)

plt.show()
