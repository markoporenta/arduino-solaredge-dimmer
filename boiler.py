import re
import requests

# TO-DO: objects (Dimmer/Controller/Inverter)

#set dimmer starting parameters
temperature = 0
dimmer = 0 # should be between 0 and 1 (0 ~ 0%, 0.5 ~ 50%, 1 ~ 100%)
maxtemp = 0

previousExport = -1

ip = "192.168.58.95"

#assuming exportmax = 2700W, boiler capacity = 2000W
exportmax = 2700
dimmerCapacity = 2000

data = [{'Solar': 4000, 'Consumption': 1000},
        {'Solar': 2000, 'Consumption': 1000},
        {'Solar': 4000, 'Consumption': 1000},
        {'Solar': 2000, 'Consumption': 1000},
        {'Solar': 4000, 'Consumption': 1000},
        {'Solar': 2000, 'Consumption': 1000},
        {'Solar': 4000, 'Consumption': 1000},
        {'Solar': 2000, 'Consumption': 1000},
        {'Solar': 4000, 'Consumption': 1000},
        {'Solar': 2000, 'Consumption': 1000},
        {'Solar': 4000, 'Consumption': 1000},
        {'Solar': 2000, 'Consumption': 1000},
        {'Solar': 4000, 'Consumption': 1000},
        {'Solar': 2000, 'Consumption': 1000},
        {'Solar': 4000, 'Consumption': 1000},
        {'Solar': 2000, 'Consumption': 1000},
        {'Solar': 4000, 'Consumption': 1000},
        {'Solar': 2000, 'Consumption': 1000},
        {'Solar': 4000, 'Consumption': 1000},
        {'Solar': 2000, 'Consumption': 1000}
        ]

def getValues(ip):
    try:
        res = requests.get('http://' + ip, timeout=10)

        #print(res.text)

        temperature = float(re.search("Temperature:-?[0-9]+\.?[0-9]*", res.text).group().split(':')[1])
        dimmer = float(re.search("Dimmer:[0-9]+", res.text).group().split(':')[1])
        maxtemp = float(re.search("Max temperature:[0-9]+", res.text).group().split(':')[1])
        try:
            return temperature, dimmer, maxtemp
        except (not temperature): #v primeru, da nismo dobili nobene vrednosti(npr. "Temperature:")
            print("No temperature value read")
    except requests.exceptions.Timeout as e:
        print(e)

#getValues("192.168.58.95")

def updatedimmer(ip, dimValue):
    try:
        updateDimmer = requests.get("http://" + ip + "/dimmer=%i" % (dimValue), timeout=10)
        print(updateDimmer.text)
    except requests.exceptions.Timeout as e:
        print(e)

def updatemaxtemp(ip, max):
    try:
        updateTemp = requests.get("http://" + ip + "/maxtemp=%i" % (max), timeout=10)
        print(updateTemp.text)
    except requests.exceptions.Timeout as e:
        print(e)

for x, dict in enumerate(data):
    #temperature, dimmer, maxtemp = getValues(ip)
    consumptionTotal = (data[x].get("Consumption")) + (dimmer * dimmerCapacity)
    export = max(0, data[x].get("Solar") - consumptionTotal) #export cannot be less than 0
    export = min(exportmax, export) # export is at most exportmax

    print("Measurement: %i" % (x))
    print("Solar: %i W" % (data[x].get("Solar")))
    print("Total Consumption: %i W" % (consumptionTotal))
    print("Dimmer: %i%% (%i W)" % ((dimmer * 100), (dimmer * dimmerCapacity)))
    print("Export: %i" % (export))
    print("-----------")

    if (previousExport == -1): # if first iteration
            dimmer = 1
            previousExport = min(exportmax, (data[x].get("Solar") - data[x].get("Consumption")))
    else:
        #adjust according to the previously known Solar/Consumption values
        dimmerWattage = (data[x-1].get("Solar") - data[x-1].get("Consumption") - exportmax) * 0.99
        dimmer = max(0, dimmerWattage / dimmerCapacity)


# to-do:
#primerjava razlicnih algoritmov: vedno gledamo previous value/ binary search / glede na to, ali je sprememba in Consumption/Solar production



updatemaxtemp("192.168.58.95", 60)
#updateDimmer = requests.get("http://192.168.58.95/dimmer=%i"%(dimmer) , timeout=10)
