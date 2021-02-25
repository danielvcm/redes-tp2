import socket
import threading
import argparse
import time
import logging

from src import comum
from src.comum import LogHelper
from src.message_factory import MessageFactory
from src.streamed_file import StreamedFile

class ConnectingClient:
    def __init__(self, addr: tuple, control_channel: socket.socket, data_channel: socket.socket) -> None:
        self.addr = addr
        self.control_channel = control_channel
        self.data_channel = data_channel
    
    def create_streamed_file(self, file_name, file_size):
        self.streamed_file = StreamedFile(file_name, file_size)

def main():
    args = get_arguments()
    host = socket.gethostbyname(socket.gethostname())
    logging.basicConfig(level=LogHelper.log_levels[args.verbose],format=LogHelper.log_format)
    tcp_server = create_server(host, args.port, socket.SOCK_STREAM)

    tcp_server.listen()
    print(f"TCP Server listening on {host}:{args.port}...")

    try:
        while True:
            control_channel, addr = tcp_server.accept()
            data_channel = create_server(host, 0, socket.SOCK_DGRAM) #quando se passa 0, o SO te dá uma porta livre

            thread = threading.Thread(target = handle_client, args = (ConnectingClient(addr,control_channel,data_channel),))
            thread.start()
    
    except KeyboardInterrupt:
        tcp_server.close()
        print("\nClosing server...")
        exit()

def get_arguments():
    parser = argparse.ArgumentParser(description="Servidor de arquivos na nuvem")
    parser.add_argument('port',type=int,help="TCP port")
    parser.add_argument('-v','--verbose',help='Select logging level',choices=[key for key in LogHelper.log_levels], default='info')
    return parser.parse_args()

def create_server(host, port, socket_type):
    addr = (host, port)
    server = comum.create_socket(host, socket_type)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(addr)
    return server

def handle_client(client: ConnectingClient):
    logging.info("Connected to TCP channel",extra=LogHelper.set_extra('CONTROL',client.addr))
    
    if not handle_hello(client):
        terminate_control_channel(client)
        return
    
    send_connection(client)

    if not handle_info_file(client):
        terminate_control_channel(client)
        return
    
    send_ok(client)

    handle_file(client)

    if not client.streamed_file.export_file():
        logging.warning("Something went wrong while exporting file", extra=LogHelper.set_extra('DATA',client.addr))
        terminate_data_channel(client)
        terminate_control_channel(client)
        
    
    send_fim(client)

    logging.info("Closing channel...",extra=LogHelper.set_extra('CONTROL',client.addr))
    client.control_channel.close()

    return

def handle_hello(client):
    msg = client.control_channel.recv(comum.SIMPLE_MESSAGE_SIZE)
    decoded_message = MessageFactory.decode(msg)
    logging.debug(f"Received a {decoded_message.type}", extra=LogHelper.set_extra('CONTROL',client.addr))
    if decoded_message.type != "HELLO":
        logging.warning("Client did not sent HELLO",extra=LogHelper.set_extra("CONTROL", client.addr))
        return False
    return True

def send_connection(client):
    udp_port = client.data_channel.getsockname()[1]
    msg = MessageFactory.build("CONNECTION",udp_port = udp_port)
    logging.debug(f"Sending CONNECTION message with port {udp_port}",extra=LogHelper.set_extra("CONTROL", client.addr))
    client.control_channel.send(msg)

def handle_info_file(client):
    msg = client.control_channel.recv(comum.INFO_FILE_MESSAGE_SIZE)
    decoded_message = MessageFactory.decode(msg)
    logging.debug(f"Received a {decoded_message.type}", extra=LogHelper.set_extra('CONTROL',client.addr))
    if decoded_message.type != "INFO FILE":
        logging.warning("Client did not sent a valid INFO FILE", extra=LogHelper.set_extra('CONTROL',client.addr))
        return False
    client.create_streamed_file(decoded_message.file_name, decoded_message.file_size)
    logging.debug("Finished allocating structures for file", extra=LogHelper.set_extra('CONTROL',client.addr))
    return True

def send_ok(client):
    logging.debug("Sending OK", extra=LogHelper.set_extra('CONTROL',client.addr))
    msg = MessageFactory.build("OK")
    client.control_channel.send(msg)

def handle_file(client):
    logging.info("Started listening for file parts...",extra=LogHelper.set_extra('DATA',client.addr))
    while not client.streamed_file.finished_streaming():
        msg = client.data_channel.recvmsg(comum.FILE_MESSAGE_SIZE)
        decoded_message = MessageFactory.decode(msg[0])
        logging.debug(f"Received payload #{decoded_message.serial_number}...",extra=LogHelper.set_extra('DATA',client.addr))
        client.streamed_file.set_payload(decoded_message.serial_number, decoded_message.payload)
        threading.Thread(target = handle_ack, args = (client, decoded_message.serial_number)).start()
    
def handle_ack(client: ConnectingClient, serial_number):
    while True:
        if client.streamed_file.sliding_window.can_send(serial_number):
            logging.debug(f"Sending ACK to payload #{serial_number}...",extra=LogHelper.set_extra('DATA',client.addr))
            message = MessageFactory.build('ACK', serial_number = serial_number)
            client.control_channel.send(message)
            client.streamed_file.sliding_window.acked(serial_number)
            break
        else:
            time.sleep(1)

def send_fim(client):
    logging.info(f"Finished processing file",extra=LogHelper.set_extra('DATA',client.addr))
    logging.info("Closing channel...",extra=LogHelper.set_extra('DATA',client.addr))
    client.data_channel.close()
    logging.debug("Sending FIM",extra=LogHelper.set_extra('CONTROL',client.addr))
    msg = MessageFactory.build("FIM")
    client.control_channel.send(msg)

def terminate_control_channel(client):
    logging.warning("Terminating connection",extra=LogHelper.set_extra('CONTROL',client.addr))
    client.control_channel.close()

def terminate_data_channel(client):
    logging.warning("Terminating connection",extra=LogHelper.set_extra('DATA',client.addr))
    client.data_channel.close()

if __name__== "__main__":
    main()