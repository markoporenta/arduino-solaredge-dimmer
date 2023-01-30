import re

import requests


class Controller:
    def __init__(self, ip, maxtemp):
        self.ip = ip
        #self.temperature = self.updateTemperature(ip)
        self.maxtemp = maxtemp

    def updateDimmer(self, ip, newValue):
        try:
            updateDimmer = requests.get('http://%s/slider?value=%i' % (ip, newValue), timeout=10)
            #print(updateDimmer.text)
        except requests.exceptions.Timeout as e:
            print(e)

    def updateTemperature(self, ip):
        try:
            res = requests.get('http://' + ip, timeout=10)

            #print(res.text)

            temperature = float(re.search("Temperature:-?[0-9]+\.?[0-9]*", res.text).group().split(':')[1])
            maxtemp = float(re.search("Max temperature:[0-9]+", res.text).group().split(':')[1])
            if temperature > maxtemp:
                print("Warning: current temperature of %f exceeds max Temperature of %i" % ((temperature), (maxtemp)))
            return (temperature)
        except requests.exceptions.Timeout as e:
            print(e)

    def updatemaxtemp(self, ip, maxtemp):
        try:
            updateTemp = requests.get("http://" + ip + "/maxtemp=%i" % (max), timeout=10)
            #print(updateTemp.text)
            return(maxtemp)
        except requests.exceptions.Timeout as e:
            print(e)
