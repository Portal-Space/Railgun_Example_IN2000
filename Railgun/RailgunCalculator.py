#Class with functionality to plot railgun graphs

import numpy as np;
import matplotlib.pyplot as plt;

from Railgun import Railgun;
from Armature import Armature;
from VoltageSource import VoltageSource;

mu0 = 4 * np.pi * 1e-7  # Permeability of free space

class RailgunSimulator:
    
    def __init__(self, railgun, armature, voltageSource, type):
        self.railgun = railgun;
        self.armature = armature;
        self.voltageSource = voltageSource;
        self.type = type; #Should be "rail", "flight" or "full"
        self.armature.angle_r = self.railgun.angle_r;
        
        self.currentArmatureTravel_x = 0;
        self.currentArmatureTravel_y = 0;
        self.currentArmatureSpeed_x = 0;
        self.currentArmatureSpeed_y = 0;
        self.currentCurrent = 0;
        self.currentMagneticFieldAtArmature = 0;
        self.currentForceOnArmature = 0;
        self.currentRadialForce = 0;
        self.currentTime = 0;
        
        self.result = {};
        self.result["armatureTravel"] = [[], []];
        self.result["armatureSpeed"] = [[], []];
        self.result["current"] = [];
        self.result["voltage"] = [];
        self.result["magneticField"] = [];
        self.result["forceArmature"] = [];
        self.result["forceRadial"] = [];
        self.result["time"] = [];
        self.result["timeRails"] = [];
        
        self.simulationFinished = False;
        self.endOfRails = False;
        self.endOfRailsLatch = True;
    
    def clearCalculation(self):
        self.currentArmatureTravel_x = 0;
        self.currentArmatureTravel_y = 0;
        self.currentArmatureSpeed_x = 0;
        self.currentArmatureSpeed_y = 0;
        self.currentCurrent = 0;
        self.currentMagneticFieldAtArmature = 0;
        self.currentForceOnArmature = 0;
        self.currentRadialForce = 0;
        self.currentTime = 0;
        
        self.result = {};
        self.result["armatureTravel"] = [[], []];
        self.result["armatureSpeed"] = [[], []];
        self.result["current"] = [];
        self.result["voltage"] = [];
        self.result["magneticField"] = [];
        self.result["forceArmature"] = [];
        self.result["forceRadial"] = [];
        self.result["time"] = [];
        self.result["timeRails"] = [];
    
    def calculateAirDensity(self, altitude):
        # Constants for the troposphere
        sea_level_density = 1.225  # kg/m^3 at sea level
        sea_level_temperature = 288.15  # Kelvin at sea level
        temperature_lapse_rate = 0.0065  # Temperature lapse rate in K/m
        gas_constant = 8.31447  # J/(mol*K)
        molar_mass_of_air = 0.0289644  # kg/mol

        # Gravity acceleration
        g0 = 9.80665  # m/s^2

        if altitude <= 11000:  # Troposphere
            # Temperature at altitude
            temperature = sea_level_temperature - temperature_lapse_rate * altitude
            # Pressure at altitude using the barometric formula
            pressure = (sea_level_density * gas_constant * sea_level_temperature / molar_mass_of_air) * \
                       (1 - temperature_lapse_rate * altitude / sea_level_temperature) ** \
                       (g0 * molar_mass_of_air / (gas_constant * temperature_lapse_rate))
            # Air density at altitude
            air_density = pressure * molar_mass_of_air / (gas_constant * temperature)
        else:
            # Above 11km other formulas and temperature profiles are required.
            air_density = 0  # Placeholder for higher altitudes.
        
        return air_density
    
    def calculateGravitationalForce(self, mass, altitude):
        #No gravity when within rail bounds
        if (np.sqrt(self.currentArmatureTravel_x**2 + self.currentArmatureTravel_y**2) <= self.railgun.railLength_m):
            return 0;
        G = 6.67430e-11  # Gravitational constant in N(m^2)/(kg^2)
        mass_earth = 5.972e24  # Mass of the Earth in kg
        radius_earth = 6.371e6  # Radius of the Earth in meters

        # Distance from the center of the Earth
        r = radius_earth + altitude

        # Gravitational force
        force = G * (mass_earth * mass) / r**2

        return force
    
    def calculateCurrent(self, timeStep):
        #Calculate the resistance of the rail plus armature
        resistance = np.sqrt(self.currentArmatureTravel_x**2 + self.currentArmatureTravel_y**2) * self.railgun.railResistancePerMeter_ohm + self.armature.resistance_ohm;
        #Retrieve the voltage
        V = self.voltageSource.updateVoltage(self.currentTime, resistance);
        #Calculate the current with ohms law
        self.currentCurrent = V / resistance;
        self.result["voltage"].append(V);
    
    def calculateLorentzForce(self):
        #Calculate the magnetic field
        self.currentMagneticFieldAtArmature = (mu0 * self.currentCurrent) / (2 * np.pi * self.railgun.railSeparation_m);
        #Calculate the force on the armature
        self.currentForceOnArmature = self.currentCurrent * self.armature.contactLength_m * self.currentMagneticFieldAtArmature;
    
    def calculateForceOnRails(self):
        area = self.railgun.railSeparation_m * self.armature.contactLength_m;
        self.currentRadialForce = (self.currentMagneticFieldAtArmature ** 2 * area) / (2 * mu0);
    
    def calculateArmatureSpeed(self, timeStep):
        drag = self.calculateArmatureDrag();
        # Calculate acceleration and add it to speed
            # X direction only has drag (And force on armature from the rails if it is on the rails)
        self.currentArmatureSpeed_x += np.cos(self.armature.angle_r)* ((self.currentForceOnArmature - drag) / self.armature.mass_kg) * timeStep;
            # Y direction has drag and gravity (And force on armature from the rails if it is on the rails)
        self.currentArmatureSpeed_y += (np.sin(self.armature.angle_r)* ((self.currentForceOnArmature - drag) / self.armature.mass_kg)) * timeStep - (self.calculateGravitationalForce(self.armature.mass_kg, self.currentArmatureTravel_y)/self.armature.mass_kg) * timeStep;
        # Add speed to position
        self.currentArmatureTravel_x += self.currentArmatureSpeed_x*timeStep;
        self.currentArmatureTravel_y += self.currentArmatureSpeed_y*timeStep;
    
    def calculateArmatureAngle(self):
        #Finds the direction of the projectile based on the speed vector (I assume that the aerodynamic projectile will always point towards the direction of travel)
        self.armature.angle_r = np.arctan2(self.currentArmatureSpeed_y, self.currentArmatureSpeed_x);
    
    def calculateArmatureDrag(self):
        #air_density = 1.225  # kg/m^3 at sea level
        air_density = self.calculateAirDensity(self.currentArmatureTravel_y);
        return (0.5 * air_density * np.sqrt(self.currentArmatureSpeed_x**2 + self.currentArmatureSpeed_y**2) * self.armature.drag_coefficient * ((self.armature.bore_m/2)**2 *np.pi))

    def doStep(self, timeStep):
        #The if else is just to decide on the type of simulation
        if (np.sqrt(self.currentArmatureTravel_x**2 + self.currentArmatureTravel_y**2) <= self.railgun.railLength_m): #Connected to the rails
            self.calculateCurrent(timeStep);
            self.result["current"].append(self.currentCurrent);
            #print(f"Current current: {self.currentCurrent}");
            
            self.calculateLorentzForce();
            self.result["magneticField"].append(self.currentMagneticFieldAtArmature);
            self.result["forceArmature"].append(self.currentForceOnArmature);
            #print(f"Current force on armature: {self.currentForceOnArmature}");
            
            self.calculateForceOnRails();
            self.result["forceRadial"].append(self.currentRadialForce);
            self.result["timeRails"].append(self.currentTime*1000);
            #print(f"Current force on rails: {self.currentRadialForce}");
        else:
            if (not self.endOfRails and self.endOfRailsLatch):
                self.endOfRails = True;
                self.endOfRailsLatch = False;
                print(f"\rLeft rails at {self.currentTime:10.5f} s with vertical speed: {self.currentArmatureSpeed_y:10.2f} m/s and horizontal speed: {self.currentArmatureSpeed_x:10.2f} m/s.\nMuzzle Velocity: {round(np.sqrt(self.currentArmatureSpeed_x**2 + self.currentArmatureSpeed_y**2), 2)} m/s");
                
            if (self.type == "rail"):
                self.simulationFinished = True;
            self.currentForceOnArmature = 0;
            self.currentCurrent = 0;
            self.currentMagneticFieldAtArmature = 0;
            self.currentRadialForce = 0;

        # This is the differential equation
        self.calculateArmatureSpeed(timeStep);
        self.calculateArmatureAngle();

        # This is for saving each step
        self.result["armatureTravel"][0].append(self.currentArmatureTravel_x);
        self.result["armatureTravel"][1].append(self.currentArmatureTravel_y);
        self.result["armatureSpeed"][0].append(self.currentArmatureSpeed_x);
        self.result["armatureSpeed"][1].append(self.currentArmatureSpeed_y);
        self.result["time"].append(self.currentTime);

        # We must remember to iterate our time
        self.currentTime += timeStep;
        
        if (self.type == "flight" and self.currentArmatureTravel_y < 0):
            self.simulationFinished = True;
    
    def doCalculation(self, timestepsPerMs, max_s):
        timestep = 0.001/timestepsPerMs;
        s_simulated = 0;
        
        while s_simulated < max_s:
            # All the simulation in done in the dostep function
            self.doStep(timestep);

            #Just for printing
            print(f"\rSimulated {self.currentTime:10.2f} s | Speed Vertical: {self.currentArmatureSpeed_y:10.2f} m/s | Speed Horizontal: {self.currentArmatureSpeed_x:10.2f} m/s", end="");
            if (self.simulationFinished):
                break;
            s_simulated += timestep;
    
    def plotGraphs(self):
        np_time = np.array(self.result["time"]);
        np_timeRails = np.array(self.result["timeRails"]);
        np_armatureSpeed_x = np.array(self.result["armatureSpeed"][0]);
        np_armatureSpeed_y = np.array(self.result["armatureSpeed"][1]);
        np_forceArmature = np.array(self.result["forceArmature"]);
        np_current = np.array(self.result["current"]);
        np_voltage = np.array(self.result["voltage"]);
        
        np_armaturePos_x = np.array(self.result["armatureTravel"][0]);
        np_armaturePos_y = np.array(self.result["armatureTravel"][1]);
        
        fig, ax = plt.subplots(5, 1, layout='constrained');
        ax[0].plot(np_timeRails, np_voltage);
        ax[0].set_xlabel('Time (ms)');
        ax[0].set_ylabel('Voltage (V)');
        ax[1].plot(np_timeRails, np_current);
        ax[1].set_xlabel('Time (ms)');
        ax[1].set_ylabel('Current (A)');
        ax[2].plot(np_timeRails, np_forceArmature);
        ax[2].set_xlabel('Time (ms)');
        ax[2].set_ylabel('Force on Armature (N)');
        ax[3].plot(np_time, np_armatureSpeed_x);
        ax[3].set_xlabel('Time (s)');
        ax[3].set_ylabel('Armature Speed x (m/s)');
        ax[4].plot(np_time, np_armatureSpeed_y);
        ax[4].set_xlabel('Time (s)');
        ax[4].set_ylabel('Armature Speed y (m/s)');
        plt.show();
        
        fig, ax = plt.subplots(1, 1, layout='constrained');
        ax.plot(np_armaturePos_x, np_armaturePos_y);
        ax.set_xlabel("Travel (m)");
        ax.set_ylabel("Altitude (m)");
        ax.set_aspect('equal', adjustable='box');
        plt.show();


# Sample usage
if __name__ == "__main__":
    #Rail length, resistance per meter of rail, bore in m, angle radians, permanent magnets in tesla
    railgun = Railgun(9.61, 0.001, 0.155, np.pi/16, 1.32);
    #bore in m, contact point length m, total resistance, mass kg, coefficient of drag 
    armature = Armature(0.155, 0.1, 0.05, 20, 0.15);
    #peak voltage V, type, capacitance f
    voltageSource = VoltageSource(6.67e4, "capacitor", (6*100)*0.0116);
    calculator = RailgunSimulator(railgun, armature, voltageSource, "flight");
    #points per ms, max time in sec
    calculator.doCalculation(10, 500); #points per ms, max simulation time
    calculator.plotGraphs();
    