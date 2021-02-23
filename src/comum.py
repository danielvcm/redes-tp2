import socket

SIMPLE_MESSAGE_SIZE = 2
CONNECTION_MESSAGE_SIZE = 6
INFO_FILE_MESSAGE_SIZE = 25

def create_socket(ip, socket_type):
    if is_valid_ipv6_address(ip):
        return socket.socket(socket.AF_INET6, socket_type)
    return socket.socket(socket.AF_INET, socket_type)

def is_valid_ipv6_address(address):
    try:
        socket.inet_pton(socket.AF_INET6, address)
    except socket.error:
        return False
    return True