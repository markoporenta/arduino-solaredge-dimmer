class Dimmer:
    def __init__(self, maxWattage):
        self.maxWattage = maxWattage
        self.value = 0 # should be between 0 and 255
        self.wattage = self.value * int(self.maxWattage / 255)

    def updateValue(self, value):
        self.value = value
        self.wattage = self.value * int(self.maxWattage / 255)