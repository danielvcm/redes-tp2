import socket
import argparse
import comum
def main():
    args = get_arguments()
    tcp_addr = (args.ip, args.port)
    if comum.is_valid_ipv6_address(args.ip):
        client = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    else:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
    client.connect(tcp_addr)
    message = comum.MessagesFactory.build("HELLO")
    client.send(message)
    msg = client.recv(6)
    decoded_message = comum.MessagesFactory.decode(msg)
    print(f"[SERVER] Sent a", msg)
    if not decoded_message.type:
        print(f"[SERVER] Sent a unkown message type")
        print(f"[SERVER] Terminating connection")
        client.close()
        return
    
    if decoded_message.type == "FIM":
        print(f"[SERVER] Server finished processing file")
        print(f"[SERVER] Closing connection...")
        client.close()


def get_arguments():
    parser = argparse.ArgumentParser("Cliente que envia arquivo para nuvem")
    parser.add_argument('ip',type=str,help="Server ip address")
    parser.add_argument('port',type=int,help="Server tcp port")
    parser.add_argument('file',type=str,help="File to send")
    return parser.parse_args()

if __name__ == "__main__":
    main()