#!/usr/bin/env python3
"""Convert the flexible (passive) wrist parts to URDF meshes.

Source: meshes/flexible_wrist/src/adjustable-ft-v33.scad, exported per part by
scripts/export_flexible_wrist_scad.ps1 (OpenSCAD on Windows):
  scad_top.stl     hand_base_plate()  z  4.0 .. 24.5 mm   -> wrist_top.stl
  scad_base.stl    base_ring()        z  0.0 ..  9.5 mm   -> wrist_base.stl
  scad_bottom.stl  stopper_ring()     z -7.0 ..  0.0 mm   -> wrist_bottom.stl
These keep the SCAD frame, in meters:
  origin = bottom face of the inner core (robot side attachment face),
  +z     = toward the hand.
(The 0.5 mm lift of wrist_top is applied in urdf/flexible_wrist.xacro.)

The arm adapter meshes/hand_mount/wrist_to_arm.STL (robot flange <-> inner core, 24 mm) is
converted to wrist_adapter.stl in meters, keeping its own frame (z 0 = core side, z 24 mm =
robot flange side, axis at x = y = 26.52 mm); urdf/flexible_wrist.xacro places it.
"""
import os
import numpy as np
import trimesh

here = os.path.dirname(os.path.abspath(__file__))
mesh_dir = os.path.join(here, '..', 'meshes', 'flexible_wrist')
src_dir = os.path.join(mesh_dir, 'src')
hand_mount_dir = os.path.join(here, '..', 'meshes', 'hand_mount')


def convert(src, dst):
    m = trimesh.load(src)
    m.apply_scale(0.001)
    m.export(os.path.join(mesh_dir, dst))
    print(dst, np.round(m.bounds * 1000, 2).tolist(), 'watertight', m.is_watertight)


def main():
    for part in ['top', 'base', 'bottom']:
        convert(os.path.join(src_dir, 'scad_%s.stl' % part), 'wrist_%s.stl' % part)
    convert(os.path.join(hand_mount_dir, 'wrist_to_arm.STL'), 'wrist_adapter.stl')


if __name__ == '__main__':
    main()
