from .message import Message, ConnectionMessage, InfoFileMessage, FileMessage
from . import comum
class MessageFactory:
    def build(message_type, **kwargs):
        if message_type not in Message.message_types:
            raise Exception(f"Message type should be one of {[key for key in Message.message_types]}")
    
        elif message_type == 'CONNECTION':
            udp_port = str(MessageFactory.get_arg('udp_port',kwargs))
            message = ConnectionMessage(udp_port)
            return message.encode()
        
        elif message_type == 'INFO FILE':
           
            file_name = str(MessageFactory.get_arg('file_name', kwargs))
            file_size = str(MessageFactory.get_arg('file_size', kwargs))

            message = InfoFileMessage(file_name, file_size)
            return message.encode()
        
        elif message_type == 'FILE':
            serial_number = int(MessageFactory.get_arg('serial_number', kwargs))
            payload_size = int(MessageFactory.get_arg('payload_size', kwargs))
            payload = MessageFactory.get_arg('payload', kwargs)
            message = FileMessage(serial_number, payload_size, payload)
            return message.encode()
        
        else: #mensagens simples
            return Message(message_type).encode()

    def decode(message: bytes):
        type_header = message[0:comum.SIMPLE_MESSAGE_SIZE]
        try:
            if type_header == Message.message_types["CONNECTION"]:
                return ConnectionMessage.decode(message)
            
            elif type_header == Message.message_types["INFO FILE"]:
                return InfoFileMessage.decode(message)
            
            elif type_header == Message.message_types['FILE']:
                return FileMessage.decode(message)
            
            else:
                return Message.decode(message)
        except:
            return Message(None)

    def get_arg(arg_name, kwargs):
        if arg_name not in kwargs:
            raise Exception(f'{arg_name} must be passed as an argument for this kind of message')
        return kwargs[arg_name]