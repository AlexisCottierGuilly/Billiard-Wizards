import numpy as np

# Constants
NUM_BALLS = 2
FRAMES = 5
OUTPUT_PATH = 'data.txt'
MAX_V = 2
dt = 0.1


# Bounds
# np.array([[0, 0, 1, 0], [1, 0, 0, 1.5], [0, 1.5, 0, 0]])
polygon = np.array([[0, 0, 1, 1], [1, 1, 2, 0], [2, 0, 1, -1], [1, -1, 0, 0], [0.75, 0.25, 1.25, 0.25], [1.25, 0.25, 1.25, -0.25], [1.25, -0.25, 0.75, -0.25], [0.75, -0.25, 0.75, 0.25], [0.9, 0.1, 1.1, 0.2], [1.1, 0.2, 1.1, 0], [1.1, 0, 1, -0.14], [1, -0.14, 0.8, -0.1], [0.8, -0.1, 0.9, 0.1]]) #list of sides, where each side is two points
is_infinite = polygon[:, 0] == polygon[:, 2]
is_zero = polygon[:, 1] == polygon[:, 3]
slopes = (polygon[:, 1] - polygon[:, 3]) / (polygon[:, 0] - polygon[:, 2] + is_infinite)
normals = np.dstack((polygon[:, 0] - polygon[:, 2], polygon[:, 1] - polygon[:, 3]))[0]
print(normals)
lengths = np.sqrt(normals[:, 0] * normals[:, 0] + normals[:, 1] * normals[:, 1])
normals[:, 0] /= lengths
normals[:, 1] /= lengths
print(normals.shape)
print(normals)
lower = np.min(np.dstack((polygon[:, 1], polygon[:, 3])), 2)[0]
upper = np.max(np.dstack((polygon[:, 1], polygon[:, 3])), 2)[0]
intercepts = polygon[:, 3] - slopes * polygon[:, 2]
BOUNDS = np.min(polygon[:, ::2]), np.max(polygon[:, ::2]), np.min(polygon[:, 1::2]), np.max(polygon[:, 1::2])
# Variables
x = np.array([np.random.uniform(BOUNDS[0] - (BOUNDS[1]-BOUNDS[0])/10, BOUNDS[1] + (BOUNDS[1]-BOUNDS[0])/10, NUM_BALLS), np.random.uniform(BOUNDS[2] - (BOUNDS[3]-BOUNDS[2])/10, BOUNDS[3] + (BOUNDS[3]-BOUNDS[2])/10, NUM_BALLS)], np.float64).T
v = np.random.standard_normal((NUM_BALLS, 2)) * MAX_V
print(v)

file = open(OUTPUT_PATH, 'w')
for side in polygon:
    file.write(f"{side[0]} {side[1]} {side[2]} {side[3]} ")
file.write("\n")

for i in range(FRAMES):
    print(x)
    for i in range(NUM_BALLS):
        file.write(f"{x[i][0]} {x[i][1]} {v[i][0]} {v[i][1]} 1 ")
    file.write("\n")
    x += v * dt
    # find balls outside polygon
    # first check if out of bounds
    #bounds_check = (x[:, 0] > BOUNDS[0]) & (x[:, 0] < BOUNDS[1]) & (x[:, 1] > BOUNDS[2]) * (x[:, 1] < BOUNDS[3])
    in_bounds = x#[bounds_check]
    num_intersections = np.zeros(NUM_BALLS, np.int32)
    last_isect = np.zeros(NUM_BALLS, np.int32)
    for i in range(slopes.size): #for each edge
        does_intersect = np.zeros(NUM_BALLS, np.bool)
        if is_zero[i]:
            does_intersect = in_bounds[:, 1] == polygon[i][1] 
        else:
            x_isect = in_bounds[:, 1] if is_infinite[i] else (in_bounds[:, 1] - intercepts[i]) / slopes[i]
            y_isect = x_isect * slopes[i] + intercepts[i]
            does_intersect = (x_isect > BOUNDS[0]) & (x_isect < in_bounds[:, 0]) & (y_isect > lower[i]) & (y_isect < upper[i])
        last_isect[does_intersect] = i
        num_intersections += does_intersect
    actual_normals = normals[last_isect]
    outside = num_intersections % 2 == 0
    a = (2*(v[:, 0] * actual_normals[:, 0] + v[:, 1] * actual_normals[:, 1]))
    #v = outside[:, None] * ((v - a[:, None]) * actual_normals) + (1 - outside)[:, None]*v

file.close()