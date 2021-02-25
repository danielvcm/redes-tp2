import socket
import threading
import argparse

from src import comum
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
        print("\nServers closing...")
        exit()

def get_arguments():
    parser = argparse.ArgumentParser(description="Servidor de arquivos na nuvem")
    parser.add_argument('port',type=int,help="TCP port")
    return parser.parse_args()

def create_server(host, port, socket_type):
    addr = (host, port)
    server = comum.create_socket(host, socket_type)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(addr)
    return server

def handle_client(client: ConnectingClient):
    print(f"[NEW CONNECTION] {client.addr} connected to TCP channel")
    
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
        print(f"[{client.addr} - DATA CHANNEL] something went wrong while exporting file")
        terminate_data_channel(client)
        terminate_control_channel(client)
        
    
    send_fim(client)

    print(f"[{client.addr} - CONTROL CHANNEL] Closing channel...")
    client.control_channel.close()

    return

def handle_hello(client):
    msg = client.control_channel.recv(comum.SIMPLE_MESSAGE_SIZE)
    decoded_message = MessageFactory.decode(msg)
    print(f"[{client.addr} - CONTROL CHANNEL] Received a", decoded_message.type)
    if decoded_message.type != "HELLO":
        print(f"[{client.addr} - CONTROL CHANNEL] Client did not sent HELLO")
        return False
    return True

def send_connection(client):
    udp_port = client.data_channel.getsockname()[1]
    msg = MessageFactory.build("CONNECTION",udp_port = udp_port)
    print(f"[{client.addr} - CONTROL CHANNEL] Sending CONNECTION message with port {udp_port}")
    client.control_channel.send(msg)

def handle_info_file(client):
    msg = client.control_channel.recv(comum.INFO_FILE_MESSAGE_SIZE)
    decoded_message = MessageFactory.decode(msg)
    print(f"[{client.addr} - CONTROL CHANNEL] Received a", decoded_message.type)
    if decoded_message.type != "INFO FILE":
        print(f"[{client.addr} - CONTROL CHANNEL] Client did not sent a valid INFO FILE")
        return False
    client.create_streamed_file(decoded_message.file_name, decoded_message.file_size)
    print(f"[{client.addr} - CONTROL CHANNEL] Finished allocating structures for file")
    return True

def send_ok(client):
    print(f"[{client.addr} - CONTROL CHANNEL] Sending OK")
    msg = MessageFactory.build("OK")
    client.control_channel.send(msg)

def handle_file(client):
    print(f"[{client.addr} - DATA CHANNEL] Started listening for file parts...")
    while not client.streamed_file.finished_streaming():
        msg = client.data_channel.recvmsg(comum.FILE_MESSAGE_SIZE)
        decoded_message = MessageFactory.decode(msg[0])
        print(f"[{client.addr} - DATA CHANNEL] Received payload #{decoded_message.serial_number}...")
        client.streamed_file.set_payload(decoded_message.serial_number, decoded_message.payload)
        #ack
    


def send_fim(client):
    print(f"[{client.addr} - DATA CHANNEL] Finished processing file")
    print(f"[{client.addr} - DATA CHANNEL] Closing channel...")
    client.data_channel.close()
    print(f"[{client.addr} - CONTROL CHANNEL] Sending FIM")
    msg = MessageFactory.build("FIM")
    client.control_channel.send(msg)

def terminate_control_channel(client):
    print(f"[{client.addr} - CONTROL CHANNEL] Terminating connection")
    client.control_channel.close()

def terminate_data_channel(client):
    print(f"[{client.addr} - DATA CHANNEL] Terminating connection")
    client.data_channel.close()

if __name__== "__main__":
    main()