# Robot Chalao — grammar and keyword reference

File extension: `.rc`. Encoding: UTF-8. Statements end at a newline; blocks close
with `khatam`. Comments start with `#`. Strings are double-quoted.

## EBNF

```ebnf
program     = { statement } ;
statement   = ( simple_stmt | compound_stmt ) NEWLINE ;

simple_stmt = let_stmt | print_stmt | return_stmt | expr_stmt
            | robot_cmd | import_stmt | break_stmt ;
let_stmt    = "maano" IDENT "=" expr ;
print_stmt  = "dikhao" expr { "," expr } ;
return_stmt = "wapas" [ expr ] ;
import_stmt = "import" STRING ;
break_stmt  = "ruko_loop" ;

compound_stmt = if_stmt | while_stmt | for_stmt | func_def
              | try_stmt | timer_stmt | subscribe_stmt | action_stmt ;
if_stmt     = "agar" expr "toh" NEWLINE block
              [ "warna" NEWLINE block ] "khatam" ;
while_stmt  = "jab" "tak" expr "karo" NEWLINE block "khatam" ;
for_stmt    = "har" IDENT expr "mein" "karo" NEWLINE block "khatam" ;
func_def    = "kaam" IDENT "(" [ params ] ")" NEWLINE block "khatam" ;
try_stmt    = "koshish" NEWLINE block
              "galti" "hone" "par" [ IDENT ] NEWLINE block "khatam" ;
timer_stmt  = "har" number time_unit "mein" NEWLINE block "khatam" ;
subscribe_stmt = "sun" STRING type_name "mein" IDENT NEWLINE block "khatam" ;
action_stmt = "action" "bhejo" STRING expr
              [ "progress" "mein" IDENT NEWLINE block ] "khatam" ;

block       = { statement } ;
params      = IDENT { "," IDENT } ;

expr        = or_expr ;
or_expr     = and_expr { "ya" and_expr } ;
and_expr    = not_expr { "aur" not_expr } ;
not_expr    = [ "nahi" ] compare ;
compare     = sum { ( "==" | "!=" | "<" | ">" | "<=" | ">=" ) sum } ;
sum         = term { ( "+" | "-" ) term } ;
term        = factor { ( "*" | "/" | "%" ) factor } ;
factor      = number | STRING | bool | IDENT | list | dict
            | call | member | typed_ctor | robot_query | "(" expr ")" ;
bool        = "sach" | "jhooth" ;
list        = "[" [ expr { "," expr } ] "]" ;
dict        = "{" [ pair { "," pair } ] "}" ;
pair        = expr ":" expr ;
call        = IDENT "(" [ expr { "," expr } ] ")" ;
member      = factor "." IDENT ;
typed_ctor  = ( "pose" | "twist" | "joints" ) "(" [ expr { "," expr } ] ")" ;
time_unit   = "second" | "minute" | "ms" ;

robot_cmd   = [ "robot" STRING ] verb_phrase ;
```

`for_stmt` (`har IDENT expr mein karo`) is told apart from `timer_stmt`
(`har number time_unit mein`) by the trailing `karo`: a for-each ends its header
with `karo`, a timer ends it with `mein`.

`robot_query` is the value-returning subset of the robot phrases (`object dhundo`,
`kahan hai`, `joints kya hai`, `battery kitni hai`, `obstacle nazdeek hai?`,
`camera dekho`, `TF pucho`, `IK nikalo`, `FK nikalo`, `lidar padho`, `depth padho`,
`imu padho`, `dabav padho`). They may appear on the right of `maano` and inside a
condition; the rest of the robot phrases are statements.

## Core keyword table (Hinglish ↔ English)

| Hinglish | English |
|---|---|
| `maano x = 5` | variable assignment |
| `agar … toh … warna … khatam` | if / else |
| `jab tak … karo … khatam` | while |
| `har x list mein karo … khatam` | for-each |
| `kaam f(a,b) … khatam` / `wapas` | function def / return |
| `dikhao …` | print |
| `sach` / `jhooth` | true / false |
| `aur` / `ya` / `nahi` | and / or / not |
| `koshish … galti hone par e … khatam` | try / except |
| `ruko_loop` | break |
| `import "x.rc"` | module import |
| `pose(...)` `twist(...)` `joints(...)` | typed constructors |

## Robot command mapping (Hinglish → ROS 2 / library)

### Connection
| Hinglish | Backend method → ROS |
|---|---|
| `robot jodo "ur5"` | `connect` → init rclpy node + backends from config |
| `robot chhodo` | `disconnect` → shutdown |
| `namespace "r1"` | `set_namespace` |
| `param set "k" v` / `param get "k"` | `param_set` / `param_get` → Set/GetParameters |

