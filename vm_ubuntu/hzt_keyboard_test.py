#!/usr/bin/env python3
# encoding: utf-8

import select
import sys
import termios
import time
import tty

LINEAR_SPEED = 0.3
ANGULAR_SPEED = 0.1
INPUT_TIMEOUT = 0.25

KEY_MAP = {
    'w': ('linear_x', LINEAR_SPEED),
    's': ('linear_x', -LINEAR_SPEED),
    'a': ('linear_y', LINEAR_SPEED),
    'd': ('linear_y', -LINEAR_SPEED),
    'left': ('angular_z', ANGULAR_SPEED),
    'right': ('angular_z', -ANGULAR_SPEED),
}

KEY_LABELS = {
    'w': 'forward',
    's': 'backward',
    'a': 'left',
    'd': 'right',
    'left': 'turn left',
    'right': 'turn right',
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


class KeyboardController:
    def __init__(self):
        self.motion_state = {
            'linear_x': 0.0,
            'linear_y': 0.0,
            'angular_z': 0.0,
        }
        self.active_keys = set()
        self.last_input_time = time.time()

    def run(self):
        print('Keyboard control started. Use W/S/A/D for linear motion, left/right arrows for rotation.')
        print('Press Q or Ctrl-C to quit.')
        try:
            with TerminalReader() as reader:
                while True:
                    key = reader.read_key(timeout_sec=INPUT_TIMEOUT)
                    if key:
                        if key in ('q', '\x03', '\x04'):
                            break
                        self.handle_key(key)
                        self.last_input_time = time.time()
                        self.print_status()
                    else:
                        if time.time() - self.last_input_time > INPUT_TIMEOUT and self.active_keys:
                            self.clear_motion()
                            self.print_status()
        except KeyboardInterrupt:
            print('\nKeyboard interrupt received, exiting.')

    def handle_key(self, key):
        if key in ('w', 's'):
            self.set_linear_axis('linear_x', key)
        elif key in ('a', 'd'):
            self.set_linear_axis('linear_y', key)
        elif key in ('left', 'right'):
            self.set_angular_axis('angular_z', key)
        else:
            print(f'Unknown key: {key}')

    def set_linear_axis(self, axis, key):
        if axis == 'linear_x':
            self.motion_state['linear_x'] = KEY_MAP[key][1]
            self.active_keys.discard('w' if key == 's' else 's')
        else:
            self.motion_state['linear_y'] = KEY_MAP[key][1]
            self.active_keys.discard('a' if key == 'd' else 'd')
        self.active_keys.add(key)

    def set_angular_axis(self, axis, key):
        self.motion_state['angular_z'] = KEY_MAP[key][1]
        self.active_keys.discard('left' if key == 'right' else 'right')
        self.active_keys.add(key)

    def clear_motion(self):
        self.motion_state = {key: 0.0 for key in self.motion_state}
        self.active_keys.clear()
        print('No input detected, motion cleared.')

    def print_status(self):
        keys = sorted(self.active_keys)
        motion = {k: v for k, v in self.motion_state.items() if abs(v) > 1e-6}
        key_desc = ', '.join(keys) if keys else 'none'
        motion_desc = ', '.join(f'{axis}={value:.2f}' for axis, value in motion.items()) or 'stationary'
        action_desc = ', '.join(KEY_LABELS[k] for k in keys) if keys else 'idle'
        print(f'Keys: [{key_desc}] | Action: [{action_desc}] | Motion: [{motion_desc}]')


def main():
    controller = KeyboardController()
    controller.run()


if __name__ == '__main__':
    main()

