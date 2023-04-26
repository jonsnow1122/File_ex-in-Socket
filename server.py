import socket
import threading
import pickle
import time

# 创建一个socket对象
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
BUFFER_SIZE = 1024  # 缓冲区大小
# 绑定IP地址和端口号
server.bind(("127.0.0.1", 8888))

# 监听连接请求
server.listen()

# 定义一个字典，存储用户名和密码
users = {"Alice": "123456", "Bob": "654321", "Charlie": "111111", "1": "1"}

# 定义一个列表，存储已连接的客户端
clients = []

# 定义一个字典，存储已连接用户
cliname = {}

# 定义一个字典，存储已发送的文件对象
files = {}


def receive_file(client):
    # 接收文件大小字符串，并转换成整数
    filesize_str = client.recv(10).decode()
    filesize = int(filesize_str)

    # 用一个变量记录已接收的字节数
    received = 0

    # 创建一个空的字节对象，用于存储文件内容
    filecontent = b""

    # 在一个循环中不断地接收文件内容，直到接收完毕
    while received < filesize:
        # 每次接收4096个字节
        chunk = client.recv(4096)

        # 将数据块追加到文件内容中
        filecontent += chunk

        # 更新已接收的字节数
        received += len(chunk)

    # 返回文件内容
    return filecontent


# 定义一个函数，处理每个客户端的消息
def handle_client(client):
    # 获取客户端的地址
    address = client.getpeername()
    print(f"New connection from {address}")

    # 向客户端发送欢迎消息
    client.send(pickle.dumps("Welcome to the chat room. Please enter your username and password."))

    # 接收客户端的用户名和密码
    try:
        username = pickle.loads(client.recv(1024))
        password = pickle.loads(client.recv(1024))
    except:
        print(f"{address} has disconnected")
        return

    # 验证用户名和密码是否正确
    if username in users and users[username] == password:

        #验证用户是否已经登陆
        if username in cliname.keys():
            client.send(pickle.dumps(f"Login failed. {username} has logged."))
        else:
            # 如果正确，向客户端发送登录成功消息，并广播给其他客户端
            client.send(pickle.dumps(f"Login successful. Hello, {username}!"))
            broadcast(f"{username} has joined the chat room.", client)

            # 将客户端添加到列表中
            clients.append(client)
            cliname[username] = client.getpeername()

            # 向客户端发送已发送的文件列表
            client.send(pickle.dumps(files))

            # 循环接收客户端的消息
            while True:
            #try:
                # 接收客户端的消息，使用pickle模块反序列化
                while True:
                    message = pickle.loads(client.recv(1024))

                # 判断消息的类型
                if isinstance(message, str):
                    if message.startswith("@"):
                        ater = message.split()[0][1:]
                        if ater in cliname.keys():
                            send_message(f"{username}: {message}", cliname[ater])
                        else:
                            client.send(pickle.dumps(f"user {ater} not found!"))
                    else:
                        # 如果是一般字符串，就是普通的聊天消息，直接广播给其他客户端
                        broadcast(f"{username}: {message}", client)
                elif isinstance(message, tuple):
                    # 如果是元组，就是文件对象，包含文件名和文件内容
                    print("123")
                    #message = client.recv(BUFFER_SIZE)
                    filename, filesize = message

                    with open(filename, 'wb') as f:
                        received_size = 0
                        filesize = int(filesize)
                        while received_size < filesize:
                            data = client.recv(BUFFER_SIZE)
                            received_size += len(data)
                            f.write(data)

                    # 广播给其他客户端有新文件可下载
                    broadcast(f"{username} has sent a file: {filename}. You can download it by typing /download {filename}", client)
                elif isinstance(message, list):
                    # 如果是列表，就是下载请求，包含请求者的用户名和要下载的文件名
                    requester, filename = message

                    # 判断文件名是否在字典中
                    if filename in files:
                        # 如果在，就将对应的文件对象发送给请求者
                        send_file(files[filename], requester)
                    else:
                        # 如果不在，就向请求者发送文件不存在的消息
                        send_message(f"File {filename} does not exist.", requester)
                '''
                except:
                    # 如果发生异常，就表示客户端断开连接，从列表中移除，并广播
                    clients.remove(client)
                    broadcast(f"{username} has left the chat room.", client)
                    print(f"{address} has disconnected")
                    break
                '''
    else:
        # 如果不正确，向客户端发送登录失败消息，并断开连接
        client.send(pickle.dumps("Login failed. Wrong username or password."))
        client.close()

# 定义一个函数，向所有其他客户端广播消息
def broadcast(message, sender):
    # 循环遍历客户端列表
    for client in clients:
        if client != sender:
            client.send(pickle.dumps(message))

# 定义一个函数，向指定的客户端发送消息，使用pickle模块序列化
def send_message(message, receiver):
    # 循环遍历客户端列表
    for client in clients:
        # 获取客户端的地址
        address = client.getpeername()
        # 如果地址的第一个元素（IP地址）等于接收者的用户名，就向其发送消息
        if address == receiver:
            client.send(pickle.dumps(message))
            break

# 定义一个函数，向指定的客户端发送文件对象，使用pickle模块序列化
def send_file(filecontent, receiver):
    # 循环遍历客户端列表
    for client in clients:
        # 获取客户端的地址
        address = client.getpeername()
        # 如果地址的第一个元素（IP地址）等于接收者的用户名，就向其发送文件对象
        if address == receiver:
            client.send(pickle.dumps(filecontent))
            break

# 打印服务器启动的消息
print("Server is running...")

# 循环接受连接请求
while True:
    # 接受一个连接请求，并返回一个客户端对象
    client, address = server.accept()
    time.sleep(1)

    # 创建一个线程，执行handle_client函数，传入客户端对象作为参数
    thread = threading.Thread(target=handle_client, args=(client,))

    # 启动线程
    thread.start()