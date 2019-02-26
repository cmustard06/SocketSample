import socket
import selectors
import types




def accept_wrapper(sock):
	conn, addr = sock.accept()
	print("accepted connection from", addr)
	conn.setblocking(False) # 立即让socket进入非阻塞模式，否则其他连接就会处于等待状态
	data = types.SimpleNamespace(addr=addr,intb=b"", outb=b"") # 创建了一个简单的对象用来保存我们想要的 socket 和数据
	# 由于我们得知道客户端连接   什么时候可以写入或者读取，下面两个事件都会被用到
	events = selectors.EVENT_READ | selectors.EVENT_WRITE
	# 事件掩码、socket 和数据对象都会被传入，这里用于监测当前连接状态
	select.register(conn, events, data=data)

def service_connection(key, mask):
	# key 就是从调用 select() 方法返回的一个具名元组，它包含了 socket 对象「fileobj」和数据对象。mask 包含了就绪的事件
	conn = key.fileobj
	data = key.data
	if mask & selectors.EVENT_READ:   # 与运算，判断是否为读事件, socket 就绪而且可以被读取，mask & selectors.EVENT_READ 就为真
		recv_data = conn.recv(1024)
		if recv_data:
			data.outb += recv_data  # 所有读取到的数据都会被追加到 data.outb 里面(这里也可以做其他处理)。随后被发送出去
		else: # 如果recv_data为空，代表客户端关闭了他的连接，此时服务器端也应该关闭该链接
			print("closing connection to ", data.addr)
			# 调用unregister() 来撤销 select() 的监控
			select.unregister(conn)
			conn.close()

	if mask & selectors.EVENT_WRITE:
		if data.outb:
			print("echoing ",repr(data.outb),"to",data.addr)
			sent = conn.sendall(data.outb)
			data.outb = b""

select = selectors.DefaultSelector()

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind(("127.0.0.1",65533))
sock.listen()
print("listen on ")
sock.setblocking(False)  # 配置 socket 为非阻塞模式,这个 socket 的调用将不在是阻塞的

#为你感兴趣的事件注册 socket 监控，对于监听 socket，作为服务端我们需要监听 selectors.EVENT_READ 这个读事件
# data 用来存储任何你 socket 中想存的数据，当 select() 返回的时候它也会返回。我们将使用 data 来跟踪 socket 上发送或者接收的东西
select.register(sock,selectors.EVENT_READ, data=None) 

# 事件循环
while True:
	# 调用select.select会阻塞当前进程直到 socket I/O 就绪(有新连接到)。它返回一个 (key, events) 元组，
	# 每个 socket 都有一个。key 就是一个包含 fileobj 属性的具名元组。
	# key.fileobj 是一个 socket 对象，mask 表示一个操作就绪的事件掩码
	events = select.select(timeout=2)
	# 如果 key.data 为空，说明有新的连接到来，我们需要调用 accept() 方法来授受连接请求
	# 如果不为空，说明该连接已被接受，正在等待下一步处理
	for key, mask in events:
		if key.data is None:
			accept_wrapper(key.fileobj)
		else:
			service_connection(key,mask)


