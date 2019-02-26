# 和服务端很相似，不一样的是它没有监听连接请求
#
import socket
import selectors
import types

messages = [b'Message 1 from client.', b'Message 2 from client.']
select = selectors.DefaultSelector()


def start_connections(host, port, num_conns):
    server_addr = (host, port)
    for i in range(0, num_conns):
        connid = i + 1
        print("starting connection", connid, "to", server_addr)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setblocking(False)
        sock.settimeout(3)
        sock.connect_ex(server_addr)  # 由于使用connect() 方法会立即触发一个 BlockingIOError 异常，所以我们使用 connect_ex() 方法取代它
        events = selectors.EVENT_WRITE | selectors.EVENT_READ

        data = types.SimpleNamespace(connid=connid, msg_total=sum(len(m) for m in messages),
                                     recv_total=0,
                                     messages=list(messages),
                                     outb=b"")
        select.register(sock, events, data=data)

    while True:
        events = select.select(timeout=5)
        for key, mask in events:
            service_connection(key, mask)


def service_connection(key, mask):
    conn = key.fileobj
    data = key.data

    if mask & selectors.EVENT_READ:
        recv_data = conn.recv(1024)
        if recv_data:
            print('received', repr(recv_data), 'from connection', data.connid)
            data.recv_total = data.recv_total + len(recv_data)
        if not recv_data or data.recv_total == data.msg_total:
            print('closing connection', data.connid)
            select.unregister(conn)
            conn.close()

    if mask & selectors.EVENT_WRITE:
        if not data.outb and data.messages:
            data.outb = data.messages.pop(0)
        if data.outb:
            print('sending', repr(data.outb), 'to connection', data.connid)
            sent = conn.send(data.outb)  # Should be ready to write
            data.outb = data.outb[sent:]


start_connections("127.0.0.1", 65533, 10)
# def single_connect(host,port):
# 	server_addr = (host, port)
# 	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# 	sock.connect(server_addr)
# 	sock.send(b"Message 1 from client")
# 	data = sock.recv(1024)
# 	print("Recv ", data.decode())
# single_connect("127.0.0.1",65533)
