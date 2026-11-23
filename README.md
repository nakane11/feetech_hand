# feetech_hand

Feetech サーボのハンドのモデル (URDF・メッシュ) と、ハンドを AERO に付けた URDF の作り方をまとめたパッケージです。

## ファイル

| パス | 内容 |
|---|---|
| `urdf/feetech_hand_dae.urdf` / `feetech_hand.urdf` | ハンド単体 (launch/display.launch・gazebo.launch で使う) |
| `urdf/feetech_hand.xacro` | ハンド単体のマクロ `feetech_hand` (prefix 付き) |
| `urdf/flexible_wrist.xacro` | 受動手首とアダプタのマクロ `flexible_wrist`。手首の長さ `flexible_wrist_length` (0.049 m) |
| `urdf/flexible_wrist_standalone.xacro` | 受動手首だけを確認するための URDF |
| `urdf/aero_with_feetech_hand.xacro` | AERO (aero_nohand.urdf) の両手にハンドを付ける xacro |
| `urdf/aero_with_feetech_hand.urdf` | 上の xacro から作った URDF (右手だけ手首あり)。aero_demo はこれを使う |
| `scripts/generate_aero_urdf.py` | `aero_with_feetech_hand.urdf` を作るスクリプト |
| `meshes/hand_mount/wrist.STL` | 手首なしのときのハンドの底板 (ロボットに直接ねじ止め)。ハンドのメッシュ `base_link.dae` の底面と同じ |
| `meshes/hand_mount/wrist_ver2.STL` | 手首ありのときのハンドの底板 (wrist_top にねじ止め)。外形・厚さ 4.5 mm は wrist.STL と同じ |
| `meshes/hand_mount/wrist_to_arm.STL` | ロボットのフランジと手首の内輪をつなぐアダプタ (24 mm) |
| `meshes/flexible_wrist/wrist_{top,base,bottom}.stl` | 受動手首の 3 部品 (m 単位、SCAD の座標系のまま) |
| `meshes/flexible_wrist/wrist_adapter.stl` | `wrist_to_arm.STL` を m 単位にしたもの |
| `meshes/flexible_wrist/src/` | 元の SCAD (`adjustable-ft-v33.scad`) と、そこから書き出した STL (mm 単位) |
| `scripts/export_flexible_wrist_scad.ps1` | SCAD から 3 部品を STL に書き出す (Windows の OpenSCAD) |
| `scripts/build_flexible_wrist_meshes.py` | 書き出した STL とアダプタを m 単位にして `wrist_*.stl` を作る |

`meshes/hand_mount/` の 3 つは Google Drive の `d2_hand/designed/stl/` からのコピーです。

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
| `r_flexible_wrist` | `true` | 右手に受動手首 (アダプタ込み) を入れる |
| `l_flexible_wrist` | `false` | 左手に受動手首 (アダプタ込み) を入れる |
| `wrist_yaw` | `0.0` | 手首をハンドの軸まわりに回す角度 [rad]。見た目だけで、ハンドの位置・向きは変わらない |

`check_urdf urdf/aero_with_feetech_hand.urdf` でリンクの木を確認できます。

### generate_aero_urdf.py が xacro の後に行うこと

1. **`l_hand_y_joint` の手直し**: skrobot が落とす `aero_nohand.urdf` では左だけ `xyz="0 0 0"` になっているので、右と同じ `0 0 -0.04` にします (f5c71ea の修正)。
2. **手首のない側の IK の手先をハンドと一緒に動かす**: `aero_nohand.urdf` の IK の手先 (`{r,l}_eef_grasp_joint`・`{r,l}_eef_pick_joint`) は、手首がある前提の位置になっています。手首のない側では、手首ありの場合のハンドの位置からの差 (xacro を手首ありでも走らせて測る) だけ、この 2 つの joint を動かします。今の寸法では、手首側に 49 mm、横に (4.87, ∓4.65) mm (右/左、`{side}_hand_link` の x, y) です。

## 手首とハンドの位置の決め方

