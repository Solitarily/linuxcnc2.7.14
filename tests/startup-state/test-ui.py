#!/usr/bin/env python

import linuxcnc
import hal

import math
import time
import sys
import subprocess
import os
import signal
import glob
import re


def wait_for_linuxcnc_startup(status, timeout=10.0):

    """Poll the Status buffer waiting for it to look initialized,
    rather than just allocated (all-zero).  Returns on success, throws
    RuntimeError on failure."""

    start_time = time.time()
    while time.time() - start_time < timeout:
        status.poll()
        if (status.angular_units == 0.0) \
            or (status.axes == 0) \
            or (status.axis_mask == 0) \
            or (status.cycle_time == 0.0) \
            or (status.exec_state != linuxcnc.EXEC_DONE) \
            or (status.interp_state != linuxcnc.INTERP_IDLE) \
            or (status.inpos == False) \
            or (status.linear_units == 0.0) \
            or (status.max_acceleration == 0.0) \
            or (status.max_velocity == 0.0) \
            or (status.program_units == 0.0) \
            or (status.rapidrate == 0.0) \
            or (status.state != linuxcnc.STATE_ESTOP) \
            or (status.task_state != linuxcnc.STATE_ESTOP):
            time.sleep(0.1)
        else:
            # looks good
            return

    # timeout, throw an exception
    raise RuntimeError


def print_status(status):

    """Prints all the fields of the status buffer.  Does not call
    poll()."""

    print "acceleration:", status.acceleration
    print "active_queue:", status.active_queue
    print "actual_position:", status.actual_position
    print "adaptive_feed_enabled:", status.adaptive_feed_enabled
    print "ain:", status.ain
    print "angular_units:", status.angular_units
    print "aout:", status.aout
    print "axes:", status.axes
    print "axis:", status.axis
    print "axis_mask:", status.axis_mask
    print "block_delete:", status.block_delete
    print "command:", status.command
    print "current_line:", status.current_line
    print "current_vel:", status.current_vel
    print "cycle_time:", status.cycle_time
    print "debug:", status.debug
    print "delay_left:", status.delay_left
    print "din:", status.din
    print "distance_to_go:", status.distance_to_go
    print "dout:", status.dout
    print "dtg:", status.dtg
    print "echo_serial_number:", status.echo_serial_number
    print "enabled:", status.enabled
    print "estop:", status.estop
    print "exec_state:", status.exec_state
    print "feed_hold_enabled:", status.feed_hold_enabled
    print "feed_override_enabled:", status.feed_override_enabled
    print "feedrate:", status.feedrate
    print "file:", status.file
    print "flood:", status.flood
    print "g5x_index:", status.g5x_index
    print "g5x_offset:", status.g5x_offset
    print "g92_offset:", status.g92_offset
    print "gcodes:", status.gcodes
    print "homed:", status.homed
    print "id:", status.id
    print "inpos:", status.inpos
    print "input_timeout:", status.input_timeout
    print "interp_state:", status.interp_state
    print "interpreter_errcode:", status.interpreter_errcode
    print "joint_actual_position:", status.joint_actual_position
    print "joint_position:", status.joint_position
    print "kinematics_type:", status.kinematics_type
    print "limit:", status.limit
    print "linear_units:", status.linear_units
    print "lube:", status.lube
    print "lube_level:", status.lube_level
    print "max_acceleration:", status.max_acceleration
    print "max_velocity:", status.max_velocity
    print "mcodes:", status.mcodes
    print "mist:", status.mist
    print "motion_line:", status.motion_line
    print "motion_mode:", status.motion_mode
    print "motion_type:", status.motion_type
    print "optional_stop:", status.optional_stop
    print "paused:", status.paused
    print "pocket_prepped:", status.pocket_prepped
    print "position:", status.position
    print "probe_tripped:", status.probe_tripped
    print "probe_val:", status.probe_val
    print "probed_position:", status.probed_position
    print "probing:", status.probing
    print "program_units:", status.program_units
    print "queue:", status.queue
    print "queue_full:", status.queue_full
    print "queued_mdi_commands:", status.queued_mdi_commands
    print "rapidrate:", status.rapidrate
    print "read_line:", status.read_line
    print "rotation_xy:", status.rotation_xy
    print "settings:", status.settings
    print "spindle_brake:", status.spindle_brake
    print "spindle_direction:", status.spindle_direction
    print "spindle_enabled:", status.spindle_enabled
    print "spindle_increasing:", status.spindle_increasing
    print "spindle_override_enabled:", status.spindle_override_enabled
    print "spindle_speed:", status.spindle_speed
    print "spindlerate:", status.spindlerate
    print "state:", status.state
    print "task_mode:", status.task_mode
    print "task_paused:", status.task_paused
    print "task_state:", status.task_state
    print "tool_in_spindle:", status.tool_in_spindle
    print "tool_offset:", status.tool_offset
    print "tool_table:", status.tool_table
    print "velocity:", status.velocity
    sys.stdout.flush()


