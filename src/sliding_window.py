from . import comum

class SlidingWindow:
    class Cell:
        def __init__(self, serial_number, transmitted = False, acked = False) -> None:
            self.serial_number = serial_number
            self.transmitted = transmitted
            self.acked = acked
    
    def __init__(self, file_size):
        self.array = self.generate_array(file_size)
        self.window_size = comum.WINDOW_SIZE
        self.transmit_edge = None

    def generate_array(self, file_size):
        array = {}
        serial_number = 0
        for i in range(0,file_size,comum.MAX_FILE_PART_SIZE):
            array[serial_number] = SlidingWindow.Cell(serial_number)
            serial_number+=1
        return array

    def can_send(self, serial_number):
        if self.transmit_edge == None:
            if serial_number < self.window_size:
                return True
        if serial_number > self.transmit_edge and serial_number < self.transmit_edge + self.window_size :
            return True
        return False
    
    def acked(self, serial_number):
        if serial_number == 0:
            self.transmit_edge = serial_number
            self.array[serial_number].acked = True
        else:
            self.array[serial_number].acked = True
            self.refresh_ack_window()

    def refresh_ack_window(self):
        if self.transmit_edge == None:
            return
        acked_edge = self.transmit_edge
        for i in range(self.transmit_edge, self.window_size):
            if self.array[i].acked == True:
                acked_edge = i
            else:
                break
        self.transmit_edge = acked_edge