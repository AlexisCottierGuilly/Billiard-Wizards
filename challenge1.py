from math import atan2, pi, sqrt, cos, sin
OUTPUT_PATH = "data.txt"
frames = 100000
#vertices are (-1, -1), (-1, 1), (1, 1), (1, -1)
pos = [0, -0.9]
prev_pos = pos.copy()
vel = [0.4, 0.2]
speed = sqrt(vel[0] * vel[0] + vel[1] * vel[1])
dt = 0.1

file = open(OUTPUT_PATH, "w")
file.write("-1 -1 -1 1 -1 1 1 1 1 1 -1 1 -1 1 -1 -1\n")
for i in range(frames):
    pos[0] += vel[0] * dt
    pos[1] += vel[1] * dt

    ver = pos[1] < -1 or pos[1] > 1
    hor = pos[0] < -1 or pos[0] > 1
    if (hor | ver):
        swap = vel[0]
        vel[0] = -vel[1]
        vel[1] = swap
        pos = prev_pos
    prev_pos = pos.copy()
    file.write(f"{(pos[0]+1)/2} {(pos[1]+1)/2} {vel[0]} {vel[1]} 1\n")
file.close()
    
    



