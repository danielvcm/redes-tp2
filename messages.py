import comum
#TODO refatorar isso aqui pq socorro esse tamanho de build

ENCODING = 'ascii'
class MessagesFactory:
    message_types = {'HELLO':b'1 ',
            'CONNECTION': b'2 ',
            'INFO FILE': b'3 ',
            'OK': b'4 ',
            'FIM': b'5 ',
            'FILE': b'6 ',
            'ACK': b'7 '}
    def build(message_type, **kwargs):
        if message_type not in MessagesFactory.message_types:
            raise Exception(f"Message type should be one of {[key for key in MessagesFactory.message_types]}")

        if message_type in ['HELLO', 'OK', 'FIM']:
            return MessagesFactory.message_types[message_type]
        
        if message_type == 'CONNECTION':
            if 'udp_port' not in kwargs:
                raise Exception('udp_port must be passed as an argument for this kind of message')
            udp_port = str(kwargs['udp_port'])
            if len(udp_port) > 4:
                raise Exception('udp_port must be of length 4 or lower')
            message = MessagesFactory.message_types['CONNECTION']+udp_port.encode(ENCODING)
            message += b' '*(comum.CONNECTION_MESSAGE_SIZE - len(message))
            return message
        
        if message_type == 'INFO FILE':
            max_file_size_len = 8
            max_file_name_len = 15
            if 'file_name' not in kwargs:
                raise Exception('file_name must be passed as an argument for this kind of message')
            file_name = str(kwargs['file_name'])
            if 'file_size' not in kwargs:
                raise Exception('file_size must be passed as an argument for this kind of message')
            file_size = str(kwargs['file_size'])
            if len(file_name) > max_file_name_len:
                raise UnicodeEncodeError('Nome do arquivo grande demais')
            if file_name[-4]!='.':
                raise UnicodeEncodeError('Nome do arquivo deve terminar com . + 3 caracteres')
            file_name = file_name.encode(ENCODING)
            
            if len(file_size)>max_file_size_len:
                raise Exception('File is too big, this service only accepts files up to 99999999 B')
            file_size = file_size.encode(ENCODING)
            message = MessagesFactory.message_types['INFO FILE'] + file_name + file_size
            message += b' '*(comum.INFO_FILE_MESSAGE_SIZE- len(message))
            return message


    def decode(message: bytes):
        type_header = message[0:2]
        if type_header == MessagesFactory.message_types["HELLO"]:
            return Message("HELLO")
        elif type_header == MessagesFactory.message_types["CONNECTION"]:
            try:
                udp_port = int(message[2:6].decode(ENCODING))
                return ConnectionMessage("CONNECTION",udp_port)
            except ValueError:
                return Message(None)
        elif type_header == MessagesFactory.message_types["INFO FILE"]:
            try:
                dot_idx = message.find(b'.')
                file_name = message[2:dot_idx+4].decode(ENCODING)
                file_size = int(message[dot_idx+4:])
                return FileInfoMessage("INFO FILE", file_name, file_size)
            except:
                return Message(None)
            
        elif type_header == MessagesFactory.message_types["OK"]:
            return Message("OK")
        elif type_header == MessagesFactory.message_types["FIM"]:
            return Message("FIM")
        else:
            return Message(None)

class Message:
    def __init__(self, type):
        self.type = type

class ConnectionMessage(Message):
    def __init__(self, type, udp_port):
        super().__init__(type)
        self.udp_port = udp_port

class FileInfoMessage(Message):
    def __init__(self, type, file_name, file_size):
        super().__init__(type)
        self.file_name = file_name
        self.file_size = file_size