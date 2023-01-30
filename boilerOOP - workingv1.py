#!/usr/bin/env python3
import sys
import argparse
import json
import time
from datetime import datetime

import solaredge_modbus

from Controller import Controller
from Dimmer import Dimmer
from Inverter import Inverter

controller = Controller("192.168.58.104", 60)
dimmer = Dimmer(2000)
inverterM = Inverter(3000, 400)

def calculateDimValue(solar, consumption, export):
#for x, dict in enumerate(inverterM.data):
    #consumptionTotal = (inverterM.data[x].get("Consumption")) + (dimmer.value * dimmer.maxWattage)
    #export = max(0, inverterM.data[x].get("Solar") - consumptionTotal) #export cannot be less than 0
    #export = min(inverterM.exportmax, export) # export is at most exportmax

    #print("Measurement: %i" % (x))
    #print("Solar: %i W" % (inverterM.data[x].get("Solar")))
    print("Solar: %i W" % (solar))
    #print("Total Consumption: %i W" % (consumptionTotal))
    print("Total Consumption: %i W" % (consumption))
    #print("Dimmer: %i%% (%i W)" % ((dimmer.value * 100), (dimmer.value * dimmer.maxWattage)))
    print("Export: %i" % (export))

    inverterM.previousExport = export
    controller.temperature = controller.updateTemperature(controller.ip)

    #algorithm 2 - binary increase/decrease # UNCOMMENT TEMPERATURE REQ?
    if(inverterM.previousExport >= inverterM.exportmax): #and (controller.temperature < controller.maxtemp): #export is at max/slightly over max, temp is under max
        a = 255 - dimmer.value
        dimmer.updateValue(dimmer.value + int(a/2))
        controller.updateDimmer(controller.ip, dimmer.value)
    else: #export is under max
        dimmer.updateValue(max(0, dimmer.value + (inverterM.previousExport - (inverterM.exportmax - inverterM.reserve)) / int(dimmer.maxWattage / 255)))
        controller.updateDimmer(controller.ip, dimmer.value)
        #a = max(0.1, 1 - dimmer.value)
        #dimmer.updateValue(dimmer.value - a/2)
        #dimmer.updateValue(max(0, dimmer.value))
        #controller.updateDimmer(controller.ip, dimmer.value)
        #dimmer.updateWattage()
    print("Changing dimmer value to %i:" % (dimmer.value))
    print("-----------")
    #inverterM.previousExport = min(inverterM.exportmax, (inverterM.data[x].get("Solar") - inverterM.data[x].get("Consumption")))
"""
    Algorithm 1 - always look at previous values and adjust the dimmer to achieve 99% export
    if (inverterM.previousExport == -1): # if first iteration
        dimmer.updateValue(1)
        inverterM.previousExport = min(inverterM.exportmax, (inverterM.data[x].get("Solar") - inverterM.data[x].get("Consumption")))
    else:
        #adjust according to the previously known Solar/Consumption values
        dimmerWattage = (inverterM.data[x - 1].get("Solar") - inverterM.data[x - 1].get("Consumption") - inverterM.exportmax) * 0.99
        dimmer.updateValue(max(0, dimmerWattage / dimmer.maxWattage))
"""


argparser = argparse.ArgumentParser()
argparser.add_argument("host", type=str, help="Modbus TCP address")
argparser.add_argument("port", type=int, help="Modbus TCP port")
argparser.add_argument("--timeout", type=int, default=1, help="Connection timeout")
argparser.add_argument("--unit", type=int, default=1, help="Modbus device address")
argparser.add_argument("--json", action="store_true", default=False, help="Output as JSON")
argparser.add_argument("--div", action="store_true", default=False, help="Output for diverter")
args = argparser.parse_args()

inverter = solaredge_modbus.Inverter(
    host=args.host,
    port=args.port,
    timeout=args.timeout,
    unit=args.unit
)
maxexport = -999999
maxexporttime = datetime.now()
export_limit = 2700

while(True):
    values = {}
    values = inverter.read_all() #call inverterSimulated instead of this!
    meters = inverter.meters()
    batteries = inverter.batteries()
    values["meters"] = {}
    values["batteries"] = {}

    for meter, params in meters.items():
        meter_values = params.read_all()
        values["meters"][meter] = meter_values

    for battery, params in batteries.items():
        battery_values = params.read_all()
        values["batteries"][battery] = battery_values

    if args.json:
        print(json.dumps(values, indent=4))
        break
    elif args.div:
       now = datetime.now()
       dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
       print("-------------- ", dt_string)

       solar = (values['power_ac'] * (10 ** values['power_ac_scale'])) #power_ac, power_ac_scale -> values
       #print(f"\tSolar power: {solar}W")
       for k, v in meter_values.items():
         if k == 'power':
           calculateDimValue(solar, -v, solar + v)
           #print("\tConsumption: %sW" % (-v))
           #if (solar + v) >= export_limit:
           #    print("\tExport: %s - %s over limit at %s" % (solar + v, solar + v - export_limit, dt_string))
           #    print(json.dumps(values, indent=4))
           #else:
           #    print("\tExport: %s" % (solar + v))
           #if (solar + v) > maxexport:
           #    maxexport = (solar + v)
           #    maxexporttime = now
           #print("\tMax export: %s at %s" % (maxexport, maxexporttime))
           break
    sys.stdout.flush()
    sys.stderr.flush()

    time.sleep(10)

