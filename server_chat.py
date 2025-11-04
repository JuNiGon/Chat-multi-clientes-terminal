import socket #rede
import threading #thread
import traceback #exceções

HOST = "0.0.0.0" #rede
PORT = 5000 #porta TCP
ENC = "utf-8" # padrão de codificação de caracteres

clients_lock = threading.Lock()
clients = {}
rooms = {}

def safe_send(conn, text): 
    try:
        conn.sendall((text + "\n").encode(ENC))
    except Exception:
        remove_client(conn) 

def broadcast(room, text, exclude_conn=None):
    with clients_lock:
        conns = list(rooms.get(room, set()))
    for conn in conns:
        if conn is exclude_conn:
            continue
        safe_send(conn, text)

def remove_client(conn):
    with clients_lock:
        info = clients.pop(conn, None)
        if info:
            room = info.get("room")
            nick = info.get("nick", "anon")
            if room and conn in rooms.get(room, set()):
                rooms[room].discard(conn)
                if not rooms[room]:
                    del rooms[room]
                try:
                    broadcast(room, "[server] %s saiu da sala." % nick, exclude_conn=None)
                except Exception:
                    pass
    try:
        conn.close()
    except Exception:
        pass

def handle_client(conn, addr):
    # inicializa cliente
    with clients_lock:
        clients[conn] = {"nick": "anon", "room": None}
    safe_send(conn, "Bem-vindo! Use /nick NOME , /join SALA , /quit")
    try:
        while True:
            data = conn.recv(4096)
            if not data:
                break
            text = data.decode(ENC).strip()
            if not text:
                continue

            # comandos
            if text.startswith("/nick "):
                newnick = text.split(" ", 1)[1].strip() or "anon"
                with clients_lock:
                    old = clients[conn]["nick"]
                    clients[conn]["nick"] = newnick
                safe_send(conn, "[server] Nick definido: %s (antes: %s)" % (newnick, old))

            elif text.startswith("/join "):
                room = text.split(" ", 1)[1].strip()
                if not room:
                    safe_send(conn, "[server] Nome de sala inválido.")
                    continue
                with clients_lock:
                    prev = clients[conn]["room"]
                    if prev and conn in rooms.get(prev, set()):
                        rooms[prev].discard(conn)
                        if not rooms[prev]:
                            del rooms[prev]
                        broadcast(prev, "[server] %s saiu da sala." % clients[conn]["nick"])
                    rooms.setdefault(room, set()).add(conn)
                    clients[conn]["room"] = room
                safe_send(conn, "[server] Entrou na sala %s" % room)
                broadcast(room, "[server] %s entrou na sala." % clients[conn]["nick"], exclude_conn=conn)

            elif text == "/quit":
                safe_send(conn, "[server] Até logo!")
                break

            else:
                with clients_lock:
                    room = clients[conn]["room"]
                    nick = clients[conn]["nick"]
                if not room:
                    safe_send(conn, "[server] Entre em uma sala com /join SALA antes de enviar mensagens.")
                else:
                    broadcast(room, "[%s] %s" % (nick, text), exclude_conn=None)

    except Exception:
        traceback.print_exc()
    finally:
        remove_client(conn)

def main():
    print("Iniciando servidor chat em %s:%d ..." % (HOST, PORT))
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen(5)
    try:
        while True:
            conn, addr = s.accept()
            print("Conexão de", addr)
            t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            t.start()
    except KeyboardInterrupt:
        print("Servidor encerrando...")
    finally:
        s.close()

if __name__ == "__main__":
    main()
