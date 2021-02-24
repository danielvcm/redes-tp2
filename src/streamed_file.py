import math

from . import comum
from .sliding_window import SlidingWindow

class StreamedFile:
    def __init__(self, client_addr, file_name, file_size) -> None:
        self.client_addr = client_addr
        self.file_name = file_name
        self.max_payloads = math.ceil(file_size/comum.MAX_FILE_PART_SIZE)
        self.sliding_window = SlidingWindow(int(file_size))
        self.payloads = {}
    
    def set_payload(self, client_addr, serial_number, payload): #mudar esses args p mensagem depois
        if client_addr == self.client_addr and serial_number < self.max_payloads:
            self.payloads[serial_number] = payload

    def export_file(self):
        if not self.finished_streaming():
            return False
        try:
            ordered_payloads = self.get_ordered_payloads()
            with open('./nuvem/'+self.file_name, 'wb') as new_file:
                for payload in ordered_payloads:
                    new_file.write(payload)
            return True
        except Exception as ex:
            print(ex)
            return False
    
    def get_ordered_payloads(self):
        serial_numbers = [key for key in self.payloads]
        serial_numbers.sort()
        ordered_payloads = [self.payload[serial_number] for serial_number in serial_numbers]
        return ordered_payloads
    
    def finished_streaming(self):
        if len(self.payloads) == self.max_payloads:
            return True
        return False
        