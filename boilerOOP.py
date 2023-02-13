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

controller = Controller("192.168.58.95", 60) #ip, max temperature
dimmer = Dimmer(2000) #dimmer capacity in watts
inverterM = Inverter(3500, 400) # export limit in watts, reserve
#inverterM = Inverter(0, 0) # for test purposes



#connect to database

#import pyodbc
# Some other example server values are
# server = 'localhost\sqlexpress' # for a named instance
# server = 'myserver,port' # to specify an alternate port
#server = 'tcp:localhost'
#database = 'University'
#username = 'sa'
#password = 'yourStrong(!)Password'
#TrustServerCertificate='yes'
#autocommit = "yes"
#cnxn = pyodbc.connect('DRIVER={ODBC Driver 18 for SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password+';TRUSTSERVERCERTIFICATE='+TrustServerCertificate+';AUTOCOMMIT='+autocommit)
#cursor = cnxn.cursor()

#cursor.execute("SELECT * FROM DEVICE")
#for x in cursor:
#    print(x)


# create table "Measurements" IF NOT ALREADY PRESENT
#mySql_Create_Table_Query = """CREATE TABLE MEASUREMENTS (
#                         MeasurementsId int IDENTITY(1,1) PRIMARY KEY,
#                         Solar int NOT NULL,
#                         Consumption int NOT NULL,
#                         Export int NOT NULL,
#                         DimmerValue int NOT NULL)
#                         """
#cursor.execute(mySql_Create_Table_Query)

#cursor.execute("DROP TABLE MEASUREMENTS")

#cursor.execute("SELECT * FROM MEASUREMENTS")
#for x in cursor:
#    print(x)

#test insert
#sql = "INSERT INTO MEASUREMENTS VALUES (1,1,1,1)"
#cursor.execute(sql)

def calculateDimValue(solar, consumption, export):

    print("Solar: %i W" % (solar))
    print("Total Consumption: %i W" % (consumption))
    print("Export: %i" % (export))

    #controller.temperature = controller.updateTemperature(controller.ip)

    #export is at max/over max:
    if(export >= inverterM.exportmax):
        a = 255 - dimmer.value
        dimmer.updateValue(dimmer.value + int(a/2))
        controller.updateDimmer(controller.ip, dimmer.value)
    else: #export is under max
        dimmer.updateValue(max(0, dimmer.value + (export - (inverterM.exportmax - inverterM.reserve)) / int(dimmer.maxWattage / 255)))
        controller.updateDimmer(controller.ip, dimmer.value)
    print("Changing dimmer value to %i:" % (dimmer.value))
    print("-----------")
    sql = "INSERT INTO MEASUREMENTS VALUES (%i, %i, %i, %i)" % (solar, consumption, export, dimmer.value)
#    cursor.execute(sql)
#    cnxn.commit()


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
    values = inverter.read_all()
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

