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
        message = Message.message_types['CONNECTION']+udp_port_bytes
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
        message = Message.message_types['INFO FILE'] + file_name + file_size_bytes
        return message
    
    def decode(message):
        dot_idx = message.find(b'.')
        file_name = message[comum.SIMPLE_MESSAGE_SIZE:dot_idx+4].decode(ENCODING)
        file_size_idx = comum.SIMPLE_MESSAGE_SIZE + InfoFileMessage.max_file_name_len
        file_size = int.from_bytes(message[file_size_idx:], BYTE_ORDER)
        return InfoFileMessage(file_name, file_size)

class FileMessage(Message):
    def __init__(self, serial_number, payload_size, payload):
        super().__init__('FILE')
        self.serial_number = str(serial_number)
        self.payload_size = str(payload_size)
        self.payload = payload
    
    def encode(self):
        if len(self.serial_number) > 4:
            raise Exception('Serial')
