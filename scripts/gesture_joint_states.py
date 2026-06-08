#!/usr/bin/env python
from __future__ import print_function

import math

import rospy
from sensor_msgs.msg import JointState


PULLEY_LIMITS = {
    "index": (0.0, 1.57079),
    "middle": (0.0, 1.57079),
    "ring": (0.0, 1.57079),
    "little": (0.0, 1.57079),
    "abduction": (0.0, 0.6),
    "thumb0": (0.0, 1.75),
    "thumb": (0.0, 1.57079),
}

JOINT_NAMES = [
    "index_pulley_joint",
    "middle_pulley_joint",
    "ring_pulley_joint",
    "little_pulley_joint",
    "index0_joint",
    "index1_joint",
    "index2_joint",
    "index3_joint",
    "middle0_joint",
    "middle1_joint",
    "middle2_joint",
    "middle3_joint",
    "ring0_joint",
    "ring1_joint",
    "ring2_joint",
    "ring3_joint",
    "little0_joint",
    "little1_joint",
    "little2_joint",
    "little3_joint",
    "abduction_pulley_joint",
    "thumb0_joint",
    "thumb1_joint",
    "thumb2_joint",
    "thumb_pulley_joint",
]

OPEN = {
    "index": 0.05,
    "middle": 0.04,
    "ring": 0.05,
    "little": 0.06,
    "abduction": 0.16,
    "thumb0": 0.28,
    "thumb": 0.10,
}

RELAXED = {
    "index": 0.35,
    "middle": 0.28,
    "ring": 0.38,
    "little": 0.48,
    "abduction": 0.20,
    "thumb0": 0.50,
    "thumb": 0.35,
}

GESTURES = [
    ("open", OPEN, 1.5, 0.7),
    ("relaxed", RELAXED, 1.8, 0.8),
    ("wave_open", {
        "index": 0.14,
        "middle": 0.10,
        "ring": 0.16,
        "little": 0.20,
        "abduction": 0.46,
        "thumb0": 0.38,
        "thumb": 0.16,
    }, 1.4, 0.6),
    ("point", {
        "index": 0.10,
        "middle": 1.18,
        "ring": 1.25,
        "little": 1.30,
        "abduction": 0.20,
        "thumb0": 0.65,
        "thumb": 0.95,
    }, 1.7, 1.0),
    ("peace", {
        "index": 0.10,
        "middle": 0.10,
        "ring": 1.25,
        "little": 1.30,
        "abduction": 0.34,
        "thumb0": 0.70,
        "thumb": 1.00,
    }, 1.7, 1.0),
    ("pinch", {
        "index": 0.88,
        "middle": 0.38,
        "ring": 0.52,
        "little": 0.62,
        "abduction": 0.16,
        "thumb0": 1.10,
        "thumb": 1.05,
    }, 1.6, 1.0),
    ("fist", {
        "index": 1.38,
        "middle": 1.42,
        "ring": 1.44,
        "little": 1.46,
        "abduction": 0.10,
        "thumb0": 1.22,
        "thumb": 1.18,
    }, 1.9, 1.0),
    ("thumbs_up", {
        "index": 1.28,
        "middle": 1.32,
        "ring": 1.36,
        "little": 1.38,
        "abduction": 0.14,
        "thumb0": 0.10,
        "thumb": 0.08,
    }, 1.7, 1.1),
    ("relaxed", RELAXED, 1.8, 0.8),
]


def clamp(value, lower, upper):
    return max(lower, min(upper, value))


def smoothstep(x):
    x = clamp(x, 0.0, 1.0)
    return x * x * x * (x * (x * 6.0 - 15.0) + 10.0)


def clamped_pose(pose):
    result = {}
    for key, value in pose.items():
        lower, upper = PULLEY_LIMITS[key]
        result[key] = clamp(value, lower, upper)
    return result


def interpolate_pose(start, goal, progress):
    result = {}
    for key in PULLEY_LIMITS:
        result[key] = start[key] + (goal[key] - start[key]) * progress
    return result


