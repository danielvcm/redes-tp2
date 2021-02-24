from . import comum
import threading
class SlidingWindow:
    class Cell:
        def __init__(self, serial_number, transmitted = False, acked = True) -> None:
            self.serial_number = serial_number
            self.transmitted = transmitted
            self.acked = acked
            self.lock = threading.Lock()
        
        def set_transmitted(self, value: bool):
            self.lock.acquire()
            self.transmitted = value
            self.lock.release()
        
        def get_transmitted(self):
            self.lock.acquire()
            value = self.transmitted 
            self.lock.release()
            return value
        
        def set_acked(self, value: bool):
            self.lock.acquire()
            self.acked = value
            self.lock.release()

        def get_acked(self):
            self.lock.acquire()
            value = self.acked 
            self.lock.release()
            return value
    
    def __init__(self, file_size):
        self.array = self.generate_array(file_size)
        self.window_size = comum.WINDOW_SIZE
        self.transmit_edge = None
        self.lock = threading.Lock()
    
    def set_transmitted(self,serial_number, transmitted):
        self.array[serial_number].set_transmitted(transmitted)
    
    def get_transmitted(self,serial_number):
        return self.array[serial_number].get_transmitted()
    
    def get_acked(self, serial_number):
        return self.array[serial_number].get_acked()
    
    def get_window_end(self):
        self.lock.acquire()
        value = self.transmit_edge + comum.WINDOW_SIZE
        self.lock.release()
        return value
    
    def generate_array(self, file_size):
        array = {}
        serial_number = 0
        for i in range(0,file_size,comum.MAX_FILE_PART_SIZE):
            array[serial_number] = SlidingWindow.Cell(serial_number)
            serial_number+=1
        return array

    def can_send(self, serial_number):
        self.lock.acquire()
        if self.transmit_edge == None:
            if serial_number < self.window_size:
                self.lock.release()
                return True
        if serial_number > self.transmit_edge and serial_number < self.transmit_edge + self.window_size :
            self.lock.release()
            return True
        
        self.lock.release()
        return False
    
    def acked(self, serial_number):
        if serial_number == 0:
            self.transmit_edge = serial_number
            self.array[serial_number].set_acked(True)
        else:
            self.array[serial_number].set_acked(True)
            self.refresh_ack_window()

    def refresh_ack_window(self):
        self.lock.acquire()
        if self.transmit_edge == None:
            self.lock.release()
            return
        acked_edge = self.transmit_edge
        for i in range(self.transmit_edge, self.window_size):
            if self.array[i].get_acked() == True:
                acked_edge = i
            else:
                break
        self.transmit_edge = acked_edge
        self.lock.release()