def assert_axis_zeroed(axis):
    assert(axis['ferror_current'] == 0.0)
    assert(axis['max_position_limit'] == 0.0)
    assert(axis['max_ferror'] == 0.0)
    assert(axis['inpos'] == 0)
    assert(axis['ferror_highmark'] == 0.0)
    assert(axis['units'] == 0.0)
    assert(axis['input'] == 0.0)
    assert(axis['min_soft_limit'] == 0)
    assert(axis['min_hard_limit'] == 0)
    assert(axis['homing'] == 0)
    assert(axis['min_ferror'] == 0.0)
    assert(axis['max_hard_limit'] == 0)
    assert(axis['output'] == 0.0)
    assert(axis['axisType'] == 0)
    assert(axis['backlash'] == 0.0)
    assert(axis['fault'] == 0)
    assert(axis['enabled'] == 0)
    assert(axis['max_soft_limit'] == 0)
    assert(axis['override_limits'] == 0)
    assert(axis['homed'] == 0)
    assert(axis['min_position_limit'] == 0.0)
    assert(axis['velocity'] == 0.0)

def assert_axis_initialized(axis):
    assert(axis['axisType'] == 1)
    assert(axis['backlash'] == 0.0)
    assert(axis['enabled'] == 0)
    assert(axis['fault'] == 0)
    assert(axis['ferror_current'] == 0.0)
    assert(axis['ferror_highmark'] == 0.0)
    assert(axis['homed'] == 0)
    assert(axis['homing'] == 0)
    assert(axis['inpos'] == 1)
    assert(axis['input'] == 0.0)
    assert(axis['max_ferror'] == 0.05)
    assert(axis['max_hard_limit'] == 0)
    assert(axis['max_position_limit'] == 40.0)
    assert(axis['max_soft_limit'] == 0)
    assert(axis['min_ferror'] == 0.01)
    assert(axis['min_hard_limit'] == 0)
    assert(axis['min_position_limit'] == -40.0)
    assert(axis['min_soft_limit'] == 0)
    assert(axis['output'] == 0.0)
    assert(axis['override_limits'] == 0)
    assert(axis['units'] == 0.03937007874015748)
    assert(axis['velocity'] == 0.0)


c = linuxcnc.command()
s = linuxcnc.stat()
e = linuxcnc.error_channel()

# Wait for LinuxCNC to initialize itself so the Status buffer stabilizes.
wait_for_linuxcnc_startup(s)

print "status at boot up"
s.poll()
print_status(s)

# FIXME: in 2.6.12, acceleration at startup is initialized to 1e99 for some reason
#assert(s.acceleration == 0.0)

assert(s.active_queue == 0)
assert(s.actual_position == (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0))
assert(s.adaptive_feed_enabled == False)
assert(s.ain == (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0))
assert(s.angular_units == 1.0)
assert(s.aout == (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0))
assert(s.axes == 3)
assert_axis_initialized(s.axis[0])
assert_axis_initialized(s.axis[1])
assert_axis_initialized(s.axis[2])
assert_axis_zeroed(s.axis[3])
assert_axis_zeroed(s.axis[4])
assert_axis_zeroed(s.axis[5])
assert_axis_zeroed(s.axis[6])
assert_axis_zeroed(s.axis[7])
assert_axis_zeroed(s.axis[8])
assert(s.axis_mask == 0x7)

