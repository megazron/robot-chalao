#!/usr/bin/env python3
"""Regenerate the diagrams in docs/img/ for Robot Chalao.

    python3 docs/make_figures.py

Hand-built SVG so it needs nothing but the standard library. Three diagrams:
the compile/run pipeline, a Hinglish-to-ROS mapping, and the plugin architecture.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(HERE, "img")
os.makedirs(IMG, exist_ok=True)

INK = "#1f2933"
MUTE = "#6b7580"
LINE = "#c3cbd3"
SAFF = "#e07a1f"        # saffron accent
SAFF_BG = "#fdefe0"
GREEN = "#2b8a3e"
GREEN_BG = "#e8f5ec"
TEAL = "#0b7285"
TEAL_BG = "#e3f2f4"
PAPER = "#ffffff"
FONT = "'Segoe UI',Helvetica,Arial,sans-serif"
MONO = "'Cascadia Code','Consolas','DejaVu Sans Mono',monospace"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class SVG:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.b = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" font-family="{FONT}">',
            '<defs><marker id="arw" markerWidth="10" markerHeight="10" refX="8" '
            'refY="3" orient="auto"><path d="M0,0 L8,3 L0,6 z" fill="#6b7580"/>'
            '</marker></defs>',
            f'<rect width="{w}" height="{h}" fill="{PAPER}"/>']

    def box(self, x, y, w, h, title, sub="", fill=PAPER, stroke=LINE, tcol=INK,
            mono=False, rx=9, sw=1.6):
        self.b.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
                      f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
        fam = f' font-family="{MONO}"' if mono else ""
        ty = y + (h / 2 + 5 if not sub else h / 2 - 4)
        self.b.append(f'<text x="{x+w/2}" y="{ty}" text-anchor="middle" '
                      f'font-size="14" font-weight="600" fill="{tcol}"{fam}>{esc(title)}</text>')
        if sub:
            self.b.append(f'<text x="{x+w/2}" y="{y+h/2+15}" text-anchor="middle" '
                          f'font-size="11.5" fill="{MUTE}">{esc(sub)}</text>')

    def arrow(self, x1, y1, x2, y2, dash=False):
        d = ' stroke-dasharray="5 5"' if dash else ""
        self.b.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{MUTE}" '
                      f'stroke-width="1.8" marker-end="url(#arw)"{d}/>')

    def text(self, x, y, s, size=13, fill=INK, anchor="start", weight="400", mono=False):
        fam = f' font-family="{MONO}"' if mono else ""
        self.b.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" '
                      f'text-anchor="{anchor}" font-weight="{weight}"{fam}>{esc(s)}</text>')

    def save(self, name):
        self.b.append("</svg>")
        open(os.path.join(IMG, name), "w").write("\n".join(self.b))
        print("wrote", name)


def pipeline():
    s = SVG(1000, 420)
    s.text(30, 40, "How a .rc program runs", size=22, weight="700")
    s.text(30, 64, "One front-end, two back-ends: interpret it now, or read the "
           "Python it would generate.", size=13, fill=MUTE)
    # top row: source -> lexer -> parser -> interpreter -> backend
    row = [
        ("robot.rc", "Hinglish source", SAFF_BG, SAFF),
        ("lexer", "tokens", TEAL_BG, TEAL),
        ("parser", "AST", TEAL_BG, TEAL),
        ("interpreter", "tree-walk", TEAL_BG, TEAL),
    ]
    x, y, w, h, gap = 30, 100, 200, 66, 26
    cx = []
    for i, (t, sub, bg, st) in enumerate(row):
        s.box(x, y, w, h, t, sub, fill=bg, stroke=st, mono=(i == 0))
        cx.append(x + w)
        if i:
            s.arrow(cx[i-1] - w + w, y + h/2, x, y + h/2) if False else None
        x += w + gap
    for i in range(1, len(row)):
        bx = 30 + i * (w + gap)
        s.arrow(bx - gap, y + h/2, bx, y + h/2)
    # interpreter -> backends
    s.arrow(30 + 3*(w+gap) + w/2, y + h, 30 + 3*(w+gap) + w/2, 250)
    s.box(30 + 3*(w+gap) - 40, 250, w + 80, 60,
          "backend (capability router)", "moveit · nav2 · perception · mavros · gazebo · sim",
          fill=GREEN_BG, stroke=GREEN)
    s.text(30 + 3*(w+gap) + w/2, 340, "real robot  —or—  --simulate (zero ROS)",
           size=12, fill=MUTE, anchor="middle")
    # parser -> transpiler -> python
    px = 30 + 2*(w+gap) + w/2
    s.arrow(px, y + h, px, 250)
    s.box(30 + (w+gap) - 30, 250, w + 60, 60, "transpiler",
          "readable rclpy / moveit_py / nav2 python", fill=SAFF_BG, stroke=SAFF)
    s.text(30 + (w+gap) + w/2, 340, "chalao transpile robot.rc  ->  robot.py",
           size=12, fill=MUTE, anchor="middle", )
    s.save("pipeline.svg")


def mapping():
    s = SVG(1000, 430)
    s.text(30, 40, "Hinglish in, ROS 2 out", size=22, weight="700")
    s.text(30, 64, "Each line is one backend call, one ROS 2 action.", size=13, fill=MUTE)
    left = [
        ('robot jodo "ur5"', "connect() -> rclpy node + MoveItPy from chalao.yaml"),
        ("ghar jao", "arm_home() -> named target 'home', plan + execute"),
        ('jao pose(0.4,0.1,0.2, 0,3.14,0)', "arm_pose() -> set_pose_target + plan + execute"),
        ("pakdo", "gripper(close=True) -> gripper action"),
        ("seedha jao (0.4,0.1,0.4)", "arm_cartesian() -> compute_cartesian_path"),
        ('object dhundo "red cup"', "find_object() -> detector plugin -> Detection"),
        ("yahan jao (2,1,0)", "nav_to() -> nav2_simple_commander goToPose"),
        ("band karo", "estop() -> cancel every action + zero cmd_vel"),
    ]
    y = 96
    for hi, ros in left:
        s.box(30, y, 330, 34, hi, fill=SAFF_BG, stroke=SAFF, mono=True, rx=6, sw=1.3)
        s.arrow(366, y + 17, 404, y + 17)
        s.box(408, y, 560, 34, ros, fill=GREEN_BG, stroke=GREEN, mono=True, rx=6, sw=1.3)
        y += 41
    s.save("mapping.svg")


def plugins():
    s = SVG(1000, 440)
    s.text(30, 40, "Plugin architecture", size=22, weight="700")
    s.text(30, 64, "Every capability is a named backend in a registry. Add a robot "
           "type by registering one more.", size=13, fill=MUTE)
    caps = ["connection", "arm", "base", "perception", "raw", "control", "sim", "drone"]
    x, y, w, h = 30, 100, 112, 44
    for i, c in enumerate(caps):
        cx = x + (i % 4) * (w + 12)
        cy = y + (i // 4) * (h + 12)
        s.box(cx, cy, w, h, c, fill=TEAL_BG, stroke=TEAL, rx=6, sw=1.3)
    # registry
    s.box(30, 224, 476, 52, "backend registry", "capability -> backend name",
          fill=PAPER, stroke=INK, sw=2)
    for i in range(4):
        s.arrow(30 + 56 + i*(w+12), 190, 30 + 56 + i*(w+12), 224)
    # backends row
    s.arrow(268, 276, 268, 316)
    real = [("sim", GREEN_BG, GREEN), ("moveit", SAFF_BG, SAFF), ("nav2", SAFF_BG, SAFF),
            ("perception", SAFF_BG, SAFF), ("mavros", SAFF_BG, SAFF), ("gazebo", SAFF_BG, SAFF)]
    bx = 30
    for name, bg, st in real:
        s.box(bx, 316, 150, 46, name,
              "always on" if name == "sim" else "lazy ROS import", fill=bg, stroke=st, rx=6, sw=1.3)
        bx += 158
        if bx > 940:
            break
    s.text(30, 400, "--simulate routes every capability to 'sim', so a .rc file runs "
           "with zero ROS installed.", size=12.5, fill=MUTE)
    s.save("plugins.svg")


if __name__ == "__main__":
    pipeline()
    mapping()
    plugins()
