import numpy as np

# Constants
NUM_BALLS = 200
FRAMES = 600
OUTPUT_PATH = 'data.txt'
MAX_V = 1
dt = 0.01
epsilon = -0.5
sensitivity = 0

# Bounds
#polygon = np.array([[0, 0, 1, 0], [1, 0, 1, 1], [1, 1, 0, 1], [0, 1, 0, 0]])
polygon = np.array([[0, 0, 1, 1], [1, 1, 2, 0], [2, 0, 1, -1], [1, -1, 0, 0], [0.75, 0.25, 1.25, 0.25], [1.25, 0.25, 1.25, -0.25], [1.25, -0.25, 0.75, -0.25], [0.75, -0.25, 0.75, 0.25], [0.9, 0.1, 1.1, 0.2], [1.1, 0.2, 1.1, 0], [1.1, 0, 1, -0.14], [1, -0.14, 0.8, -0.1], [0.8, -0.1, 0.9, 0.1]]) #list of sides, where each side is two points
#polygon = np.array([[0, 0, 1, 1], [1, 1, 2, 0], [2, 0, 1, -1], [1, -1, 0, 0]])
As = polygon[:, 1] - polygon[:, 3]
Bs = polygon[:, 2] - polygon[:, 0]
normals = np.array(list(zip(As, Bs)), np.float64)
magnitudes = np.sqrt(normals[:, 0] ** 2 + normals[:, 1]**2)
print(normals)
print(magnitudes)
normals /= magnitudes[:, None]
print(normals)
Cs = polygon[:, 0]*polygon[:, 3] - polygon[:, 2]*polygon[:, 1]
lower = np.min(np.dstack((polygon[:, 1], polygon[:, 3])), 2)[0]
upper = np.max(np.dstack((polygon[:, 1], polygon[:, 3])), 2)[0]
#intercepts = polygon[:, 3] - slopes * polygon[:, 2]
BOUNDS = np.min(polygon[:, ::2]), np.max(polygon[:, ::2]), np.min(polygon[:, 1::2]), np.max(polygon[:, 1::2])
SIZE = BOUNDS[1] - BOUNDS[0], BOUNDS[3] - BOUNDS[2]
# Variables
#x = np.array([[0.2, 0.5]])
x = np.array([np.random.uniform(BOUNDS[0] - SIZE[0] * epsilon, BOUNDS[1] + SIZE[0] * epsilon, NUM_BALLS), np.random.uniform(BOUNDS[2] - SIZE[1] * epsilon, BOUNDS[3] + SIZE[1] * epsilon, NUM_BALLS)], np.float64).T
xprev = x.copy()
#v = np.array([[0, 2]])#
v = np.random.standard_normal((NUM_BALLS, 2)) * MAX_V
file = open(OUTPUT_PATH, 'w')
for side in polygon:
    file.write(f"{side[0]} {side[1]} {side[2]} {side[3]} ")
file.write("\n")


for i in range(FRAMES):
    x += v * dt
    num_intersections = np.zeros(NUM_BALLS, np.int32)
    nearest_side = np.zeros(NUM_BALLS, np.int32)
    closest = np.zeros(NUM_BALLS, np.float64)
    for i in range(polygon.shape[0]): #for each edge
        if (As[i] == 0):
            num_intersections += x[:, 1] == Cs[i]
        else:
            x_isect = -(Cs[i] + Bs[i] * x[:, 1]) / As[i]
            num_intersections += (lower[i] < x[:, 1]) & (x[:, 1] < upper[i]) & (x_isect < x[:, 0])
            #crossed = ((xprev[:, 0] < x_isect) & (x_isect < x[:, 0])) | ((x[:, 0] < x_isect) & (x_isect < xprev[:, 0]))
            proximity_to_line = As[i] * x[:, 0] + Bs[i] * x[:, 1] + Cs[i]
            #print(i, proximity_to_line)
            improved = proximity_to_line > closest
            nearest_side[improved] = i
            closest[improved] = proximity_to_line[improved]
    xprev = x.copy()
    new_v = v - 2*(v[:, 0] * normals[:, 0][nearest_side] + v[:, 1] * normals[:, 1][nearest_side])[:, None] * normals[nearest_side]
    x[num_intersections % 2 == 0] = xprev[num_intersections % 2 == 0]
    v[num_intersections % 2 == 0] = new_v[num_intersections % 2 == 0]
    for i in range(NUM_BALLS):
        file.write(f"{(x[i][0] - BOUNDS[0])/SIZE[0]} {(x[i][1] - BOUNDS[2])/SIZE[1]} {v[i][0]} {v[i][1]} {1} ")
    file.write("\n")

file.close()