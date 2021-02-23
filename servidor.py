import socket
import threading
import argparse
import comum
from messages import MessagesFactory
UDP_PORT = 50

def main():
    args = get_arguments()
    host = socket.gethostbyname(socket.gethostname())
    tcp_addr = (host, args.port)

    if comum.is_valid_ipv6_address(host):
        server = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    else:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    server.bind(tcp_addr)

    server.listen()
    print(f"Server listening on {host}:{args.port}...")
    try:
        while True:
            conn, addr = server.accept()
            thread = threading.Thread(target = handle_client, args = (conn, addr))
            thread.start()
    
    except KeyboardInterrupt:
        print("\nServer closing...")
        exit()


def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected to TCP channel")
    
    msg = conn.recv(2)
    decoded_message = MessagesFactory.decode(msg)
    print(f"[{addr}] Sent a", decoded_message.type)
    if decoded_message.type != "HELLO":
        print(f"[{addr}] Did not follow the handshake correctly")
        print(f"[{addr}] Terminating connection")
        conn.close()
        return
    msg = MessagesFactory.build("CONNECTION",udp_port = UDP_PORT)
    conn.send(msg)
    print(f"[{addr}] Finished processing file")
    print(f"[{addr}] Acknowledging client")
    msg = MessagesFactory.build("FIM")
    conn.send(msg)
    print(f"[{addr}] Closing connection...")
    conn.close()

def handle_udp():
    pass

def get_arguments():
    parser = argparse.ArgumentParser(description="Servidor de arquivos na nuvem")
    parser.add_argument('port',type=int,help="TCP port")
    return parser.parse_args()

if __name__== "__main__":
    main()