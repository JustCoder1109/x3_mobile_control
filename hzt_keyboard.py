#!/usr/bin/env python
# encoding: utf-8

#public lib
# import sys
# import math
# import random
# import threading
# from math import pi
# from time import sleep
# from Rosmaster_Lib import Rosmaster
import select
import sys
import termios
import time
import tty

#ros lib
import rclpy
from rclpy.node import Node
# from std_msgs.msg import String,Float32,Int32,Bool
from geometry_msgs.msg import Twist
# from sensor_msgs.msg import Imu,MagneticField, JointState
# from rclpy.clock import Clock

LINEAR_SPEED = 0.3
ANGULAR_SPEED = 0.1
INPUT_TIMEOUT = 0.25
PUBLISH_RATE = 20.0

KEY_MAP = {
    'w': ('linear_x', LINEAR_SPEED),
    's': ('linear_x', -LINEAR_SPEED),
    'a': ('linear_y', LINEAR_SPEED),
    'd': ('linear_y', -LINEAR_SPEED),
    'left': ('angular_z', ANGULAR_SPEED),
    'right': ('angular_z', -ANGULAR_SPEED),
}


class TerminalReader:
    def __enter__(self):
        self.fd = sys.stdin.fileno()
        self.old_settings = termios.tcgetattr(self.fd)
        tty.setcbreak(self.fd)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old_settings)

    def read_key(self, timeout_sec=0.1):
        rlist, _, _ = select.select([sys.stdin], [], [], timeout_sec)
        if not rlist:
            return None
        char = sys.stdin.read(1)
        if char == '\x03':
            raise KeyboardInterrupt
        if char == '\x1b':
            seq = sys.stdin.read(2)
            if seq == '[D':
                return 'left'
            if seq == '[C':
                return 'right'
            return None
        return char.lower()


class HztKeyboardNode(Node):
    def __init__(self):
        super().__init__('hzt_keyboard')
        self.publisher = self.create_publisher(Twist, '/cmd_vel', 10)
        self.linear_state = None
        self.angular_state = None
        self.last_input_time = time.time()
        self.get_logger().info('hzt_keyboard node started. Use W/S/A/D and arrow keys to control.')
        self.get_logger().info('W/S/A/D = move, left/right arrows = turn')

    def run(self):
        try:
            with TerminalReader() as reader:
                while rclpy.ok():
                    key = reader.read_key(timeout_sec=1.0 / PUBLISH_RATE)
                    if key:
                        self.handle_key(key)
                        self.last_input_time = time.time()
                    else:
                        if time.time() - self.last_input_time > INPUT_TIMEOUT:
                            self.clear_motion()
                    self.publish_twist()
                    rclpy.spin_once(self, timeout_sec=0)
        except KeyboardInterrupt:
            self.get_logger().info('Keyboard interrupt received, stopping.')
            self.clear_motion()
            self.publish_twist()

    def handle_key(self, key):
        if key in ('w', 's', 'a', 'd'):
            self.set_linear_state(key)
        elif key in ('left', 'right'):
            self.set_angular_state(key)
        elif key in ('q', '\x03', '\x04'):
            raise KeyboardInterrupt
        else:
            return

    def set_linear_state(self, key):
        self.angular_state = self.angular_state
        if key == 'w':
            self.linear_state = ('linear_x', LINEAR_SPEED)
        elif key == 's':
            self.linear_state = ('linear_x', -LINEAR_SPEED)
        elif key == 'a':
            self.linear_state = ('linear_y', LINEAR_SPEED)
        elif key == 'd':
            self.linear_state = ('linear_y', -LINEAR_SPEED)

    def set_angular_state(self, key):
        if key == 'left':
            self.angular_state = ('angular_z', ANGULAR_SPEED)
        elif key == 'right':
            self.angular_state = ('angular_z', -ANGULAR_SPEED)

    def clear_motion(self):
        self.linear_state = None
        self.angular_state = None

    def publish_twist(self):
        twist = Twist()
        if self.linear_state:
            field, value = self.linear_state
            if field == 'linear_x':
                twist.linear.x = value
            elif field == 'linear_y':
                twist.linear.y = value
        if self.angular_state:
            _, value = self.angular_state
            twist.angular.z = value
        self.publisher.publish(twist)


def main(args=None):
    rclpy.init(args=args)
    node = HztKeyboardNode()
    try:
        node.run()
    finally:
        node.destroy_node()
        rclpy.shutdown()

