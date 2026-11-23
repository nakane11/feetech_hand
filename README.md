# feetech_hand

Feetech サーボのハンドのモデル (URDF・メッシュ) と、ハンドを AERO に付けた URDF の作り方をまとめたパッケージです。

## ファイル

| パス | 内容 |
|---|---|
| `urdf/feetech_hand_dae.urdf` / `feetech_hand.urdf` | ハンド単体 (launch/display.launch・gazebo.launch で使う) |
| `urdf/feetech_hand.xacro` | ハンド単体のマクロ `feetech_hand` (prefix 付き) |
| `urdf/flexible_wrist.xacro` | 受動手首のマクロ `flexible_wrist` と手首の長さ `flexible_wrist_length` (0.032 m) |
| `urdf/flexible_wrist_standalone.xacro` | 受動手首だけを確認するための URDF |
| `urdf/aero_with_feetech_hand.xacro` | AERO (aero_nohand.urdf) の両手にハンドを付ける xacro |
| `urdf/aero_with_feetech_hand.urdf` | 上の xacro から作った URDF (右手だけ手首あり)。aero_demo はこれを使う |
| `scripts/generate_aero_urdf.py` | `aero_with_feetech_hand.urdf` を作るスクリプト |
| `meshes/flexible_wrist/wrist_{top,base,bottom}.stl` | 受動手首の 3 部品 (m 単位、SCAD の座標系のまま) |
| `meshes/flexible_wrist/src/` | 元の SCAD (`adjustable-ft-v33.scad`) と、そこから書き出した STL (mm 単位) |
| `scripts/export_flexible_wrist_scad.ps1` | SCAD から 3 部品を STL に書き出す (Windows の OpenSCAD) |
| `scripts/build_flexible_wrist_meshes.py` | 書き出した STL を m 単位にして `wrist_*.stl` を作る |

## AERO + ハンドの URDF を作る

xacro だけでは作らず、必ず `generate_aero_urdf.py` を使ってください (理由は後述)。ROS noetic の環境で実行します。

```bash
source /opt/ros/noetic/setup.bash
cd ~/ros/hand/src/feetech_hand
python3 scripts/generate_aero_urdf.py
# -> urdf/aero_with_feetech_hand.urdf (右手だけ手首あり、実機と同じ)
```

手首の有無は左右別に xacro の引数で指定します。`-o` で出力先を変えられます。

```bash
python3 scripts/generate_aero_urdf.py -o /tmp/aero_both.urdf l_flexible_wrist:=true
python3 scripts/generate_aero_urdf.py -o /tmp/aero_none.urdf r_flexible_wrist:=false
```

| 引数 | 既定 | 意味 |
|---|---|---|
| `r_flexible_wrist` | `true` | 右手に受動手首を入れる |
| `l_flexible_wrist` | `false` | 左手に受動手首を入れる |
| `wrist_yaw` | `0.0` | 手首をハンドの軸まわりに回す角度 [rad]。見た目だけで、ハンドの位置・向きは変わらない |

`check_urdf urdf/aero_with_feetech_hand.urdf` でリンクの木を確認できます。

### generate_aero_urdf.py が xacro の後に行うこと

1. **`l_hand_y_joint` の手直し**: skrobot が落とす `aero_nohand.urdf` では左だけ `xyz="0 0 0"` になっているので、右と同じ `0 0 -0.04` にします (f5c71ea の修正)。
2. **手首のない側の IK の手先を寄せる**: `aero_nohand.urdf` の IK の手先 (`{r,l}_eef_grasp_joint`・`{r,l}_eef_pick_joint`) は、手首がある前提の位置になっています。手首のない側では、この 2 つの joint を手首の長さ (32 mm) だけ手首側 (`{side}_hand_link` の +z) に寄せます。

## 手首とハンドの位置の決め方

- 手首なし: ハンドは元の URDF の位置 (`{side}_hand_link` のハンド取り付け面) に付きます。
- 手首あり: 手首の bottom の底面を元のハンド取り付け面に置き、ハンドは向きを変えずに手首の長さ 32.0 mm (bottom の底面〜top の先端) だけ先へ出ます。
- IK の手先 (`{r,l}arm_end_coords`) は、どちらの場合も**ハンドから見て同じ位置**になります。手首ありの側はハンドが 32 mm 先に出て手先は元のまま、手首なしの側はハンドが元のままで手先が 32 mm 手首側に寄ります。

手首の部品のリンクは `{side}_wrist_bottom_link`・`{side}_wrist_base_link`・`{side}_wrist_top_link` です。干渉判定用に、それぞれ半径 31 mm の円柱を collision に入れています。

## aero_demo での使われ方

- aero_demo は `urdf/aero_with_feetech_hand.urdf` を `~/.skrobot/aero_description/typeJSK/urdf/` にコピーして読み込みます。コピーされるのはこちらの方が新しいときだけです。
- 干渉判定用の `aero_with_feetech_hand_primitives*.urdf` も同じ場所に作られ、元の URDF が新しくなると作り直されます。
- `~/.skrobot` は全 worktree で共有されています。URDF を作り直すと、すべての worktree で、次に読み込むときから新しいモデルになります。

## 受動手首のメッシュを作り直す

SCAD (`meshes/flexible_wrist/src/adjustable-ft-v33.scad`) を変えたときの手順です。原本は Google Drive の `d2_hand/flexible_wrist/` にあります。

1. Windows の PowerShell で 3 部品を STL に書き出します (OpenSCAD 2021.01、`C:\Program Files\OpenSCAD\openscad.com` を使います)。
   ```powershell
   powershell -File scripts\export_flexible_wrist_scad.ps1
   # -> meshes/flexible_wrist/src/scad_{base,top,bottom}.stl
   ```
2. WSL で m 単位の `wrist_*.stl` を作ります (trimesh を使います)。
   ```bash
   python3 scripts/build_flexible_wrist_meshes.py
   ```
3. 部品の寸法が変わったら `urdf/flexible_wrist.xacro` を直し、`generate_aero_urdf.py` で URDF を作り直します。直すのは次の値です。
   - 長さ `flexible_wrist_length`
   - bottom の厚さ `flexible_wrist_bottom_thickness`
   - 質量・慣性
   - collision の範囲

注意:

- SCAD のままだと top (`hand_base_plate`、z = 4.0 mm から) が base の外輪 (高さ 4.5 mm) と 0.5 mm 重なります。URDF では top を 0.5 mm 上げています。
- 各部品の座標の原点は SCAD の原点のままです。base は z 0〜9.5 mm、bottom (`stopper_ring`) は z −7〜0 mm です。

## 注意

`aero_with_feetech_hand.xacro` の include は、次の 2 か所を絶対パスで参照しています。別の環境で使うときは書き換えてください。

- `/home/leus/.skrobot/...`
- `/home/leus/ros/hand/src/feetech_hand/...`