### Arm (MoveIt 2 via moveit_py)
| Hinglish | Method → ROS |
|---|---|
| `ghar jao` | `arm_home` → named target `home` |
| `jao pose(x,y,z,r,p,yw)` / `jao <var>` | `arm_pose` → set_pose_target + plan + execute |
| `jao joints(...)` | `arm_joints` → joint-space target |
| `seedha jao (x,y,z)` | `arm_cartesian` → compute_cartesian_path |
| `named pose "ready"` | `arm_named` → named target |
| `pakdo` / `chhodo` | `gripper(close=True/False)` |
| `speed 0.5` | `set_speed` → max_velocity_scaling |
| `planner "RRTConnect"` | `set_planner` → set_planner_id |
| `rukawat jodo "box" (x,y,z) size(a,b,c)` | `add_obstacle` → PlanningScene |
| `rukawat hatao` / `attach "box"` / `detach "box"` | `remove_obstacle` / `attach` / `detach` |
| `kahan hai` / `joints kya hai` | `get_pose` / `get_joints` |
| `IK nikalo pose` / `FK nikalo joints` | `ik` / `fk` → /compute_ik, /compute_fk |

### Mobile base (Nav2 + cmd_vel)
| Hinglish | Method → ROS |
|---|---|
| `aage chalo 1 meter` / `peeche chalo 1 meter` | `base_move` → timed cmd_vel |
| `ghumo 90 degree` | `base_rotate` |
| `speed_move v w` / `ruk jao` | `base_twist` / `base_stop` |
| `map load "f"` / `localize` | `map_load` / `localize` (AMCL) |
| `yahan jao (x,y,theta)` | `nav_to` → nav2_simple_commander goToPose |
| `waypoints follow [...]` | `follow_waypoints` → followWaypoints |
| `map banao` / `map save "n"` | `slam_start` / `map_save` |
| `obstacle nazdeek hai?` | `obstacle_near` → costmap/scan → bool |

### Perception
| Hinglish | Method → ROS |
|---|---|
| `camera dekho "/img"` / `photo lo "f.png"` | `camera_view` / `photo` (cv_bridge) |
| `object dhundo "red cup"` | `find_object` → detector plugin (YOLO/OpenCV) |
| `lidar padho` / `depth padho` / `imu padho` / `dabav padho` | `read_lidar` / `read_depth` / `read_imu` / `read_ft` |
| `battery kitni hai` | `battery` → BatteryState |
| `AprilTag dhundo` / `ArUco dhundo` | `find_apriltag` / `find_aruco` |
| `TF pucho "base" se "tool"` | `tf` → tf2 lookup_transform |

### Raw ROS 2
| Hinglish | Method → ROS |
|---|---|
| `sun "topic" type mein x … khatam` | `subscribe` |
| `bolo "topic" value` | `publish` |
| `sewa bulao "service" args` | `call_service` |
| `action bhejo "name" goal … progress mein p … khatam` | `send_action` |
| `nodes dikhao` / `topics dikhao` | `list_nodes` / `list_topics` |
| `record shuru "bag"` / `record band` | `record_start` / `record_stop` (rosbag2) |
| `launch "pkg" "file.launch.py"` | `launch` |
| `urdf load "robot.urdf"` | `urdf_load` |

### ros2_control
| Hinglish | Method → ROS |
|---|---|
| `joint "j1" ko 1.2 rad pe le jao` | `joint_to` |
| `controller switch "name"` | `controller_switch` |
| `torque on` / `torque off` | `torque(on=True/False)` |

### Simulation
| Hinglish | Method → ROS |
|---|---|
| `simulation shuru gazebo "world"` | `sim_start` |
| `spawn "model" (x,y,z)` | `spawn` |
| `simulation band` / `rviz kholo` | `sim_stop` / `rviz_open` |

### Safety and timing
| Hinglish | Meaning |
|---|---|
| `band karo` | e-stop → `estop`, cancels all actions/timers |
| `workspace limit (...)` / `speed limit v` | `set_workspace_limit` / `set_speed_limit` |
| `ruko 2 second` | interpreter sleep |
| `har 0.1 second mein … khatam` | timer loop (`Timer` node) |
| `deadline 5 second` | run the following with a time budget |

### Drone (MAVROS)
| Hinglish | Method → ROS |
|---|---|
| `udaan bharo` / `utro` | `takeoff` / `land` |
| `height 2 meter` | `set_height` |

## Short aliases

Robot Chalao ships short aliases for the longer keywords. Each alias is rewritten
to its canonical keyword in the lexer, so aliases work everywhere the canonical
keyword works, old programs are unaffected, and the native C++ core and the Python
reference produce byte-identical output. Because they are lexer-level keywords,
these words are reserved and cannot be used as identifiers.

| Short | Canonical | Meaning |
|---|---|---|
| `bas` | `khatam` | end a block |
| `bol` | `dikhao` | print |
| `rakh` | `maano` | variable binding |
| `try` | `koshish` | try |
| `de` | `wapas` | return |
| `tod` | `ruko_loop` | break a loop |