ロボットのフランジ面は `{side}_hand_link` の z = 10 mm の面で、ハンドを留める 4 つのねじ穴 (20 × 39.7 mm) はその z 軸を中心に並んでいます (AERO の `hand_yaw/wrist.dae`)。

- **手首なし**: ハンドの底板 `wrist.STL` の 20 × 39.7 mm の穴の中心を、フランジの穴の中心 (`hand_link` の z 軸) に合わせます。
- **手首あり**: ロボット → アダプタ `wrist_to_arm` (24 mm) → 内輪 (ばね) → bottom・外輪・top → 底板 `wrist_ver2` → ハンド の順に付きます。
  - アダプタのロボット側の穴は底板 `wrist.STL` と同じ 20 × 39.7 mm で、手首の軸はフランジの穴の中心です。
  - ハンドは、`wrist_ver2.STL` の 3 つのねじ穴 (半径 18 mm、wrist_top の穴と合う) の中心を手首の軸に合わせます。この中心は底板の上で 20 × 39.7 mm の穴の中心から (4.87, −4.65) mm (右手) ずれているので、ハンドは手首なしのときより横にもずれます。
  - ハンドの向きは手首なしのときと同じです。
  - ハンドは手首なしのときより 49.0 mm 先に出ます。アダプタ 24 mm と、内輪の下面から top の先端まで 25 mm の和で、底板はどちらも 4.5 mm なので差し引きゼロです。
- **IK の手先** (`{r,l}arm_end_coords`) は、どちらの場合も**ハンドから見て同じ位置**になります。手首ありの側は元の `aero_nohand.urdf` の位置のままで、手首なしの側はハンドと一緒に動かします。

手首の部品のリンクは `{side}_wrist_adapter_link`・`{side}_wrist_bottom_link`・`{side}_wrist_base_link`・`{side}_wrist_top_link` です。干渉判定用の collision は次のとおりです。
- アダプタ: 34.2 × 49.7 × 24 mm の箱
- 手首の 3 部品: 半径 31 mm の円柱

2026-11 より前の URDF は、手首なしのときのハンドの穴がフランジの穴から 9 mm ずれていました (`hand_x`・`hand_y` が 0.01・±0.004)。

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
2. WSL で m 単位の `wrist_*.stl` を作ります (trimesh を使います)。アダプタ (`meshes/hand_mount/wrist_to_arm.STL`) もここで変換されます。
   ```bash
   python3 scripts/build_flexible_wrist_meshes.py
   ```
3. 部品の寸法が変わったら `urdf/flexible_wrist.xacro` を直し、`generate_aero_urdf.py` で URDF を作り直します。直すのは次の値です。
   - アダプタの長さ `flexible_wrist_adapter_length`
   - 内輪の下面から top の先端まで `flexible_wrist_core_to_hand`
   - 質量・慣性
   - collision の範囲

   ハンドの底板の穴が変わったら、`aero_with_feetech_hand.xacro` の `hand_x`・`hand_y`・`hand_x_wrist`・`hand_y_wrist` も直します。

注意:

- SCAD のままだと top (`hand_base_plate`、z = 4.0 mm から) が base の外輪 (高さ 4.5 mm) と 0.5 mm 重なります。URDF では top を 0.5 mm 上げています。
- 各部品の座標の原点は SCAD の原点 (内輪の下面) のままです。base は z 0〜9.5 mm、bottom (`stopper_ring`) は z −7〜0 mm です。

## 注意

- `aero_with_feetech_hand.xacro` の include は、次の 2 か所を絶対パスで参照しています。別の環境で使うときは書き換えてください。
  - `/home/leus/.skrobot/...`
  - `/home/leus/ros/hand/src/feetech_hand/...`
- AERO の `hand_yaw/wrist.dae` のフランジの穴 (20 × 39.7 mm) は長い辺が `hand_link` の x 向きですが、URDF のハンドの底板の穴は長い辺が y 向きで、90° 違います。実機に合わせてハンドの向きは元の URDF のままにしているので、dae の穴の向きの方が実機と違う可能性があります。
