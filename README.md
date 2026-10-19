# Robot Chalao 🤖

[![ci](https://github.com/megazron/robot-chalao/actions/workflows/ci.yml/badge.svg)](https://github.com/megazron/robot-chalao/actions/workflows/ci.yml)
[![release](https://img.shields.io/github/v/release/megazron/robot-chalao)](https://github.com/megazron/robot-chalao/releases/latest)
[![python](https://img.shields.io/badge/python-3.10%E2%80%933.13-blue)](pyproject.toml)
[![ROS 2](https://img.shields.io/badge/ROS%202-Jazzy%20%7C%20Humble-22314e)](#real-robots)
[![license](https://img.shields.io/badge/license-MIT-green)](LICENSE)

![demo](docs/img/demo.gif)

*Robot Chalao `.rc` code in short mode (`rakh`, `bol`, `bas`), the `chalao run --simulate` output, and the Kinova Gen3 executing it in MuJoCo.*

**Hinglish mein likho, koi bhi ROS 2 robot chalao.**
**Write Hinglish, run any ROS 2 robot.**

Robot Chalao ek chhoti programming language hai (file `.rc`) jisse aap Hindi-English
mix mein likh kar ek asli ya simulated robot chala sakte ho — arm, mobile base, drone,
humanoid, gripper, sensor. ROS nahi aati? Koi baat nahi. `--simulate` mode bina ROS ke
chalta hai, aur har line jo ROS 2 call banegi wo Hinglish mein print karta hai.

Robot Chalao is a small programming language (`.rc` files) that lets someone who knows
Hinglish but not ROS write a short script and drive a real or simulated robot — arms,
mobile bases, drones, humanoids, grippers, sensors. Advanced users can still drop down
to raw ROS 2 calls. `--simulate` runs with zero ROS installed and prints, in Hinglish,
exactly the ROS 2 calls it would make.

```
# pehla program / your first program
robot jodo "ur5"          # connect to the arm from chalao.yaml
speed 0.4
ghar jao                  # go home
maano pick = pose(0.4, 0.1, 0.2, 0, 3.14, 0)
jao pick                  # move to the pick pose
pakdo                     # close the gripper
seedha jao (0.4, 0.1, 0.4)   # lift straight up
chhodo                    # open the gripper
ghar jao
robot chhodo
```

```bash
chalao run pehla.rc --simulate --config examples/chalao.yaml
```

![How a .rc program runs](docs/img/pipeline.svg)

*Ek front-end, do back-end: abhi chalao, ya jo Python banega use padho. One front-end,
two back-ends: interpret it now, or read the generated Python.*

## Try it now, in your browser

**[▶ megazron.github.io/robot-chalao](https://megazron.github.io/robot-chalao/)**: write `.rc` code and run it in `--simulate` mode, see the ROS 2 Python it compiles to, and share a link to your program. It runs the real `robot_chalao` package in your browser via Pyodide, with no install and no ROS.

## 60-second start

```bash
pip install https://github.com/megazron/robot-chalao/releases/download/v1.0.0/robot_chalao-1.0.0-py3-none-any.whl
chalao init mera_robot && cd mera_robot
chalao run main.rc --simulate      # zero ROS needed
```

`chalao init` writes a `chalao.yaml` (your robot) and a `main.rc` (your program).
Edit them, `chalao check main.rc` to catch mistakes, and drop `--simulate` once a
ROS 2 robot is running.

## Kise ke liye? / Who is this for

Bharat mein bahut log Hinglish mein sochte hain par ROS 2 ka learning curve unko rok
deta hai. Robot Chalao wo doori kam karta hai: seedhe, natural commands, aur asli ROS
2 / MoveIt 2 / Nav2 / Gazebo neeche. For people who think in Hinglish but are blocked by
the ROS 2 learning curve. Plain commands on top, real ROS 2 underneath.

## Install

| What | How |
|---|---|
| Language + simulator (Python 3.10+, zero ROS) | `pip install https://github.com/megazron/robot-chalao/releases/download/v1.0.0/robot_chalao-1.0.0-py3-none-any.whl` |
| Latest from `main` | `pip install git+https://github.com/megazron/robot-chalao` |
| Native binary (no Python, static Linux x86_64) | download `chalao-native-v1.0.0-linux-x86_64.tar.gz` from [Releases](https://github.com/megazron/robot-chalao/releases/latest), or `make -C native` |
| VS Code highlighting + snippets | `code --install-extension robot-chalao-1.0.0.vsix` (from [Releases](https://github.com/megazron/robot-chalao/releases/latest)) |

For real robots, also install and source ROS 2 (Jazzy or Humble) and whatever your
robot needs:

```bash
sudo apt install ros-jazzy-desktop ros-jazzy-moveit ros-jazzy-navigation2 \
     ros-jazzy-nav2-bringup ros-jazzy-ros-gz
source /opt/ros/jazzy/setup.bash
```

`--simulate` ko ROS ki zaroorat nahi. `chalao doctor` batata hai kya installed hai.
`--simulate` needs none of that; `chalao doctor` tells you what is installed and how
to fix what is missing, in Hinglish.

## CLI

| Command | Kaam / What it does |
|---|---|
| `chalao init [dir]` | naya project: `chalao.yaml` + `main.rc` |
| `chalao run file.rc` | program chalao (real robot); `chalao file.rc` bhi chalta hai |
| `chalao run file.rc --simulate` | bina ROS ke dry-run |
| `chalao check file.rc ...` | grammar check, bina chalaye (CI ke liye exit code) |
| `chalao transpile file.rc -o out.py` | padhne-layak Python (rclpy/moveit_py/nav2) banao |
| `chalao repl` / `chalao repl --real` | interactive shell (`madad` = help), nakli ya asli |
| `chalao doctor` | ROS/MoveIt/Nav2 check, Hinglish diagnostics |
| `chalao --version` | version |
| `--config chalao.yaml` | robot config file chuno (default: `./chalao.yaml`, phir script ke paas wala) |

The native binary (`native/chalao`) supports `run`, `check`, `repl` and
`--version` with the simulator backend, byte-for-byte identical to the Python
reference. CI enforces that on every feature test and example.

## Hinglish in, ROS 2 out

![Hinglish to ROS 2 mapping](docs/img/mapping.svg)

*Har Hinglish line ek backend call hai, ek ROS 2 action. Each Hinglish line is one
backend call, one ROS 2 action.*

The complete keyword and command tables live in [`docs/GRAMMAR.md`](docs/GRAMMAR.md).
A summary:

**Core language**

| Hinglish | English |
|---|---|
| `maano x = 5` | variable |
| `agar … toh … warna … khatam` | if / else |
| `jab tak … karo … khatam` | while |
| `har x list mein karo … khatam` | for-each |
| `kaam f(a,b) … wapas … khatam` | function / return |
| `dikhao …` | print |
| `sach / jhooth / aur / ya / nahi` | true / false / and / or / not |
| `koshish … galti hone par e … khatam` | try / except |
| `ruko_loop` / `import "x.rc"` | break / import |

## Short forms

Don't want to type the long keywords? Use the short aliases. These are
**aliases**, not a new language: they map to the exact same keywords, so old
programs keep working and you can mix both in one file. Example 06 uses them and
prints byte-for-byte the same output as example 01.

| Short | Full | does |
|---|---|---|
| `bas` | `khatam` | end a block |
| `bol` | `dikhao` | print |
| `rakh` | `maano` | variable (`rakh x = 5`) |
| `try` | `koshish` | try |
| `de` | `wapas` | return |
| `tod` | `ruko_loop` | break a loop |

```
robot jodo "ur5"
speed 0.4
ghar jao
rakh pick = pose(0.4, 0.1, 0.2, 0, 3.14, 0)   # rakh = maano
jao pick
pakdo
agar battery kitni hai > 20 toh
    bol "battery theek hai"                    # bol = dikhao
warna
    bol "charge chahiye"
bas                                            # bas = khatam
robot chhodo
```

**Robot commands** (full mapping in `docs/GRAMMAR.md`): connection (`robot jodo`,
`robot chhodo`, `namespace`, `param`), arm via MoveIt 2 (`ghar jao`, `jao pose(...)`,
`seedha jao`, `pakdo`/`chhodo`, `speed`, `planner`, `rukawat jodo`, `attach`, `kahan hai`,
`IK nikalo`), mobile via Nav2 (`aage chalo`, `ghumo`, `yahan jao`, `waypoints follow`,
`map banao`/`save`, `obstacle nazdeek hai?`), perception (`camera dekho`, `object dhundo`,
`lidar padho`, `battery kitni hai`, `AprilTag dhundo`, `TF pucho`), raw ROS 2 (`sun`,
`bolo`, `sewa bulao`, `action bhejo`, `record shuru`, `launch`, `urdf load`), ros2_control
(`joint "j1" ko 1.2 rad pe le jao`, `controller switch`, `torque on/off`), simulation
(`simulation shuru gazebo`, `spawn`, `rviz kholo`), safety and timing (`band karo`,
`workspace limit`, `ruko 2 second`, `har 0.1 second mein … khatam`, `deadline`), and
drone via MAVROS (`udaan bharo`, `utro`, `height`), and runtime plumbing
shared with [zronOS](https://github.com/megazron/zronos): `frame` (publish a static
TF), `sehat theek/warning/kharaab` (diagnostics on `/diagnostics`), `sewa do`
(serve a function) and `maano r = sewa bulao "naam" args`.

## Config — `chalao.yaml`

`robot jodo "naam"` config file se robot uthata hai: type, planning group, ee link,
gripper topic, cmd_vel, named poses, speed/workspace limits, camera topics.

```yaml
default_robot: ur5
robots:
  ur5:
    type: arm
    planning_group: manipulator
    ee_link: tool0
    base_link: base_link
    gripper: {action: "/gripper_controller/gripper_cmd"}
    named_poses: {home: [0, -1.57, 0, -1.57, 0, 0]}
    speed_limit: 0.5
    workspace: {xmin: -0.8, xmax: 0.8, ymin: -0.8, ymax: 0.8, zmin: 0.0, zmax: 1.2}
    cameras: {main: "/camera/image_raw"}
    backends: {arm: moveit, perception: perception, raw: raw}
  turtlebot:
    type: mobile
    cmd_vel: /cmd_vel
    backends: {base: nav2, perception: perception, raw: raw}
```

### Real robots

For a MoveIt arm, point the config at the robot's `*_moveit_config` package and
Robot Chalao builds the full MoveIt setup itself. No custom launch file needed;
just have the robot driver (or fake hardware) and its controllers running:

```yaml
  gen3:
    type: arm
    planning_group: manipulator
    ee_link: end_effector_link
    moveit_config_package: kinova_gen3_7dof_robotiq_2f_85_moveit_config
    moveit_robot_name: gen3
    moveit_mappings: {robot_ip: "192.168.1.10", dof: 7, gripper: robotiq_2f_85}
    gripper: {action: "/robotiq_gripper_controller/gripper_cmd"}
    named_poses: {home: [0.0, 0.26, 3.14, -2.27, 0.0, 0.96, 1.57]}
```

What has been verified, and how:

- **Live ROS 2 (CI, every push):** a real run publishes the expected `/cmd_vel`
  (ending in a stop), `/diagnostics`, `/tf_static` and raw topic messages
  (`tests/test_ros_live.py` in a `ros:jazzy` container).
- **MoveIt 2 (manual, Jazzy):** a Kinova Gen3 7-DoF on `ros2_control` fake hardware
  executes `ghar jao`, `jao joints(...)`, `kahan hai`, `joints kya hai`, `speed`,
  `planner`, `pakdo`/`chhodo` through `moveit_py`; `speed 0.1` vs `speed 0.5`
  changes the executed trajectory duration (2.1 s vs 0.55 s).
- **Not claimed:** Nav2 goal navigation, MAVROS and Gazebo have not been run
  against live stacks in CI. Test on your own robot with the e-stop in reach.

## Examples

Sab `--simulate` mein chalte hain. All run in `--simulate`:

```bash
chalao run examples/01_arm_pick_place.rc --simulate --config examples/chalao.yaml
chalao run examples/02_mobile_patrol.rc  --simulate --config examples/chalao.yaml
chalao run examples/03_camera_pick.rc    --simulate --config examples/chalao.yaml
chalao run examples/04_slam_map.rc       --simulate --config examples/chalao.yaml
chalao run examples/05_drone_square.rc   --simulate --config examples/chalao.yaml
```

1. **Arm pick and place** — go home, pick, straight-line lift, place.
2. **Mobile patrol** — patrol four waypoints, checking for obstacles.
3. **Camera pick** — find a red cup, then the arm grabs and places it.
4. **SLAM map building** — start SLAM, drive a loop, save the map.
5. **Drone square** — take off, fly a 2 m square, land.

Details in [`examples/README.md`](examples/README.md).

## Read the generated Python

Kabhi kabhi aap dekhna chahoge ki neeche kya ho raha hai. `chalao transpile` aapke
`.rc` ko padhne-layak `rclpy` + `moveit_py` + `nav2_simple_commander` Python mein badal
deta hai — seekhne aur debug karne ke liye.

```bash
chalao transpile examples/01_arm_pick_place.rc -o arm.py
```

## Mobile-base interruption handling

Timed Nav2-backend moves attempt a zero-velocity command on completion or an
exception, including Ctrl+C. Disconnect also attempts a stop before destroying
the publisher. If the stop fails during exception handling, the original failure
is preserved. Speed limits must be finite and positive; use `ruk jao` to stop.

These are best-effort ROS commands. They cannot confirm that a disconnected
robot stopped; configure the base controller's command timeout/watchdog. The
regression tests use a fake publisher and do not claim hardware validation.

## Plugin architecture

![Plugin architecture](docs/img/plugins.svg)

*Har capability ek named backend hai. Naya robot type? Ek aur backend register karo.
Each capability is a named backend; add a robot type by registering one more.*

Backends: `sim` (hamesha on), `moveit`, `nav2`, `perception`, `raw`, `control`,
`gazebo`, `mavros`. Real backends ROS ko lazily import karte hain, to package bina ROS
ke bhi import hota hai; method call par hi Hinglish error aata hai agar ROS nahi mila.

## Grammar (EBNF, chhota sa hissa)

```ebnf
statement  = let_stmt | if_stmt | while_stmt | for_stmt | func_def
           | try_stmt | print_stmt | robot_cmd | ... ;
if_stmt    = "agar" expr "toh" NEWLINE block [ "warna" NEWLINE block ] "khatam" ;
for_stmt   = "har" IDENT expr "mein" "karo" NEWLINE block "khatam" ;
robot_cmd  = [ "robot" STRING ] verb_phrase ;
```

Poora grammar / full grammar: [`docs/GRAMMAR.md`](docs/GRAMMAR.md).

## Errors sab Hinglish mein

```
Bhai, line 3: 'y' naam ki koi cheez nahi bani (undefined name 'y')
  --> patrol.rc:3
     3 |   dikhao y
Bhai, ROS 2 (rclpy) nahi mila (source your ROS 2 setup, or run with --simulate)
```

## Troubleshooting

```bash
chalao doctor
```
Yeh check karta hai rclpy, moveit_py, nav2_simple_commander, tf2, OpenCV — aur har ek
ke liye ek line ka fix deta hai. Checks each dependency and prints a one-line fix.

## VS Code

Syntax highlighting + snippets: install `robot-chalao-1.0.0.vsix` from
[Releases](https://github.com/megazron/robot-chalao/releases/latest)
(`code --install-extension robot-chalao-1.0.0.vsix`). Source in
[`vscode-extension/`](vscode-extension/).

## Roadmap

Multi-robot fleets, Hinglish behaviour trees, LLM/voice commands, aur ek web IDE —
[`docs/ROADMAP.md`](docs/ROADMAP.md). Honest status har item ke saath.

## Contributing

Naya backend, naya keyword, ya naya example — swagat hai. New backends, keywords
and examples welcome. See [CONTRIBUTING.md](CONTRIBUTING.md); every language change
lands in both the Python and native cores, and the parity tests keep them identical.
Release notes: [CHANGELOG.md](CHANGELOG.md).

## License

MIT. Banaya / built by Gaus Mohiuddin Sayyad ([megazron](https://github.com/megazron)).
