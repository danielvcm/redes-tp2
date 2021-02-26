import math
import threading
from . import comum
from .sliding_window import SlidingWindow

class StreamedFile:
    def __init__(self, file_name, file_size) -> None:
        self.file_name = file_name
        self.max_payloads = math.ceil(file_size/comum.MAX_FILE_PART_SIZE)
        self.sliding_window = SlidingWindow(int(file_size))
        self.payloads = {}
        self.lock = threading.Lock()
    
    def set_payload(self,  serial_number, payload):
        self.lock.acquire()
        if serial_number < self.max_payloads:
            self.payloads[serial_number] = payload
        self.lock.release()

    def export_file(self):
        if not self.finished_streaming():
            return False
        try:
            self.lock.acquire()
            ordered_payloads = self.get_ordered_payloads()
            with open('./nuvem/'+self.file_name, 'wb') as new_file:
                for payload in ordered_payloads:
                    new_file.write(payload)
            self.lock.release()
            return True
        except Exception as ex:
            self.lock.release()
            print(ex)
            return False
    
    def get_ordered_payloads(self):
        serial_numbers = [key for key in self.payloads]
        serial_numbers.sort()
        ordered_payloads = [self.payloads[serial_number] for serial_number in serial_numbers]
        return ordered_payloads
    
    def finished_streaming(self):
        self.lock.acquire()
        if len(self.payloads) == self.max_payloads:
            self.lock.release()
            return True
        self.lock.release()
        return False
        