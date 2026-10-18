"""Shaded renders of the case (front 3/4, back 3/4, exploded) with trimesh + matplotlib."""
import os, sys, math
import numpy as np, trimesh
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, 'out')
L = lambda n: trimesh.load(os.path.join(OUT, n))
shell, back, stand = L('luchtmeter_voorkant.stl'), L('luchtmeter_achterplaat.stl'), L('luchtmeter_standaard.stl')
# stand-ins: cover glass (black, glossy) and the active screen area (dark blue) behind the window
glass = trimesh.creation.box((106.0, 67.9, 0.8)); glass.apply_translation((0, 10.0, -2.0))
screen = trimesh.creation.box((95.0, 53.9, 0.2)); screen.apply_translation((0, 10.0, -1.55))
pcb = trimesh.creation.box((106.0, 88.0, 1.6)); pcb.apply_translation((0, 0, -15.3))


def draw(ax, mesh, color, light, alpha=1.0, offset=(0, 0, 0)):
    m = mesh.copy(); m.apply_translation(offset)
    n = m.face_normals; shade = 0.35 + 0.65 * np.clip(n @ light, 0, 1)
    cols = np.clip(np.outer(shade, color), 0, 1)
    pc = Poly3DCollection(m.vertices[m.faces], facecolors=np.c_[cols, np.full(len(cols), alpha)], linewidths=0)
    ax.add_collection3d(pc)


def view(name, parts, elev, azim, lim=70):
    fig = plt.figure(figsize=(10, 8), dpi=110); ax = fig.add_subplot(111, projection='3d')
    ax.set_proj_type('persp', focal_length=0.3)
    e, a = math.radians(elev), math.radians(azim)
    cam = np.array([math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e)])
    light = cam * 0.6 + np.array([0.3, 0.5, 0.6]); light /= np.linalg.norm(light)
    for mesh, color, alpha, off in parts:
        draw(ax, mesh, color, light, alpha, off)
    ax.set_xlim(-lim, lim); ax.set_ylim(-lim, lim); ax.set_zlim(-lim, lim)
    ax.view_init(elev=elev, azim=azim, vertical_axis='y'); ax.set_axis_off()
    fig.patch.set_facecolor('#e9ecef')
    fig.savefig(os.path.join(OUT, name), bbox_inches='tight', facecolor=fig.get_facecolor()); plt.close(fig)
    print('render', name)


WHITE, GREY, BLACK, BLUE, GREEN = (0.93, 0.93, 0.91), (0.55, 0.57, 0.6), (0.04, 0.04, 0.05), (0.08, 0.16, 0.35), (0.05, 0.3, 0.12)
view('render_voorkant.png', [(shell, WHITE, 1, (0, 0, 0)), (screen, BLUE, 1, (0, 0, 0)), (glass, BLACK, 1, (0, 0, 0))], 18, -60)
view('render_achterkant.png', [(shell, WHITE, 1, (0, 0, 0)), (back, WHITE, 1, (0, 0, 0))], 20, 125)
view('render_explosie.png', [(shell, WHITE, 1, (0, 0, 0)), (glass, BLACK, 1, (0, 0, 0)), (pcb, GREEN, 1, (0, 0, -25)),
                             (back, GREY, 1, (0, 0, -55))], 20, -50, lim=85)
