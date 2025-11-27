import serial
import time
from threading import Event
import math
import yaml


class CNC_Machine():
    #All of this data could also be stored in a yaml file
    BAUD_RATE = 115200
    SERIAL_PORT = "COM6" #Serial Port you are using
    X_LOW_BOUND = 0
    X_HIGH_BOUND = 270 #Note this bound wasn't working upstairs, but it is usually the boundary for the small CNC machine
    Y_LOW_BOUND = 0
    Y_HIGH_BOUND = 150
    Z_LOW_BOUND = -35
    Z_HIGH_BOUND = 0

    #Tracks the locations
    LOCATIONS = None
    LOCATION_FILE = 'location_status.yaml'

    VIRTUAL=True #Is this a simulation?

    def __init__(self,virtual=False):
        self.LOCATIONS = self.load_from_yaml(self.LOCATION_FILE)
        self.VIRTUAL = virtual
        print("Connected to CNC Machine!")

    def load_from_yaml(self,file_in):
        with open(file_in, "r") as file:
            data_in = yaml.safe_load(file)
        return data_in

    #Return to origin (currently doesn't use limit switches)
    def home(self):
        print("Returning CNC to origin")
        self.move_to_point_safe(x=0,y=0,z=0,gtype="G0")

    #Wait for the CNC machine to complete its motion
    def wait_for_movement_completion(self,ser, cleaned_line):
        Event().wait(1)
        if cleaned_line != '$X' or '$$':
            idle_count = 0
            while True:
                ser.reset_input_buffer()
                command = str.encode('?' + '\n')
                ser.write(command)
                grbl_out = ser.readline()
                grbl_response = grbl_out.strip().decode('utf-8')

                if grbl_response != 'ok':
                    if grbl_response.find('Idle') > 0:
                        idle_count += 1
                if idle_count > 0:
                    break
        return

    #Move through a list of points
    def move_through_points(self,point_list,speed=3000):
        print("Moving through list of points!", point_list)
        gcode=""
        for point in point_list:
            x,y,z = point
            if self.coordinates_within_bounds(x,y,z):
                gcode += self.get_gcode_path_to_point(x,y,z,speed,"G1")
        self.follow_gcode_path(gcode)

    #Command the CNC machine to move to a point (x,y,z) with specific speed. Gtype could be G0 or G1, G0 moves at maximum possible speed
    def move_to_point(self,x=None,y=None,z=None,speed=3000,gtype="G1"):
        if self.coordinates_within_bounds(x,y,z):
            gcode = self.get_gcode_path_to_point(x,y,z,speed,gtype)
            print(f"Moved To (X{x}, Y{y}, Z{z}): ", self.follow_gcode_path(gcode))
        else:
            print(f"Cannot move to (X{x}, Y{y}, Z{z}), coordinates not within bounds")

    #Command the CNC machine to move to its max height then to an xy location then down to the target z
    def move_to_point_safe(self,x,y,z,speed=3000,gtype="G1"):
        if self.coordinates_within_bounds(x,y,z):
            #gcode = self.get_gcode_path_to_point(x=None,y=self.Y_HIGH_BOUND,z=self.Z_HIGH_BOUND,speed=speed,gtype=gtype) #Max height
            #gcode += self.get_gcode_path_to_point(x=x,y=self.Y_HIGH_BOUND,z=self.Z_HIGH_BOUND,speed=speed,gtype=gtype) #xy travel
            #gcode += self.get_gcode_path_to_point(x=None,y=y,z=z,speed=speed,gtype=gtype) #Down
            gcode = self.get_gcode_path_to_point(x=None,y=None,z=self.Z_HIGH_BOUND,speed=speed,gtype=gtype) #Max height
            gcode += self.get_gcode_path_to_point(x=x,y=y,z=self.Z_HIGH_BOUND,speed=speed,gtype=gtype) #xy travel
            gcode += self.get_gcode_path_to_point(x=None,y=None,z=z,speed=speed,gtype=gtype) #Down
            print(f"Moved safely To (X{x}, Y{y}, Z{z}): ", self.follow_gcode_path(gcode))
        else:
            print(f"Cannot move to (X{x}, Y{y}, Z{z}), coordinates not within bounds")

    #Move to a location defined in the Locations file
    def move_to_location(self,location_name,location_index,safe=True,speed=3000):
        print(f"Moving to location: {location_name} at index {location_index}")
        x,y,z = self.get_location_position(location_name,location_index)
        if safe:
            self.move_to_point_safe(x,y,z,speed=speed)
        else:
            self.move_to_point(x,y,z,speed=speed)

    #Get the location in x,y,z from name and index
    def get_location_position(self,location_name,location_index):
        x = self.LOCATIONS[location_name]['x_origin']
        y = self.LOCATIONS[location_name]['y_origin']
        z = self.LOCATIONS[location_name]['z_origin']

        if location_index > 0:
            try:
                num_x = self.LOCATIONS[location_name]['num_x']
                num_y = self.LOCATIONS[location_name]['num_y']
                x_offset = self.LOCATIONS[location_name]['x_offset']
                y_offset = self.LOCATIONS[location_name]['y_offset']
                x = x + location_index%num_x*x_offset
                y = y + math.floor(location_index/num_x)*y_offset
            except:
                print("Error extracting location from locations")
                return None
        
        return x,y,z

    #Returns the gcode to move to a point (x,y,z)
    #You can create a long gcode list to execute all at once instead of doing it line-by-line
    def get_gcode_path_to_point(self,x=None,y=None,z=None,speed=500,gtype="G1"):
        return_string = gtype
        if x != None:
            return_string += f" X{x}"
        if y != None:
            return_string += f" Y{y}"
        if z != None:
            return_string += f" Z{z}"
        if speed != None:
            return_string += f" F{speed}"
        return return_string + " \n"

    #Check if you are within the stage
    def coordinates_within_bounds(self,x,y,z):
        within_x_bounds = within_y_bounds = within_z_bounds = False
        if x is None: 
            within_x_bounds = True
        elif self.X_LOW_BOUND <= x <= self.X_HIGH_BOUND:
            within_x_bounds = True
        if y is None: 
            within_y_bounds = True
        elif self.Y_LOW_BOUND <= y <= self.Y_HIGH_BOUND:
            within_y_bounds = True
        if z is None: 
            within_z_bounds = True
        elif self.Z_LOW_BOUND <= z <= self.Z_HIGH_BOUND:
            within_z_bounds = True
        return within_x_bounds and within_y_bounds and within_z_bounds

    #Wake up the CNC machine
    def wake_up(self,ser):
        ser.write(str.encode("\r\n\r\n"))
        time.sleep(1)  # Wait for cnc to initialize
        ser.flushInput()  # Flush startup text in serial input

    #Follows a gcode path, will execute as many commands at a time as the buffer is set to
    #If the buffer is too high, the machine may not complete all the commands
    def follow_gcode_path(self,gcode, buffer=20):
        if not self.VIRTUAL: 
            with serial.Serial(self.SERIAL_PORT, self.BAUD_RATE) as ser:
                self.wake_up(ser)
                out_strings = []
                commands = gcode.split('\n')
                for i in range (0, math.ceil(len(commands)/buffer)):
                    try:
                        buffered_commands = commands[i*buffer:(i+1)*buffer]
                    except:
                        buffered_commands = commands[i*buffer:]
                    buffered_gcode = ""
                    for j in range (0, len(buffered_commands)):
                        buffered_gcode += buffered_commands[j] 
                        buffered_gcode += "\n"

                    command = str.encode(buffered_gcode)
                    ser.write(command)
                    self.wait_for_movement_completion(ser, buffered_gcode)
                    grbl_out = ser.readline()  # Wait for response
                    out_string =grbl_out.strip().decode('utf-8')
                    out_strings.append(out_string)
                    print("Movement commands rendered:", len(buffered_commands)+i*buffer)
                return out_strings