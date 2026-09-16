# Examples — Robot Chalao

Har example `--simulate` mode mein bina ROS ke chalta hai. Har example runs in
`--simulate` mode with zero ROS installed; the simulator prints, in Hinglish,
exactly the ROS 2 calls it would make.

```bash
# har example ko aise chalao / run any example like this:
chalao run examples/01_arm_pick_place.rc --simulate --config examples/chalao.yaml
chalao run examples/02_mobile_patrol.rc  --simulate --config examples/chalao.yaml
chalao run examples/03_camera_pick.rc    --simulate --config examples/chalao.yaml
chalao run examples/04_slam_map.rc       --simulate --config examples/chalao.yaml
chalao run examples/05_drone_square.rc   --simulate --config examples/chalao.yaml
```

Asli robot par chalane ke liye `--simulate` hata do aur apna ROS 2 source kar lo.
To run on a real robot, drop `--simulate` and source your ROS 2 workspace first.

## 01 — Arm pick and place
`robot jodo` se ek 7-DOF arm (ur5) se jud kar, ghar pose se ek object uthata hai
aur doosri jagah rakhta hai. Connects to a 7-DOF arm, goes home, picks an object
with the gripper, moves it in a straight Cartesian line, and places it. Shows
`ghar jao`, `jao pose(...)`, `seedha jao`, `pakdo`/`chhodo`, `speed`.

## 02 — Mobile patrol
Ek mobile base chaar waypoint ke beech do baar gasht karta hai, aur har waypoint
se pehle rukawat check karta hai. A mobile base patrols four waypoints twice,
checking `obstacle nazdeek hai?` before each move. Shows `localize`, a `jab tak`
loop, a `har ... mein karo` loop, `yahan jao (x,y,theta)`, `ruk jao`.

## 03 — Camera pick
Camera se "red cup" dhoondh kar, arm us tak jaata hai, pakadta hai, aur rakh deta
hai. The camera finds a red cup, the arm approaches from above, grasps, lifts and
places it. Shows `object dhundo`, member access on the returned `Detection`
(`cup.pose.x`), `agar ... warna`, `pakdo`/`chhodo`.

## 04 — SLAM map building
`map banao` se mapping shuru kar ke robot ek chhota chakkar lagata hai aur `map
save` se map save karta hai. Starts SLAM, drives a small exploration loop, and
saves the map. Shows `map banao`, `aage chalo`, `ghumo`, `map save`.

## 05 — Drone square
Drone udta hai, 2 meter oonchai par ek square banata hai, phir utar jaata hai.
The drone takes off, flies a 2 m square, and lands. Shows `udaan bharo`,
`height`, `aage chalo`/`ghumo` in a `har` loop, `utro`.

### Drone config
Example 05 ke liye `chalao.yaml` mein ek `drone` robot chahiye / example 05 needs
a `drone` entry in `chalao.yaml`:

```yaml
  drone:
    type: drone
    backends: {drone: mavros, base: mavros}
```
