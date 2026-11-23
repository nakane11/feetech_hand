#!/usr/bin/env python3
"""Generate aero_with_feetech_hand*.urdf from aero_with_feetech_hand.xacro.

After xacro this script
  1. applies the l_hand_y_joint fix: aero_nohand.urdf (downloaded by skrobot) has it at
     xyz="0 0 0" while the right side is "0 0 -0.04" (carried since f5c71ea,
     "fix misalignment of l_hand_link");
  2. for each side WITHOUT the flexible wrist, moves {side}_eef_grasp_joint and
     {side}_eef_pick_joint with the hand: the IK tips in aero_nohand.urdf are defined
     assuming the wrist (the right hand of the real robot has one), so they are moved by
     T_hand(without wrist) * T_hand(with wrist)^-1, where T_hand is the pose of
     {side}_feetech_base_link in {side}_hand_link (measured from xacro outputs). The IK
     tip relative to the hand is then the same with and without the wrist.

usage:
  generate_aero_urdf.py                       # right wrist only -> urdf/aero_with_feetech_hand.urdf
  generate_aero_urdf.py -o out.urdf r_flexible_wrist:=false l_flexible_wrist:=true
"""
import argparse
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

import numpy as np

here = os.path.dirname(os.path.abspath(__file__))
urdf_dir = os.path.normpath(os.path.join(here, '..', 'urdf'))
src = os.path.join(urdf_dir, 'aero_with_feetech_hand.xacro')


def rpy_to_matrix(r, p, y):
    cr, sr, cp, sp, cy, sy = np.cos(r), np.sin(r), np.cos(p), np.sin(p), np.cos(y), np.sin(y)
    return np.array([[cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr],
                     [sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr],
                     [-sp, cp * sr, cp * cr]])


def matrix_to_rpy(R):
    p = np.arcsin(-np.clip(R[2, 0], -1, 1))
    if abs(np.cos(p)) > 1e-9:
        return np.arctan2(R[2, 1], R[2, 2]), p, np.arctan2(R[1, 0], R[0, 0])
    return np.arctan2(-R[1, 2], R[1, 1]), p, 0.0


def origin_T(joint):
    o = joint.find('origin')
    T = np.eye(4)
    if o is not None:
        T[:3, :3] = rpy_to_matrix(*[float(v) for v in o.get('rpy', '0 0 0').split()])
        T[:3, 3] = [float(v) for v in o.get('xyz', '0 0 0').split()]
    return T


def link_pose(text, base, target):
    """pose of ``target`` in ``base`` through the joint tree (joint angles 0)."""
    joints = {j.find('child').get('link'): j for j in ET.fromstring(text).findall('joint')}
    T = np.eye(4)
    link = target
    while link != base:
        if link not in joints:
            sys.exit('%s is not below %s' % (target, base))
        j = joints[link]
        T = origin_T(j) @ T
        link = j.find('parent').get('link')
    return T


def run_xacro(args):
    return subprocess.check_output(['xacro', src] + args, universal_newlines=True)


def fmt(v):
    return ' '.join('%.10g' % (0.0 if abs(x) < 1e-12 else x) for x in v)


def joint_origin_set(text, joint, xyz=None, rpy=None):
    """replace xyz / rpy of the <origin> of ``joint``; returns (text, old origin tag)."""
    pat = re.compile(r'(<joint name="%s"[^>]*>.*?)(<origin [^>]*/>)' % re.escape(joint), re.S)
    m = pat.search(text)
    if m is None:
        sys.exit('joint %s not found' % joint)
    tag = m.group(2)
    new = tag
    for key, val in (('xyz', xyz), ('rpy', rpy)):
        if val is None:
            continue
        if re.search(r'\b%s="' % key, new):
            new = re.sub(r'\b%s="[^"]*"' % key, '%s="%s"' % (key, fmt(val)), new)
        else:
            new = new.replace('<origin ', '<origin %s="%s" ' % (key, fmt(val)), 1)
    return text[:m.start(2)] + new + text[m.end(2):], tag, new


def main():
    p = argparse.ArgumentParser()
    p.add_argument('-o', '--output', default=os.path.join(urdf_dir, 'aero_with_feetech_hand.urdf'))
    p.add_argument('xacro_args', nargs='*', help='name:=value passed to xacro')
    a = p.parse_args()
    text = run_xacro(a.xacro_args)

    v = [float(x) for x in re.search(r'<joint name="l_hand_y_joint".*?<origin [^>]*xyz="([^"]+)"',
                                     text, re.S).group(1).split()]
    text, old, new = joint_origin_set(text, 'l_hand_y_joint', xyz=[v[0], v[1], -0.04])
    print('l_hand_y_joint: %s -> %s' % (old, new))

    for side in ('r', 'l'):
        if '<link name="%s_wrist_base_link"' % side in text:
            print('%s: flexible wrist' % side)
            continue
        others = [x for x in a.xacro_args if not x.startswith('%s_flexible_wrist:=' % side)]
        text_w = run_xacro(others + ['%s_flexible_wrist:=true' % side])
        hand, base = '%s_hand_link' % side, '%s_feetech_base_link' % side
        T_n, T_w = link_pose(text, hand, base), link_pose(text_w, hand, base)
        D = T_n @ np.linalg.inv(T_w)
        print('%s: no wrist, IK tips moved by %s mm (with the hand, from the wrist case)'
              % (side, fmt(np.round(D[:3, 3] * 1000, 3))))
        for j in ('%s_eef_grasp_joint' % side, '%s_eef_pick_joint' % side):
            T = D @ link_pose(text, hand, j.replace('_joint', '_link'))
            # keep the original rpy text when the hand does not turn (rpy near pitch 90 deg is not unique)
            rpy = None if np.allclose(D[:3, :3], np.eye(3), atol=1e-9) else matrix_to_rpy(T[:3, :3])
            text, old, new = joint_origin_set(text, j, xyz=T[:3, 3], rpy=rpy)
            print('  %s: %s -> %s' % (j, old, new))

    with open(a.output, 'w') as f:
        f.write(text)
    print('wrote', a.output)


if __name__ == '__main__':
    main()