def add_human_motion(pose, elapsed, amount):
    """Add small low-frequency variation so poses do not look robotic."""
    offsets = {
        "index": math.sin(elapsed * 2.1 + 0.2) * 0.018,
        "middle": math.sin(elapsed * 1.8 + 1.3) * 0.014,
        "ring": math.sin(elapsed * 1.6 + 2.2) * 0.016,
        "little": math.sin(elapsed * 1.9 + 2.9) * 0.018,
        "abduction": math.sin(elapsed * 1.2 + 0.7) * 0.010,
        "thumb0": math.sin(elapsed * 1.7 + 1.9) * 0.015,
        "thumb": math.sin(elapsed * 2.0 + 2.7) * 0.014,
    }
    result = {}
    for key, value in pose.items():
        lower, upper = PULLEY_LIMITS[key]
        result[key] = clamp(value + offsets[key] * amount, lower, upper)
    return result


def expand_mimic_joints(pose):
    index = pose["index"]
    middle = pose["middle"]
    ring = pose["ring"]
    little = pose["little"]
    abduction = pose["abduction"]
    thumb0 = pose["thumb0"]
    thumb = pose["thumb"]

    return [
        index,
        middle,
        ring,
        little,
        abduction,
        index,
        index,
        index,
        abduction * 0.3333,
        middle,
        middle,
        middle,
        abduction * 0.3333,
        ring,
        ring,
        ring,
        abduction,
        little,
        little,
        little,
        abduction,
        thumb0,
        thumb,
        thumb,
        thumb,
    ]


def publish_pose(publishers, pose):
    msg = JointState()
    msg.header.stamp = rospy.Time.now()
    msg.name = list(JOINT_NAMES)
    msg.position = expand_mimic_joints(pose)
    msg.velocity = []
    msg.effort = []
    for pub in publishers:
        pub.publish(msg)


def run():
    rospy.init_node("feetech_hand_gesture_joint_states")

    topic = rospy.get_param("~topic", "/joint_states")
    alias_topic = rospy.get_param("~alias_topic", "/joint_state")
    rate_hz = rospy.get_param("~rate", 50.0)
    loop = rospy.get_param("~loop", True)
    human_motion = rospy.get_param("~human_motion", 1.0)
    hold_scale = rospy.get_param("~hold_scale", 1.0)
    transition_scale = rospy.get_param("~transition_scale", 1.0)

    topics = [topic]
    if alias_topic and alias_topic not in topics:
        topics.append(alias_topic)
    publishers = [rospy.Publisher(name, JointState, queue_size=10)
                  for name in topics]
    rate = rospy.Rate(rate_hz)

    rospy.loginfo("Publishing Feetech hand gestures to %s", ", ".join(topics))

    current = clamped_pose(OPEN)
    sequence = [(name, clamped_pose(pose), transition, hold)
                for name, pose, transition, hold in GESTURES]

    while not rospy.is_shutdown():
        for name, goal, transition_time, hold_time in sequence:
            if rospy.is_shutdown():
                return

            transition_time = max(0.05, transition_time * transition_scale)
            hold_time = max(0.0, hold_time * hold_scale)
            start = dict(current)
            started = rospy.Time.now()

            rospy.loginfo("Gesture: %s", name)
            while not rospy.is_shutdown():
                elapsed = (rospy.Time.now() - started).to_sec()
                progress = smoothstep(elapsed / transition_time)
                pose = interpolate_pose(start, goal, progress)
                pose = add_human_motion(pose, rospy.get_time(), human_motion)
                publish_pose(publishers, pose)

                if elapsed >= transition_time:
                    break
                rate.sleep()

            current = dict(goal)
            hold_started = rospy.Time.now()
            while not rospy.is_shutdown():
                elapsed = (rospy.Time.now() - hold_started).to_sec()
                pose = add_human_motion(current, rospy.get_time(), human_motion * 0.5)
                publish_pose(publishers, pose)

                if elapsed >= hold_time:
                    break
                rate.sleep()

        if not loop:
            rospy.signal_shutdown("gesture sequence completed")


if __name__ == "__main__":
    try:
        run()
    except rospy.ROSInterruptException:
        pass
