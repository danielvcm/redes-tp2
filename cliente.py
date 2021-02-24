import socket
import argparse
from src import comum
from src.message_factory import MessageFactory
import os

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
    
    if not send_info_file(client, args.file):
        terminate_control_channel(client)
        return
    
    if not handle_ok(client):
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
    try:
        file_size = os.path.getsize('./'+file_name)
    except:
        print(f"File {file_name} either doesn't exist or this program do not have access to it")
        return False
    
    try:
        message = MessageFactory.build("INFO FILE", file_name= file_name, file_size= file_size)
    
    except UnicodeEncodeError as err:
        print("Nome não permitido")
        if 'ascii' in err.args[0]:
            print("So podem caracteres da tabela ASCII")
        else:
            print(err.args[4])
        return False

    print(f"[CONTROL CHANNEL] Sending INFO FILE...")
    client.send(message)
    return True

def handle_ok(client):
    msg = client.recv(comum.SIMPLE_MESSAGE_SIZE)
    decoded_message = MessageFactory.decode(msg)

    if decoded_message.type != "OK":
        print(f"[CONTROL CHANNEL] Server did not send OK")
        return False
    
    print(f"[CONTROL CHANNEL] Received an OK to proceed sending the file")
    return True

def handle_fim(client):
    msg = client.recv(comum.SIMPLE_MESSAGE_SIZE)
    decoded_message = MessageFactory.decode(msg)
    print(f"[CONTROL CHANNEL] Received a", decoded_message.type)
    if decoded_message.type == "FIM":
        print(f"[CONTROL CHANNEL] Server finished processing file")
        return True
    return False

def get_file_payloads(file_name):
    file_payloads = []

    with open(file_name,'rb') as file_to_send:
        payload = file_to_send.read(comum.MAX_FILE_PART_SIZE)
        while payload != b"":
            file_payloads.append(payload)
            payload = file_to_send.read(comum.MAX_FILE_PART_SIZE)

    return file_payloads

def terminate_control_channel(client):
    print(f"[CONTROL CHANNEL] Terminating connection")
    client.close()

if __name__ == "__main__":
    main()