import sys
import json
import argparse
import socket
import re
from config import SERVER_PORT

def is_valid_ip(ip):
    ip_pattern = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')
    return bool(ip_pattern.match(ip))

def send_message_to_server(message):
    try:
        client_ipv4_address = "127.0.0.1"
        print(f"Sending message to Server {client_ipv4_address}:{SERVER_PORT}")
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        client_socket.sendto(message.encode(), (client_ipv4_address, SERVER_PORT))

        response, _ = client_socket.recvfrom(1024)
        decoded_response = response.decode()
        print(f"Server Response: {decoded_response}")

        client_socket.close()

    except Exception as e:
        print(f"Error sending message to the Server: {e}")

def arg_parser():
    parser = argparse.ArgumentParser(description='Send commands to the server.')
    parser.add_argument('-a', metavar="ip", help='add IP address to the server')
    parser.add_argument('-d', metavar="ip", help='delete IP address from the server')

    res = parser.parse_args()
    if res.a is not None:
        cmd = "add"
        ip = res.a
    elif res.d is not None:
        cmd = "del"
        ip = res.d
    else:
        parser.print_help()
        sys.exit(1)

    if not is_valid_ip(ip):
        print("Invalid IP address format. Please use a valid IPv4 address.")
        sys.exit(1)

    return cmd, ip

if __name__ == "__main__":
    cmd, ip = arg_parser()
    command = {"cmd": cmd, "ip": ip}
    str_data = json.dumps(command)
    send_message_to_server(str_data)