assert(s.block_delete == True)

assert(s.command == "")
assert(s.current_line == 0)
assert(s.current_vel == 0.0)
assert(s.cycle_time > 0.0)

assert(s.debug == 0)
assert(s.delay_left == 0.0)
assert(s.din == (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0))
assert(s.distance_to_go == 0.0)
assert(s.dout == (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0))
assert(s.dtg == (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0))

assert(s.echo_serial_number == 0)
assert(s.enabled == False)
assert(s.estop == 1)
assert(s.exec_state == linuxcnc.EXEC_DONE)

assert(s.feed_hold_enabled == True)
assert(s.feed_override_enabled == True)
assert(s.feedrate == 1.0)
assert(s.file == "")
assert(s.flood == 0)

assert(s.g5x_index == 1)

# mmm, floats
assert(math.fabs(s.g5x_offset[0] - 0.125) < 0.0000001)
assert(math.fabs(s.g5x_offset[1] - 0.250) < 0.0000001)
assert(math.fabs(s.g5x_offset[2] - 0.500) < 0.0000001)
assert(s.g5x_offset[3:] == (0.0, 0.0, 0.0, 0.0, 0.0, 0.0))

assert(math.fabs(s.g92_offset[0] - 1.000) < 0.0000001)
assert(math.fabs(s.g92_offset[1] - 2.000) < 0.0000001)
assert(math.fabs(s.g92_offset[2] - 4.000) < 0.0000001)
assert(s.g92_offset[3:] == (0.0, 0.0, 0.0, 0.0, 0.0, 0.0))

assert(s.gcodes == (0, 800, -1, 170, 400, 200, 900, 940, 540, 490, 990, 640, -1, 970, 911, 80))

assert(s.homed == (0, 0, 0, 0, 0, 0, 0, 0, 0))

assert(s.id == 0)
assert(s.inpos == True)
assert(s.input_timeout == False)
assert(s.interp_state == linuxcnc.INTERP_IDLE)
assert(s.interpreter_errcode == 0)

assert(s.joint_actual_position == (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0))
assert(s.joint_position == (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0))

assert(s.kinematics_type == 1)

assert(s.limit == (0, 0, 0, 0, 0, 0, 0, 0, 0))
assert(math.fabs(s.linear_units - 0.0393700787402) < 0.0000001)

assert(s.lube == 0)
assert(s.lube_level == 0)

assert(math.fabs(s.max_acceleration - 123.45) < 0.0000001)
assert(math.fabs(s.max_velocity - 45.67) < 0.0000001)
assert(s.mcodes == (0, -1, 5, -1, 9, -1, 48, -1, 53, 0))
assert(s.mist == 0)
assert(s.motion_line == 0)
assert(s.motion_mode == linuxcnc.TRAJ_MODE_FREE)
assert(s.motion_type == 0)

assert(s.optional_stop == True)

assert(s.paused == False)
assert(s.pocket_prepped == -1)
assert(s.position == (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0))
assert(s.probe_tripped == False)
assert(s.probe_val == 0)
assert(s.probed_position == (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0))
assert(s.probing == False)
assert(s.program_units == 1)

assert(s.queue == 0)
assert(s.queue_full == False)
assert(s.queued_mdi_commands == 0)

assert(s.rapidrate == 1.0)
assert(s.read_line == 0)
assert(s.rotation_xy == 0.0)

assert(s.settings == (0.0, 0.0, 0.0))
assert(s.spindle_brake == 1)
assert(s.spindle_direction == 0)
assert(s.spindle_enabled == 0)
assert(s.spindle_increasing == 0)
assert(s.spindle_override_enabled == True)
assert(s.spindle_speed == 0.0)
assert(s.spindlerate == 1.0)
assert(s.state == linuxcnc.STATE_ESTOP)

assert(s.task_mode == linuxcnc.MODE_MANUAL)
assert(s.task_paused == 0)
assert(s.task_state == linuxcnc.STATE_ESTOP)
assert(s.tool_in_spindle == 0)
assert(s.tool_offset == (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0))

assert(s.velocity == 0.0)

sys.exit(0)

