from src import comum
from src.message_factory import MessageFactory
from src.sliding_window import SlidingWindow
from src.comum import LogHelper
from src.progress_bar import ProgressBar

import socket
import argparse
import threading
import os
import time
import logging

TIMEOUT = 5

class FileControl:
    def __init__(self, file_name, data_channel: socket.socket, udp_addr: tuple) -> None:
        self.payloads = self.get_file_payloads(file_name)

        file_size = os.path.getsize('./'+file_name)
        self.sliding_window = SlidingWindow(file_size)

        self.data_channel = data_channel
        self.udp_addr = udp_addr

    
    def get_file_payloads(self, file_name):
        file_payloads = {}

        with open(file_name,'rb') as file_to_send:
            serial_number = 0
            payload = file_to_send.read(comum.MAX_FILE_PART_SIZE)
            while payload != b"":
                file_payloads[serial_number] = payload

                serial_number +=1
                payload = file_to_send.read(comum.MAX_FILE_PART_SIZE)

        return file_payloads

    
def main():
    args = get_arguments()
    logging.basicConfig(level=LogHelper.log_levels[args.verbose],format=LogHelper.log_format)
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
        
    udp_addr = (args.ip, udp_port)
    data_channel = comum.create_socket(args.ip, socket.SOCK_DGRAM)
    print(f"[{udp_addr[0]}:{udp_addr[1]} - DATA CHANNEL] Connected to UDP server")

    file_control = FileControl(args.file,data_channel,udp_addr)
    threading.Thread(target = send_file,args = (file_control,)).start()

    if not handle_ack(client, file_control):
        terminate_data_channel(data_channel)
        terminate_control_channel(client)
        return
    
    if not handle_fim(client):
        terminate_data_channel(data_channel)
        terminate_control_channel(client)
        return

    print(f"[{udp_addr[0]}:{udp_addr[1]} - DATA CHANNEL] Closing connection...")
    data_channel.close()

    print(f"[{tcp_addr[0]}:{tcp_addr[1]} - CONTROL CHANNEL] Closing connection...")
    client.close()
    

def get_arguments():
    parser = argparse.ArgumentParser("Cliente que envia arquivo para nuvem")
    parser.add_argument('ip',type=str,help="Server ip address")
    parser.add_argument('port',type=int,help="Server tcp port")
    parser.add_argument('file',type=str,help="File to send")
    parser.add_argument('-v','--verbose',help='Select logging level',choices=[key for key in LogHelper.log_levels], default='info')
    return parser.parse_args()

def send_hello(client:socket.socket):
    print(f"[{client.getsockname()[0]}:{client.getsockname()[1]} - CONTROL CHANNEL]Connected to TCP server")
    logging.debug("Sending HELLO...",extra=LogHelper.set_extra('CONTROL',client.getsockname()))
    message = MessageFactory.build("HELLO")
    client.send(message)

def handle_connection_message(client):
    msg = client.recv(comum.CONNECTION_MESSAGE_SIZE)
    decoded_message = MessageFactory.decode(msg)
    if decoded_message.type != "CONNECTION":
        logging.warning("Server did not sent a valid CONNECTION message",extra=LogHelper.set_extra('CONTROL',client.getsockname()))
        return None
    logging.debug(f"Received a CONNECTION message with port {decoded_message.udp_port}",extra=LogHelper.set_extra('CONTROL',client.getsockname()))
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

    logging.debug(f"Sending INFO FILE...",extra=LogHelper.set_extra('CONTROL',client.getsockname()))
    client.send(message)
    return True

def handle_ok(client):
    msg = client.recv(comum.SIMPLE_MESSAGE_SIZE)
    decoded_message = MessageFactory.decode(msg)

    if decoded_message.type != "OK":
        logging.warning(f"Server did not send OK",extra=LogHelper.set_extra('CONTROL',client.getsockname()))
        return False
    
    logging.debug(f"Received an OK to proceed sending the file",extra=LogHelper.set_extra('CONTROL',client.getsockname()))
    return True

def send_file(file_control: FileControl):
    print(f"[{file_control.udp_addr[0]}:{file_control.udp_addr[1]} - DATA CHANNEL] Started to send file...\n")
    i = 0
    while True:
        if i == len(file_control.payloads):
            break
        elif file_control.sliding_window.can_send(i):
            threading.Thread(target = send_file_part,args = (file_control,i)).start()
            i+=1
        else:
            time.sleep(1)
    
def send_file_part(file_control: FileControl, serial_number):
    payload = file_control.payloads[serial_number]
    message = MessageFactory.build("FILE",serial_number = serial_number, payload = payload, payload_size = len(payload))

    #enquanto o pacote não tiver sido enviado corretamente
    while not file_control.sliding_window.get_transmitted(serial_number):
        logging.debug(f"Sending payload #{serial_number}",extra=LogHelper.set_extra('DATA',file_control.udp_addr))
        file_control.data_channel.sendto(message, file_control.udp_addr)
        file_control.sliding_window.set_transmitted(serial_number,True)
        
        #essa thread dorme por TIMEOUT segundos
        time.sleep(TIMEOUT)
        
        #se depois de TIMEOUT segundos o arquivo ainda não foi acked pelo servidor, se mantém no loop
        if not file_control.sliding_window.get_acked(serial_number):
            logging.debug(f"Payload #{serial_number} wasn't acked, will resend",extra=LogHelper.set_extra('DATA',file_control.udp_addr))
            file_control.sliding_window.set_transmitted(serial_number,False)

def handle_ack(client: socket.socket, file_control: FileControl):
    acked_msgs = 0
    progress_bar = None
    if logging.getLevelName(logging.root.level) !=  'DEBUG':
        progress_bar = ProgressBar(len(file_control.payloads))
        print('Upload progress:')
        progress_bar.init_print()
    while acked_msgs < len(file_control.payloads):
        msg = client.recv(comum.ACK_MESSAGE_SIZE)
        decoded_message = MessageFactory.decode(msg)
        if decoded_message.type != "ACK" and decoded_message.type == 'FIM':
            logging.warning("Did not receive enough ACKs",extra=LogHelper.set_extra('CONTROL',client.getsockname()))
            return False
        if decoded_message.type == 'ACK':
            logging.debug(f"Received ACK for payload #{decoded_message.serial_number}",extra=LogHelper.set_extra('CONTROL',client.getsockname()))
            file_control.sliding_window.acked(decoded_message.serial_number)
            if progress_bar:
                progress_bar.increase()
            acked_msgs +=1
    if progress_bar:
        progress_bar.end_print()
    return True
        
def handle_fim(client):
    msg = client.recv(comum.SIMPLE_MESSAGE_SIZE)
    decoded_message = MessageFactory.decode(msg)

    if decoded_message.type != "FIM":
        logging.warning(f"[CONTROL CHANNEL] Server did not send FIM",extra=LogHelper.set_extra('CONTROL',client.getsockname()))
        return False

    print(f"\n[{client.getsockname()[0]}:{client.getsockname()[1]} - CONTROL CHANNEL] Server finished processing file")
    return True

def terminate_control_channel(client):
    logging.warning(f"Terminating connection",extra=LogHelper.set_extra('CONTROL',client.getsockname()))
    client.close()

def terminate_data_channel(data_channel):
    logging.warning(f"Terminating connection",extra=LogHelper.set_extra('DATA',data_channel.getsockname()))
    data_channel.close()

if __name__ == "__main__":
    main()