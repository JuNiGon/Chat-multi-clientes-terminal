# client_chat.py

import socket
import threading
import sys

ENC = "utf-8"

try:
    raw_input
except NameError:
    raw_input = input

def recv_loop(sock):
    try:
        while True:
            data = sock.recv(4096)
            if not data:
                print("[connection closed by server]")
                break
            # printa exatamente o que recebeu
            sys.stdout.write(data.decode(ENC))
            sys.stdout.flush()
    except Exception:
        pass
    finally:
        try:
            sock.close()
        except:
            pass

def main():
    host = raw_input("Host (default 127.0.0.1): ").strip() or "127.0.0.1"
    port_s = raw_input("Port (default 5000): ").strip() or "5000"
    try:
        port = int(port_s)
    except:
        print("Porta inválida.")
        return

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    print("Conectado a %s:%d" % (host, port))

    t = threading.Thread(target=recv_loop, args=(sock,), daemon=True)
    t.start()

    try:
        while True:
            line = raw_input()
            if not line:
                continue
            sock.sendall((line + "\n").encode(ENC))
            if line.strip() == "/quit":
                break
    except KeyboardInterrupt:
        try:
            sock.sendall(("/quit\n").encode(ENC))
        except:
            pass
    finally:
        try:
            sock.close()
        except:
            pass
        print("Desconectado.")

if __name__ == "__main__":
    main()
