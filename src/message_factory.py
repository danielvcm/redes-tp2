from .message import Message, ConnectionMessage, InfoFileMessage

class MessageFactory:
    def build(message_type, **kwargs):
        if message_type not in Message.message_types:
            raise Exception(f"Message type should be one of {[key for key in Message.message_types]}")
    
        if message_type == 'CONNECTION':
            if 'udp_port' not in kwargs:
                raise Exception('udp_port must be passed as an argument for this kind of message')
            udp_port = str(kwargs['udp_port'])
            message = ConnectionMessage(udp_port)
            return message.encode()
        
        if message_type == 'INFO FILE':
            if 'file_name' not in kwargs:
                raise Exception('file_name must be passed as an argument for this kind of message')
            file_name = str(kwargs['file_name'])
            if 'file_size' not in kwargs:
                raise Exception('file_size must be passed as an argument for this kind of message')
            file_size = str(kwargs['file_size'])
            message = InfoFileMessage(file_name, file_size)
            return message.encode()
        
        else: #mensagens simples
            return Message(message_type).encode()

    def decode(message: bytes):
        type_header = message[0:2]

        if type_header == Message.message_types["CONNECTION"]:
            try:
                return ConnectionMessage.decode(message)
            except:
                return Message(None)
        
        elif type_header == Message.message_types["INFO FILE"]:
            try:
                return InfoFileMessage.decode(message)
            except:
                return Message(None)
            
        else:
            return Message.decode(message)
