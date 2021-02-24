import socket
import threading
import argparse

from src import comum
from src.message_factory import MessageFactory
from src.streamed_file import StreamedFile

UDP_PORT = 5042

#TODO Criar estrutura de dados pra receber o arquivo
#   importante ter: addr do cliente, janela deslizante (?), vetor com pedaços do arquivo (outra classe pedaço?)
class ConnectingClient:
    def __init__(self, addr: tuple, control_channel: socket.socket, data_server: socket.socket) -> None:
        self.addr = addr
        self.control_channel = control_channel
        self.data_server = data_server
    
    def create_streamed_file(self, file_name, file_size):
        self.streamed_file = StreamedFile(self.addr, file_name, file_size)

def main():
    args = get_arguments()
    host = socket.gethostbyname(socket.gethostname())

    tcp_server = create_server(host, args.port, socket.SOCK_STREAM)
    udp_server = create_server(host, UDP_PORT, socket.SOCK_DGRAM)

    tcp_server.listen()
    print(f"TCP Server listening on {host}:{args.port}...")

    try:
        while True:
            control_channel, addr = tcp_server.accept()
            thread = threading.Thread(target = handle_client, args = (ConnectingClient(addr,control_channel,udp_server),))
            thread.start()
    
    except KeyboardInterrupt:
        tcp_server.close()
        udp_server.close()
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

    send_fim(client)

    print(f"[{client.addr} - CONTROL CHANNEL] Closing connection...")
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
    udp_port = client.data_server.getsockname()[1]
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

def send_fim(client):
    print(f"[{client.addr} - CONTROL CHANNEL] Finished processing file")
    print(f"[{client.addr} - CONTROL CHANNEL] Acknowledging client")
    msg = MessageFactory.build("FIM")
    client.control_channel.send(msg)

def terminate_control_channel(client):
    print(f"[{client.addr} - CONTROL CHANNEL] Terminating connection")
    client.control_channel.close()

if __name__== "__main__":
    main()