import socket
import argparse
import comum
from messages import MessagesFactory
def main():
    args = get_arguments()
    tcp_addr = (args.ip, args.port)
    if comum.is_valid_ipv6_address(args.ip):
        client = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    else:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
    client.connect(tcp_addr)
    message = MessagesFactory.build("HELLO")
    client.send(message)
    msg = client.recv(6)
    decoded_message = MessagesFactory.decode(msg)
    print(f"[CONTROL CHANNEL] Sent a", decoded_message.type)
    if decoded_message.type != "CONNECTION":
        print(f"[CONTROL CHANNEL] Server did not sent a valid CONNECTION message")
        print(f"[CONTROL CHANNEL] Terminating connection")
        client.close()
        return
    
    msg = client.recv(2)
    decoded_message = MessagesFactory.decode(msg)
    print(f"[CONTROL CHANNEL] Sent a", decoded_message.type)
    if decoded_message.type == "FIM":
        print(f"[CONTROL CHANNEL] Server finished processing file")
        print(f"[CONTROL CHANNEL] Closing connection...")
        client.close()


def get_arguments():
    parser = argparse.ArgumentParser("Cliente que envia arquivo para nuvem")
    parser.add_argument('ip',type=str,help="Server ip address")
    parser.add_argument('port',type=int,help="Server tcp port")
    parser.add_argument('file',type=str,help="File to send")
    return parser.parse_args()

if __name__ == "__main__":
    main()