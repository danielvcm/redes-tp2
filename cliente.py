import socket
import argparse
import comum
from messages import MessagesFactory
#TODO refatorar isso aqui pq socorro esse tamanho de main
#TODO ler arquivo dado na entrada, pegar o tamanho, dividir em pedaços de arquivo

def main():
    args = get_arguments()
    tcp_addr = (args.ip, args.port)
    client = comum.create_socket(args.ip,socket.SOCK_STREAM)
  
    client.connect(tcp_addr)
    print(f"[CONTROL CHANNEL] Connected to TCP server")
    print(f"[CONTROL CHANNEL] Sending HELLO...")
    message = MessagesFactory.build("HELLO")
    client.send(message)

    msg = client.recv(comum.CONNECTION_MESSAGE_SIZE)
    decoded_message = MessagesFactory.decode(msg)
    if decoded_message.type != "CONNECTION":
        print(f"[CONTROL CHANNEL] Server did not sent a valid CONNECTION message")
        print(f"[CONTROL CHANNEL] Terminating connection")
        client.close()
        return
    print(f"[CONTROL CHANNEL] Received a CONNECTION message with port", decoded_message.udp_port)
    try:
        message = MessagesFactory.build("INFO FILE", file_name= 'teste.txt', file_size= 200)
    except UnicodeEncodeError as err:
        print("Nome não permitido")
        if 'ascii' in err.args[0]:
            print("So podem caracteres da tabela ASCII")
        else:
            print(err.args[0])
        print(f"[CONTROL CHANNEL] Terminating connection")
        client.close()
        return

    print(f"[CONTROL CHANNEL] Sending INFO FILE...")
    client.send(message)

    msg = client.recv(comum.SIMPLE_MESSAGE_SIZE)
    decoded_message = MessagesFactory.decode(msg)
    print(f"[CONTROL CHANNEL] Received a", decoded_message.type)
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