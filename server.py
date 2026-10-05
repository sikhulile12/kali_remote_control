#!/usr/bin/env python3
"""Minimal remote-control server for authorized administration use.

Usage:
    python3 server.py --host 0.0.0.0 --port 9000

Then type shell commands at the prompt and they will be executed on the remote client.
"""

import argparse
import socket
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


def send_message(sock, payload):
    sock.sendall(len(payload).to_bytes(4, byteorder="big", signed=False))
    sock.sendall(payload)


def recv_message(sock):
    header = recv_exact(sock, 4)
    if not header:
        return None
    length = int.from_bytes(header, byteorder="big", signed=False)
    if length == 0:
        return b""
    return recv_exact(sock, length)


def handle_client(conn, addr):
    print(f"[+] Connection from {addr[0]}:{addr[1]}")
    while True:
        try:
            command = input("remote> ").strip()
        except EOFError:
            print("\n[!] No more input. Closing session.")
            break
        if not command:
            continue
        if command.lower() in {"exit", "quit", "close"}:
            send_message(conn, b"QUIT")
            print(f"[+] Closing session with {addr[0]}:{addr[1]}")
            break

        send_message(conn, command.encode("utf-8"))
        response = recv_message(conn)
        if response is None:
            print(f"[!] Remote host disconnected from {addr[0]}:{addr[1]}")
            break

        print(response.decode("utf-8", errors="replace"), end="")

    conn.close()


def start_server(host="0.0.0.0", port=9000):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, int(port)))
    server.listen(5)
    print(f"[+] Remote control server listening on {host}:{port}")

    try:
        while True:
            conn, addr = server.accept()
            handle_client(conn, addr)
    except KeyboardInterrupt:
        print("\n[!] Server shutdown requested.")
    finally:
        server.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Minimal remote-control server for authorized use.")
    parser.add_argument("--host", default="0.0.0.0", help="Address to bind the server to.")
    parser.add_argument("--port", type=int, default=9000, help="TCP port to listen on.")
    args = parser.parse_args()

    start_server(args.host, args.port)
