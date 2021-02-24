from . import comum

ENCODING = 'ascii'
BYTE_ORDER = 'big'

class Message:
    message_types = {'HELLO':b'1 ',
            'CONNECTION': b'2 ',
            'INFO FILE': b'3 ',
            'OK': b'4 ',
            'FIM': b'5 ',
            'FILE': b'6 ',
            'ACK': b'7 '}
    def __init__(self, type):
        self.type = type

    def encode(self):
        return Message.message_types[self.type]
    
    def decode(message):
        for key in Message.message_types:
            if message[0:2] == Message.message_types[key]:
                return Message(key)
        return Message(None)

class ConnectionMessage(Message):
    def __init__(self, udp_port):
        super().__init__("CONNECTION")
        self.udp_port = int(udp_port)
    
    def encode(self):
        try:
            udp_port_bytes = self.udp_port.to_bytes(4,BYTE_ORDER)
        except OverflowError:
            raise Exception('udp_port length is too big')
        message = Message.message_types[self.type]+udp_port_bytes
        return message
    
    def decode(message):
        udp_port = int.from_bytes(message[comum.SIMPLE_MESSAGE_SIZE:], BYTE_ORDER)
        return ConnectionMessage(udp_port)

class InfoFileMessage(Message):
    max_file_name_len = 15
    max_file_size_len = 8

    def __init__(self, file_name, file_size):
        super().__init__('INFO FILE')
        self.file_name = file_name
        self.file_size = int(file_size)


    def convert_file_size_to_bytes(self):
        try:
            file_size_bytes = self.file_size.to_bytes(self.max_file_size_len,BYTE_ORDER)
            return file_size_bytes
        except OverflowError:
            raise Exception('File is too big')
    
    def validate_file_name(self):
        if len(self.file_name) > self.max_file_name_len:
            raise UnicodeEncodeError('asc',self.file_name, 0, 1,'Nome do arquivo grande demais')
        if len(self.file_name)<5 or self.file_name[-4]!='.':
            raise UnicodeEncodeError('asc',self.file_name, 0, 1,'Nome do arquivo deve terminar com . + 3 caracteres')
    
    def encode(self):
        self.validate_file_name()
        file_size_bytes = self.convert_file_size_to_bytes()
        file_name = self.file_name.encode(ENCODING)
        file_name += b' '*(InfoFileMessage.max_file_name_len-len(file_name))
        message = Message.message_types[self.type] + file_name + file_size_bytes
        return message
    
    def decode(message):
        dot_idx = message.find(b'.')
        file_name = message[comum.SIMPLE_MESSAGE_SIZE:dot_idx+4].decode(ENCODING)
        file_size_idx = comum.SIMPLE_MESSAGE_SIZE + InfoFileMessage.max_file_name_len
        file_size = int.from_bytes(message[file_size_idx:], BYTE_ORDER)
        return InfoFileMessage(file_name, file_size)

class FileMessage(Message):
    max_serial_number_len = 4
    max_payload_size_len = 8

    def __init__(self, serial_number, payload_size, payload):
        super().__init__('FILE')
        self.serial_number = int(serial_number)
        self.payload_size = int(payload_size)
        self.payload = payload
    
    def encode(self):
        serial_number_bytes = self.convert_serial_number_to_bytes()
        payload_size_bytes = self.convert_payload_size_to_bytes()
        payload = self.get_right_size_payload()
        
        message = Message.message_types[self.type] + serial_number_bytes + payload_size_bytes + payload
        
        return message

    def decode(message: bytes):
        serial_number_start_idx = comum.SIMPLE_MESSAGE_SIZE
        payload_size_start_idx = FileMessage.max_serial_number_len+serial_number_start_idx
        payload_start_idx = payload_size_start_idx+FileMessage.max_payload_size_len
        serial_number = int.from_bytes(message[serial_number_start_idx:payload_size_start_idx],BYTE_ORDER)
        payload_size = int.from_bytes(message[payload_size_start_idx:payload_start_idx],BYTE_ORDER)
        payload = message[payload_start_idx:payload_size]
        return FileMessage(serial_number, payload_size, payload)

    def convert_serial_number_to_bytes(self):
        try:
            serial_number_bytes = self.serial_number.to_bytes(self.max_serial_number_len, BYTE_ORDER)
            return serial_number_bytes
        except OverflowError:
            raise Exception(f'Serial number {self.serial_number} is too long')
    
    def convert_payload_size_to_bytes(self):
        try:
            payload_size_bytes = self.payload_size.to_bytes(self.max_payload_size_len, BYTE_ORDER)
            return payload_size_bytes
        except OverflowError:
            raise Exception(f'Payload size {self.payload_size} is too long')
    
    def get_right_size_payload(self):
        payload = self.payload
        if len(self.payload)< comum.MAX_FILE_PART_SIZE:
            payload = self.payload + b' '*(comum.MAX_FILE_PART_SIZE-len(self.payload))
        return payload



