# battery-charger
A custom battery charger using a dc programmable power supply (FCCT 400-40-I from supplier.ind.br)

### Development Roadmap:
- [x] implement modbus communication with the power supply  
- [x] implement custom waveform generation  
- [x] implement voltage and current measurements  
- [x] implement capacity and energy measurements  
- [ ] transfer `states` to a _json config file_  
- [ ] transfer `charge_program` to the _json config file_  
- [ ] add the _json config file_ as an argument from _command line_  
- [ ] implement a configuration for verbosity  as an argument from _command line_  
- [ ] implement the `TCP IP` and `PORT` as an argument from _command line_ and in the _json confg file_  
- [ ] implement a _csv log_ to a file (which the name sould be passed as an argument from _command line_)
- [ ] implement a report to txt file
- [ ] callibrate voltage and current setpoint  
- [ ] callibrate voltage and current measurements  
- [ ] test with a battery  
- [ ] integrate an _Arduino Uno_ with _temperature + smoke sensors_  
- [ ] implement a _relay + fuse + connectors + buzzer_ PCB as a shield for the _Arduino Uno_  
- [ ] `supplier.py` as a _library_  

### Dependencies:
  `pyModbusTCP == 0.1.7`
  
### Setup for development:
- install dependencies

To test **without** a power supply:  
- configure `SERVER_HOST` string as `localhost`  
- run`sudo ./dumb_modus_server.py`  
- run `./battery_carger.py`  

To test **with** a power supply:
- Turn your power supply on and configure its ethernet address  
- configure `SERVER_HOST` string to the power supply ethernet address  
- connect resistors to the power supply output  
- plug your oscilloscope  
- run `./battery_carger.py`  
