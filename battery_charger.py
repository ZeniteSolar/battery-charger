#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pyModbusTCP.client import ModbusClient
import time
import operator
import atexit
import supplier

SERVER_HOST = "localhost"
#SERVER_HOST = "172.16.158.209"
SERVER_PORT = 502

c = ModbusClient()
#c.debug(True)

c.host(SERVER_HOST)
c.port(SERVER_PORT)
timeout_min = 0.1
timeout = 0.5
timeout_step = 0.1

current = 0
voltage = 0
runtime = 0
power = 0
energy = 0
capacity = 0

def turn_on():
    answer = True
    write_voltage(0)
    write_current(0)
    while answer is True:
        supplier.send(c, "turn_on_slow", 1)
        time.sleep(timeout_min)
        answer = supplier.send(c, "read_status")

def turn_off():
    answer = True
    write_voltage(0)
    write_current(0)
    while answer is True:
        supplier.send(c, "turn_off", 1)
        time.sleep(timeout_min)
        answer = supplier.send(c, "read_status")

@atexit.register
def shutdown():
    turn_off()
    c.close()
    #TODO: report results of charge program.

def test_wave():
    def triangular_wave():
        v_min = 5
        v_max = 10
        v_delta = 0.5
        cycles = 3
        seconds_per_cycle = 1
        steps = int((v_max - v_min) // v_delta)
        timeout_step = seconds_per_cycle / (steps * 2)
        voltage = v_min
        for cycle in range(cycles):
            for updown in [1, -1]:
                for step in range(steps):
                    voltage = voltage + updown * v_delta
                    answer = supplier.send(c, "voltage", voltage)
                    time.sleep(max(timeout_min, timeout_step))

    def square_wave():
        v_min = 5
        v_max = 10
        v_delta = v_max - v_min
        cycles = 3
        seconds_per_cycle = 1
        steps = int((v_max - v_min) // v_delta)
        timeout_step = seconds_per_cycle / (steps)
        voltage = v_min
        for cycle in range(cycles):
            for updown in [1, -1]:
                for step in range(steps):
                    voltage = voltage + updown * v_delta
                    answer = supplier.send(c, "voltage", voltage)
                    time.sleep(max(timeout_min, timeout_step))

    # open or reconnect TCP to server
    if not c.is_open():
        if not c.open():
            print("unable to connect to "+SERVER_HOST+":"+str(SERVER_PORT))

    if c.is_open():

        # read
        command_name = "read_config"
        answer = supplier.send(c, command_name)
        command_name = "read_voltage"
        answer = supplier.send(c, command_name)
        command_name = "read_current"
        answer = supplier.send(c, command_name)

        # write
        turn_on()
        triangular_wave()
        square_wave()
        turn_off()

    exit()

def write_voltage(value: float):
    max_tries = 10
    accepted_error = 0.5
    gain = 1.13868
    corrected_value = value*gain
    for tries in range(max_tries):
        supplier.send(c, "voltage", corrected_value)
        time.sleep(max(timeout_min, timeout_step))

        voltage_config = read_voltage_config()
        if abs(voltage_config - corrected_value) < accepted_error:
            break

    return voltage_config

def write_current(value: float):
    max_tries = 10
    accepted_error = 0.01
    corrected_value = value
    for tries in range(max_tries):
        supplier.send(c, "current", corrected_value)
        time.sleep(max(timeout_min, timeout_step))

        current_config = read_current_config()
        if abs(current_config - corrected_value) < accepted_error:
            break

    return current_config


def read_voltage_config() -> float:
    return supplier.send(c, "read_config")[0]

def read_current_config() -> float:
    return supplier.send(c, "read_config")[1]

def read_voltage() -> float:
    return supplier.send(c, "read_voltage")

def read_current() -> float:
    return supplier.send(c, "read_current")

def battery_charge():
    global runtime
    global current
    global voltage
    global power
    global energy
    global capacity

    charge_program = ["constant_voltage", "constant_current"]

    #TODO: load from json file
    states = {
        "off": {
            "settings": {
                "voltage": 0,
                "current": 0,
            },
        },
        "constant_voltage": {
            "settings": {
                "voltage": 0,
                "current": 0,
            },
            "conditions": [
                {
                    "operator": operator.lt,
                    "variable": "current",
                    "value": 1.0,
                },
                {
                    "operator": operator.gt,
                    "variable": "runtime",
                    "value": 4*3600,
                },
            ]
        },
        "constant_current": {
            "settings": {
                "voltage": 20,
                "current": 2.0,
            },
            "conditions": [
                {
                    "operator": operator.gt,
                    "variable": "voltage",
                    "value": 17,
                },
                {
                    "operator": operator.gt,
                    "variable": "runtime",
                    "value": 3600,
                },
            ]
        },
    }

    def set_state(state: int):
        #TODO: verbose it!
        settings = states[charge_program[state]]["settings"]
        write_current(settings["current"])
        write_voltage(settings["voltage"])

    def condition(state: int) -> bool:
        if "conditions" in states[charge_program[state]]:
            conditions = states[charge_program[state]]["conditions"]
            for c in conditions:
                operator = c["operator"]
                variable = globals()[c["variable"]]
                value = float(c["value"])
                #print(">>>>>>>>>>>>checking if ", variable, " is gt ", value)
                if operator(variable, value):
                    print(">>>>> Changing state due to condition", c)
                    return True
        return False

    if not c.is_open():
        if not c.open():
            print("unable to connect to " + SERVER_HOST + ":" + str(SERVER_PORT))

    if c.is_open():
        state = 0
        runtime = time.time()
        time_init = [runtime]
        time_old = runtime
        time_now = runtime
        time_delta = 0
        turn_on()
        set_state(state)

        while True:
            time_old = time_now
            time_now = time.time()
            runtime = (time_now - time_init[state])
            time_delta = time_now - time_old

            current_old = current
            voltage_old = voltage
            power_old = power

            current = read_current()
            voltage = read_voltage()

            power = current * voltage
            energy = energy + ((power + power_old) / 2) * (time_delta / 3600)
            capacity = capacity + ((current + current_old) / 2) * (time_delta / 3600)

            #TODO: LOG to csv file
            print(runtime, "s, ",
                  time_delta, "s, ",
                  voltage, "V, ",
                  current, "A, ",
                  power, "W, ",
                  energy, "Wh, ",
                  capacity, "Ah"
            )

            if condition(state):
                time_finish = time.time()
                time_init.append(time_finish)

                state = state + 1
                set_state(state)

                if state == len(charge_program):
                    break

        print("times:" + str(time_init))

        shutdown()


if__name__== "__main__":
    battery_charge()

