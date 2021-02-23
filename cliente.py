import socket
import argparse
from src import comum
from src.message_factory import MessageFactory
#TODO ler arquivo dado na entrada, pegar o tamanho, dividir em pedaços de arquivo

def main():
    args = get_arguments()

    tcp_addr = (args.ip, args.port)
    client = comum.create_socket(args.ip,socket.SOCK_STREAM)  
    client.connect(tcp_addr)
    send_hello(client)
    udp_port = handle_connection_message(client)
    if not udp_port:
        terminate_control_channel(client)
        return
    
    file_content_idk = send_info_file(client, "teste.txt")
    if not file_content_idk:
        terminate_control_channel(client)
        return
    
    while True:
        if handle_fim(client):
            print(f"[CONTROL CHANNEL] Closing connection...")
            client.close()
            break


def get_arguments():
    parser = argparse.ArgumentParser("Cliente que envia arquivo para nuvem")
    parser.add_argument('ip',type=str,help="Server ip address")
    parser.add_argument('port',type=int,help="Server tcp port")
    parser.add_argument('file',type=str,help="File to send")
    return parser.parse_args()

def send_hello(client):
    print(f"[CONTROL CHANNEL] Connected to TCP server")
    print(f"[CONTROL CHANNEL] Sending HELLO...")
    message = MessageFactory.build("HELLO")
    client.send(message)

def handle_connection_message(client):
    msg = client.recv(comum.CONNECTION_MESSAGE_SIZE)
    decoded_message = MessageFactory.decode(msg)
    if decoded_message.type != "CONNECTION":
        print(f"[CONTROL CHANNEL] Server did not sent a valid CONNECTION message")
        return None
    print(f"[CONTROL CHANNEL] Received a CONNECTION message with port", decoded_message.udp_port)
    return decoded_message.udp_port

def send_info_file(client, file_name):
    #TODO: get file size and contents
    try:
        message = MessageFactory.build("INFO FILE", file_name= file_name, file_size= 200)
    except UnicodeEncodeError as err:
        print("Nome não permitido")
        if 'ascii' in err.args[0]:
            print("So podem caracteres da tabela ASCII")
        else:
            print(err.args[0])
        return None

    print(f"[CONTROL CHANNEL] Sending INFO FILE...")
    client.send(message)
    return 1

def handle_fim(client):
    msg = client.recv(comum.SIMPLE_MESSAGE_SIZE)
    decoded_message = MessageFactory.decode(msg)
    print(f"[CONTROL CHANNEL] Received a", decoded_message.type)
    if decoded_message.type == "FIM":
        print(f"[CONTROL CHANNEL] Server finished processing file")
        return True
    return False
        

def terminate_control_channel(client):
    print(f"[CONTROL CHANNEL] Terminating connection")
    client.close()

if __name__ == "__main__":
    main()