#Class that represents the railgun

class Railgun:
    
    def __init__(self, rail_length_m, railResistancePerMeter_ohm, bore_m, angle, permanent_magnetic_field_t = 0):
        self.railLength_m = rail_length_m;
        self.railResistancePerMeter_ohm = railResistancePerMeter_ohm;
        self.bore_m = bore_m;
        self.railSeparation_m = self.bore_m/2;
        self.angle_r = angle;
        self.permanent_magnetic_field_t = permanent_magnetic_field_t;