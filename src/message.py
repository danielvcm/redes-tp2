from . import comum

ENCODING = 'ascii'

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
        self.udp_port = str(udp_port)
    
    def encode(self):
        if len(self.udp_port) > 4:
            raise Exception('udp_port must be of length 4 or lower')
        message = Message.message_types['CONNECTION']+self.udp_port.encode(ENCODING)
        message += b' '*(comum.CONNECTION_MESSAGE_SIZE - len(message))
        return message
    
    def decode(message):
        udp_port = int(message[2:6].decode(ENCODING))
        return ConnectionMessage(udp_port)

class InfoFileMessage(Message):
    def __init__(self, file_name, file_size):
        super().__init__('INFO FILE')
        self.file_name = file_name
        self.file_size = file_size

    def validate_file_size(self):
        max_file_size_len = 8
        if len(self.file_size)>max_file_size_len:
            raise Exception('File is too big, this service only accepts files up to 99999999 B')
    
    def validate_file_name(self):
        max_file_name_len = 15
        if len(self.file_name) > max_file_name_len:
            raise UnicodeEncodeError('Nome do arquivo grande demais')
        if self.file_name[-4]!='.':
            raise UnicodeEncodeError('Nome do arquivo deve terminar com . + 3 caracteres')
    
    def encode(self):
        self.validate_file_name()
        self.validate_file_size()
        file_name = self.file_name.encode(ENCODING)
        file_size = self.file_size.encode(ENCODING)
        message = Message.message_types['INFO FILE'] + file_name + file_size
        message += b' '*(comum.INFO_FILE_MESSAGE_SIZE- len(message))
        return message
    
    def decode(message):
        dot_idx = message.find(b'.')
        file_name = message[2:dot_idx+4].decode(ENCODING)
        file_size = int(message[dot_idx+4:])
        return InfoFileMessage(file_name, file_size)
