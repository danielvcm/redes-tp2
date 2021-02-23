import socket
import threading
import argparse
import comum
from messages import MessagesFactory
UDP_PORT = 5042
#TODO refatorar isso aqui pq socorro esse tamanho de main e handle_client
#TODO Criar estrutura de dados pra receber o arquivo
#   importante ter: addr do cliente, janela deslizante (?), vetor com pedaços do arquivo (outra classe pedaço?)
class ConnectingClient:
    def __init__(self, addr: tuple, control_channel: socket.socket, data_server: socket.socket) -> None:
        self.addr = addr
        self.control_channel = control_channel
        self.data_server = data_server

def main():
    args = get_arguments()
    host = socket.gethostbyname(socket.gethostname())
    tcp_addr = (host, args.port)

    server = comum.create_socket(host, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(tcp_addr)

    udp_addr = (host, UDP_PORT)
    data_server = comum.create_socket(host, socket.SOCK_DGRAM)
    data_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    data_server.bind(udp_addr)

    server.listen()
    print(f"TCP Server listening on {host}:{args.port}...")

    try:
        while True:
            control_channel, addr = server.accept()
            thread = threading.Thread(target = handle_client, args = (ConnectingClient(addr,control_channel,data_server),))
            thread.start()
    
    except KeyboardInterrupt:
        server.close()
        data_server.close()
        print("\nServers closing...")
        exit()


def handle_client(client: ConnectingClient):
    print(f"[NEW CONNECTION] {client.addr} connected to TCP channel")
    
    msg = client.control_channel.recv(comum.SIMPLE_MESSAGE_SIZE)
    decoded_message = MessagesFactory.decode(msg)
    print(f"[{client.addr} - CONTROL CHANNEL] Received a", decoded_message.type)
    if decoded_message.type != "HELLO":
        print(f"[{client.addr} - CONTROL CHANNEL] Client did not sent HELLO")
        print(f"[{client.addr} - CONTROL CHANNEL] Terminating connection")
        client.control_channel.close()
        return
    udp_port = client.data_server.getsockname()[1]
    msg = MessagesFactory.build("CONNECTION",udp_port = udp_port)
    print(f"[{client.addr} - CONTROL CHANNEL] Sending CONNECTION message with port {udp_port}")
    client.control_channel.send(msg)

    msg = client.control_channel.recv(comum.INFO_FILE_MESSAGE_SIZE)
    decoded_message = MessagesFactory.decode(msg)
    print(f"[{client.addr} - CONTROL CHANNEL] Received a", decoded_message.type)
    if decoded_message.type != "INFO FILE":
        print(f"[{client.addr} - CONTROL CHANNEL] Client did not sent a valid INFO FILE")
        print(f"[{client.addr} - CONTROL CHANNEL] Terminating connection")
        client.control_channel.close()
        return
    print(decoded_message.file_name, decoded_message.file_size)

    print(f"[{client.addr} - CONTROL CHANNEL] Finished processing file")
    print(f"[{client.addr} - CONTROL CHANNEL] Acknowledging client")
    msg = MessagesFactory.build("FIM")
    client.control_channel.send(msg)

    print(f"[{client.addr} - CONTROL CHANNEL] Closing connection...")
    client.control_channel.close()

def handle_udp():
    pass

def get_arguments():
    parser = argparse.ArgumentParser(description="Servidor de arquivos na nuvem")
    parser.add_argument('port',type=int,help="TCP port")
    return parser.parse_args()


if __name__== "__main__":
    main()