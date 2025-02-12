#Armature class

class Armature:
    
    def __init__(self, bore_m, contact_length, resistance_ohm, mass_kg, drag_coefficient):
        self.bore_m = bore_m;
        self.resistance_ohm = resistance_ohm;
        self.drag_coefficient = drag_coefficient;
        self.contactLength_m = contact_length
        self.mass_kg = mass_kg;
        self.angle_r  = 0;