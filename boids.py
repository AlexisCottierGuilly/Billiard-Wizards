import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.path import Path
from matplotlib.patches import PathPatch
import random

# --- Création de la forme d'un poisson ---
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

# --- Classe Fish, les danseurs insouciants de l'océan ---
class Fish:
    def __init__(self, ax, position, velocity, scale=1.0, color='steelblue'):
        self.ax = ax
        self.position = np.array(position, dtype=float)
        self.velocity = np.array(velocity, dtype=float)
        self.scale = scale
        self.base_path = get_fish_path(scale)
        self.patch = PathPatch(self.base_path, facecolor=color, lw=0)
        ax.add_patch(self.patch)
    
    def update(self, fishes, sharks, dt=1.0):
        perception_radius = 0.5
        sigma = perception_radius / 35.0  # sigma = 0.05
        max_turn = np.pi / 12  # 15° par frame
        
        alignment = np.zeros(2)
        cohesion = np.zeros(2)
        separation = np.zeros(2)
        total_weight = 0
        
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
        
        # Influence des requins : fuite viscérale
        for shark in sharks:
            fear_radius = 0.5
            vec_to_shark = self.position - shark.position
            distance_to_shark = np.linalg.norm(vec_to_shark)
            if distance_to_shark < fear_radius:
                fear_strength = np.exp(- (distance_to_shark ** 2) / (2 * (fear_radius/3)**2))
                repulsion = (vec_to_shark / (distance_to_shark + 1e-5)) * 0.15 * fear_strength
                acceleration += repulsion
        
        v_old = self.velocity.copy()
        v_new = self.velocity + acceleration
        
        angle_old = np.arctan2(v_old[1], v_old[0])
        angle_new = np.arctan2(v_new[1], v_new[0])
        angle_diff = (angle_new - angle_old + np.pi) % (2 * np.pi) - np.pi
        if np.abs(angle_diff) > max_turn:
            angle_new = angle_old + np.sign(angle_diff) * max_turn
            speed = np.linalg.norm(v_new)
            v_new = speed * np.array([np.cos(angle_new), np.sin(angle_new)])
        
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

# --- Classe Shark, les prédateurs implacables (qui peuvent eux-mêmes avoir peur !) ---
class Shark:
    def __init__(self, ax, position, scale=0.225, color='lightslategrey'):
        self.ax = ax
        self.position = np.array(position, dtype=float)
        self.scale = scale
        self.velocity = np.array([1, 0], dtype=float)  # direction initiale
        self.base_path = self.get_shark_path(scale)
        self.patch = PathPatch(self.base_path, facecolor=color, lw=0)
        ax.add_patch(self.patch)
    
    def get_shark_path(self, scale=1.0):
        # Forme stylisée et élégante pour le requin
        verts = [
            (0.15, 0),    # Pointe avant
            (0, 0.08),    # Haut du corps
            (-0.15, 0),   # Corps arrière
            (0, -0.08),   # Bas du corps
            (0.15, 0)     # Retour à la pointe
        ]
        verts = np.array(verts) * scale
        codes = [Path.MOVETO, Path.LINETO, Path.LINETO, Path.LINETO, Path.CLOSEPOLY]
        return Path(verts, codes)
    
    def update(self, fishes, dt=1.0):
        # --- Calcul de la densité locale de poissons ---
        density_radius = 0.5
        density_sigma = density_radius / 3.0  # pour une pondération douce
        density = 0.0
        weighted_sum = np.zeros(2)
        for fish in fishes:
            distance = np.linalg.norm(fish.position - self.position)
            if distance < density_radius:
                weight = np.exp(- (distance ** 2) / (2 * density_sigma ** 2))
                density += weight
                weighted_sum += fish.position * weight
        
        # Seuil de densité pour que le requin prenne peur
        density_threshold = 2.0
        
        if density > density_threshold:
            # Calcul du centre de masse des poissons dans la zone
            center_of_mass = weighted_sum / density
            # Le requin fuit en s'éloignant du centre de masse
            direction = self.position - center_of_mass
            norm = np.linalg.norm(direction)
            if norm > 0:
                direction /= norm
            else:
                direction = np.array([1, 0])
            max_speed = 0.007
            self.velocity = direction * max_speed
        else:
            # Comportement normal : chasse le poisson le plus proche
            if fishes:
                distances = [np.linalg.norm(fish.position - self.position) for fish in fishes]
                target = fishes[np.argmin(distances)]
                direction = target.position - self.position
                norm = np.linalg.norm(direction)
                if norm > 0:
                    direction /= norm
                else:
                    direction = np.array([1, 0])
                max_speed = 0.007
                self.velocity = direction * max_speed
        
        self.position = (self.position + self.velocity * dt) % 1.0
    
    def draw(self):
        angle = np.arctan2(self.velocity[1], self.velocity[0])
        c, s = np.cos(angle), np.sin(angle)
        R = np.array([[c, -s], [s, c]])
        verts = self.base_path.vertices.copy()
        transformed_verts = (verts @ R.T) + self.position
        self.patch.set_path(Path(transformed_verts, self.base_path.codes))

# --- Configuration de la figure en plein écran et du fond océanique sombre ---
fig, ax = plt.subplots()
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.set_aspect('equal')
fig.patch.set_facecolor('midnightblue')
ax.set_facecolor('midnightblue')
plt.axis('off')

# Passage en mode plein écran
mng = plt.get_current_fig_manager()

# Palette de couleurs sobres pour les poissons
colors = ['steelblue', 'cadetblue', 'slategray', 'mediumslateblue', 'mediumaquamarine']

# Création des poissons
num_fishes = 80
fishes = []
for _ in range(num_fishes):
    pos = np.random.rand(2)
    angle = np.random.rand() * 2 * np.pi
    vel = np.array([np.cos(angle), np.sin(angle)]) * 0.002
    color = random.choice(colors)
    fishes.append(Fish(ax, pos, vel, scale=0.3, color=color))

# Création de plusieurs requins
num_sharks = 2
sharks = []
for _ in range(num_sharks):
    pos = np.random.rand(2)
    sharks.append(Shark(ax, pos, scale=0.225, color='lightslategrey'))

# --- Animation dynamique entre chasseurs et chassés (et requins parfois effrayés !) ---
def animate(frame):
    # Mise à jour et dessin des requins
    for shark in sharks:
        shark.update(fishes, dt=1.0)
        shark.draw()
    
    # Mise à jour et dessin des poissons
    for fish in fishes:
        fish.update(fishes, sharks, dt=1.0)
        fish.draw()
    
    # Les requins capturent les poissons s'ils se rapprochent trop
    capture_radius = 0.03
    remaining_fishes = []
    for fish in fishes:
        captured = any(np.linalg.norm(fish.position - shark.position) < capture_radius for shark in sharks)
        if not captured:
            remaining_fishes.append(fish)
    fishes[:] = remaining_fishes
    
    return [fish.patch for fish in fishes] + [shark.patch for shark in sharks]

anim = animation.FuncAnimation(fig, animate, frames=1000, interval=20, blit=True)

plt.show()
