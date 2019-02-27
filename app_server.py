import sys
import selectors
import struct
import traceback
import socket
import libserver

sel = selectors.DefaultSelector()


def accept_wrapper(sock):
    conn, addr = sock.accept()
    print("accepted connection from", addr)
    conn.setblocking(False)
    message = libserver.Message(sel, conn, addr)
    sel.register(conn, selectors.EVENT_READ, data=message)


def main():
    host = "127.0.0.1"
    port= 65533
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host,port))
    sock.listen()
    print("listening on",(host,port))
    sock.setblocking(False)
    sel.register(sock, selectors.EVENT_READ, data=None)

    try:
        while True:
            events = sel.select(timeout=None)
            for key, mask in events:
                if key.data is None:
                    accept_wrapper(key.fileobj)
                else:
                    message = key.data
                    try:
                        message.process_events(mask)
                    except Exception:
                        print("main: error: exception for:",
                            f"{message.addr}: \n{traceback.format_exc()}")
                        message.close()
    except KeyboardInterrupt:
        print("exiting")
    finally:
        sel.close()
if __name__ == '__main__':
    main()
