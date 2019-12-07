def pack_regs_addr(identifier: int, command: int) -> int:
    return ((identifier << 8) & 0xFF00) | (command & 0x00FF)

def pack_regs_value(value: float, factor: int) -> list:
    result = int(value * factor)
    return [(result & 0xFF00) | (result & 0xFF)]

def unpack_regs_value(value: list, factor: int) -> int:
    length = len(value)
    if length == 1:
        result = float(value[0]) / factor
    elif length == 2:
        result = float((value[1] << 8) | (value[0])) / factor
    else:
        result = 0
    return result

def send(modbus_client, command_name: str, value: int = 0, verbose: bool = False) -> str:
    protocol = {
        "voltage": {
            "identifier": 0x01,
            "command": 205,
            "factor": 10,
            "unit": "V"
        },
        "current": {
            "identifier": 0x02,
            "command": 205,
            "factor": 100,
            "unit": "A"
        },
        "turn_on_slow": {
            "identifier": 0x01,
            "command": 202,
            "factor": 10,
            "unit": ""
        },
        "turn_off_slow": {
            "identifier": 0x01,
            "command": 204,
            "factor": 10,
            "unit": ""
        },
        "turn_off": {
            "identifier": 0x01,
            "command": 203,
            "factor": 10,
            "unit": "s"
        },
        "turn_on_ramp_time": {
            "identifier": 0x01,
            "command": 209,
            "factor": 10,
            "unit": "s"
        },
        "turn_off_ramp_time": {
            "identifier": 0x01,
            "command": 210,
            "factor": 10,
            "unit": "s"
        },
        "read_config": {
            "identifier": 0x01,
            "command": 211,
        },
        "read_voltage": {
            "identifier": 0x00,
            "command": 212,
            "factor": 10
        },
        "read_current": {
            "identifier": 0x01,
            "command": 212,
            "factor": 1000
        },
        "read_status": {
            "identifier": 0x01,
            "command": 213,
            "factor": 3
        },
    };
    identifier = protocol[command_name]["identifier"]
    command = protocol[command_name]["command"]

    regs_addr = pack_regs_addr(identifier, command)
    if command_name == "read_config":
        regs_value = 6
        answer = modbus_client.read_holding_registers(regs_addr, regs_value)

        if answer is not None:
            factor = protocol["voltage"]["factor"]
            voltage = unpack_regs_value(answer[0:1], factor)
            factor = protocol["current"]["factor"]
            current = unpack_regs_value(answer[1:2], factor)

            print("voltage config: " + str(voltage) + " " + protocol["voltage"]["unit"])
            print("current config: " + str(current) + " " + protocol["current"]["unit"])
            answer = (voltage, current)

    elif command_name == "read_voltage":
        regs_value = 4
        answer = modbus_client.read_holding_registers(regs_addr, regs_value)

        if answer is not None:
            factor = protocol[command_name]["factor"]
            voltage = unpack_regs_value(answer[0:2], factor)

            #print("voltage: " + str(voltage) + " " + protocol["voltage"]["unit"])

            answer = voltage

    elif command_name == "read_current":
        regs_value = 4
        answer = modbus_client.read_holding_registers(regs_addr, regs_value)

        if answer is not None:
            factor = protocol[command_name]["factor"]
            current = unpack_regs_value(answer[0:2], factor)

            #print("current: " + str(current) + " " + protocol["current"]["unit"])

            answer = current
    elif command_name == "read_status":
        regs_value = 1
        answer = modbus_client.read_holding_registers(regs_addr, regs_value)
        if answer is not None:
            if answer[0] == 0:
                print("status: OFF")
                answer = False
            elif answer[0] == 10:
                print("status: ON")
                answer = True
            else:
                print("unknown: ", answer[0])
    else:
        factor = protocol[command_name]["factor"]
        regs_value = pack_regs_value(value, factor)
        answer = modbus_client.write_multiple_registers(regs_addr, regs_value)

        print("set " + command_name + " to " + str(value), end='')
        if answer is True:
            print(" -> ok")
        else:
            print(" -> error: " + str(answer))

    return answer

