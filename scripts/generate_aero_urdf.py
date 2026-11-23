#!/usr/bin/env python3
"""Generate aero_with_feetech_hand*.urdf from aero_with_feetech_hand.xacro.

After xacro this script
  1. applies the l_hand_y_joint fix: aero_nohand.urdf (downloaded by skrobot) has it at
     xyz="0 0 0" while the right side is "0 0 -0.04" (carried since f5c71ea,
     "fix misalignment of l_hand_link");
  2. for each side WITHOUT the flexible wrist, moves {side}_eef_grasp_joint and
     {side}_eef_pick_joint toward the wrist (+z of {side}_hand_link) by
     flexible_wrist_length (urdf/flexible_wrist.xacro). The IK tips in aero_nohand.urdf
     are defined assuming the wrist (the right hand of the real robot has one).

usage:
  generate_aero_urdf.py                       # right wrist only -> urdf/aero_with_feetech_hand.urdf
  generate_aero_urdf.py -o out.urdf r_flexible_wrist:=false l_flexible_wrist:=true
"""
import argparse
import os
import re
import subprocess
import sys

here = os.path.dirname(os.path.abspath(__file__))
urdf_dir = os.path.normpath(os.path.join(here, '..', 'urdf'))


def wrist_length():
    with open(os.path.join(urdf_dir, 'flexible_wrist.xacro')) as f:
        m = re.search(r'<xacro:property name="flexible_wrist_length" value="([^"]+)"', f.read())
    return float(m.group(1))


def joint_origin_sub(text, joint, func):
    """replace the xyz of the <origin> of ``joint`` by func(list of 3 floats)."""
    pat = re.compile(r'(<joint name="%s"[^>]*>.*?<origin [^>]*xyz=")([^"]+)(")' % re.escape(joint), re.S)
    m = pat.search(text)
    if m is None:
        sys.exit('joint %s not found' % joint)
    xyz = func([float(v) for v in m.group(2).split()])
    new = ' '.join('%.10g' % v for v in xyz)
    return text[:m.start(2)] + new + text[m.end(2):], m.group(2), new


def main():
    p = argparse.ArgumentParser()
    p.add_argument('-o', '--output', default=os.path.join(urdf_dir, 'aero_with_feetech_hand.urdf'))
    p.add_argument('xacro_args', nargs='*', help='name:=value passed to xacro')
    a = p.parse_args()
    src = os.path.join(urdf_dir, 'aero_with_feetech_hand.xacro')
    text = subprocess.check_output(['xacro', src] + a.xacro_args, universal_newlines=True)

    text, old, new = joint_origin_sub(text, 'l_hand_y_joint', lambda v: [v[0], v[1], -0.04])
    print('l_hand_y_joint xyz: %s -> %s' % (old, new))

    L = wrist_length()
    for side in ('r', 'l'):
        if '<link name="%s_wrist_base_link"' % side in text:
            print('%s: flexible wrist' % side)
            continue
        for j in ('%s_eef_grasp_joint' % side, '%s_eef_pick_joint' % side):
            text, old, new = joint_origin_sub(text, j, lambda v: [v[0], v[1], v[2] + L])
            print('%s: no wrist, %s xyz: %s -> %s' % (side, j, old, new))

    with open(a.output, 'w') as f:
        f.write(text)
    print('wrote', a.output)


if __name__ == '__main__':
    main()
