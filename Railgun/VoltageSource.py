#Voltage source class

import numpy as np;

class VoltageSource:
    
    def __init__(self, peakVoltage, type, capacitance_f = 1):
        self.peakVoltage = peakVoltage;
        self.type = type;
        self.capacitance_f = capacitance_f;
    
    def updateVoltage(self, time, resistance):
        if self.type == "constant":
            return self.peakVoltage;
        elif self.type == "capacitor":
            tau = resistance * self.capacitance_f;
            V = self.peakVoltage * np.exp(-time / tau);
            return V;
        else:
            return 0;