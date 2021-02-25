import socket
import logging

SIMPLE_MESSAGE_SIZE = 2
CONNECTION_MESSAGE_SIZE = 6
INFO_FILE_MESSAGE_SIZE = 25
FILE_MESSAGE_SIZE = 1008
ACK_MESSAGE_SIZE = 6

MAX_FILE_PART_SIZE = 1000
WINDOW_SIZE = 4

class LogHelper:

    log_levels = {'debug': logging.DEBUG,
            'info': logging.INFO,
            'warning': logging.WARNING}
    log_format = "[%(host)s:%(port)s - %(channel_name)s CHANNEL] %(message)s"

    def set_extra(channel_name, addr):
        return {
            'host': addr[0],
            'port': addr[1],
            'channel_name': channel_name
            }

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