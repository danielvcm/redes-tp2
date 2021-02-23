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
            if 'UDP_PORT' not in kwargs:
                raise Exception('UDP_PORT must be passed as an argument for this kind of message')
            udp_port = str(kwargs['UDP_PORT'])
            if len(udp_port) > 4:
                raise Exception('UDP_PORT must be of length 4 or lower')
            if len(udp_port) < 4:
                udp_port = udp_port +' '*(len(udp_port)-4)
            message = MessagesFactory.message_types['CONNECTION']+bytes(udp_port.encode(ENCODING))
            return message

    def decode(message):
        type_header = message[0:2]
        if type_header == MessagesFactory.message_types["HELLO"]:
            return Message("HELLO")
        elif type_header == MessagesFactory.message_types["OK"]:
            return Message("OK")
        elif type_header == MessagesFactory.message_types["FIM"]:
            return Message("FIM")
        else:
            return Message(None)

class Message:
    def __init__(self, type):
        self.type = type
        
import socket

def is_valid_ipv6_address(address):
    try:
        socket.inet_pton(socket.AF_INET6, address)
    except socket.error:
        return False
    return True