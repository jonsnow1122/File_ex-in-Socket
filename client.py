import os
import socket
import threading
import pickle
import tkinter as tk
import time
from tkinter import filedialog


# 创建一个socket对象
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
flag = True
BUFFER_SIZE = 1024  # 缓冲区大小
# 连接到服务器的IP地址和端口号
client.connect(("127.0.0.1", 8888))

# 创建一个图形用户界面
window = tk.Tk()
window.title("Chat Room")

# 创建一个文本框，显示聊天消息
text = tk.Text(window)
text.pack()

# 创建一个输入框，输入聊天消息
entry = tk.Entry(window)
entry.pack()

# 创建一个函数，发送聊天消息
def send_message():
    if flag:
        # 获取输入框的内容，并清空输入框
        message = entry.get()

        # 判断消息是否以/开头，表示特殊指令
        if message.startswith("/"):
            # 判断是否是下载指令，格式为/download 文件名
            if message.startswith("/download "):
                # 获取要下载的文件名
                filename = message.split()[1]

                # 向服务器发送下载请求，包含自己的IP地址和文件名，使用pickle模块序列化
                client.send(pickle.dumps([client.getsockname(), filename]))
            else:
                # 如果是其他指令，就在文本框中显示无效指令的消息
                text.insert(tk.END, "Invalid command.\n")
        else:
            # 如果是普通的聊天消息，就直接发送给服务器，使用pickle模块序列化
            client.send(pickle.dumps(message))
            text.insert(tk.END, ":" + message + "\n")
    entry.delete(0, tk.END)

# 创建一个按钮，点击时调用send_message函数
button = tk.Button(window, text="Send", command=send_message)
button.pack()

# 创建一个函数，选择要发送的文件
def choose_file():
    if flag:
        # 弹出一个文件选择器，获取选择的文件路径
        filepath = filedialog.askopenfilename()

        # 判断是否选择了文件
        if filepath:
            # 获取文件名和文件内容
            filename = filepath.split("/")[-1]
            filesize = os.path.getsize(filepath)
            message = (filename, filesize)
            client.send(pickle.dumps(message))
            print(123)

            with open(filepath, 'rb') as f:
                while True:
                    data = f.read(BUFFER_SIZE)
                    if not data:
                        break
                    client.send(data)

            listbox.insert(tk.END, filename)

# 创建一个列表框，显示已发送的文件列表
listbox = tk.Listbox(window)
listbox.pack()

# 创建一个按钮，点击时调用choose_file函数
button = tk.Button(window, text="Choose File", command=choose_file)
button.pack()



# 创建一个函数，下载选中的文件
def download_file():
    if flag:
        # 获取列表框中选中的文件名
        filename = listbox.get(tk.ACTIVE)

        # 向服务器发送下载请求，包含自己的IP地址和文件名，使用pickle模块序列化
        client.send(pickle.dumps([client.getsockname(), filename]))

# 创建一个按钮，点击时调用download_file函数
button = tk.Button(window, text="Download File", command=download_file)
button.pack()

# 定义一个函数，接收服务器的消息
def receive_message():
    # 循环接收服务器的消息，使用pickle模块反序列化
    while True:
        message = pickle.loads(client.recv(1024))

        # 判断消息的类型
        #if not message:
        #    continue
        if isinstance(message, str):
            # 如果是字符串，就是普通的聊天消息，直接在文本框中显示
            text.insert(tk.END, message + "\n")
            if message.split()[0] == "Login" and message.split()[1] == "failed.":
                flag = False
                break
        elif isinstance(message, dict):
            # 如果是字典，就是已发送的文件列表，循环遍历并添加到列表框中
            for filename in message:
                listbox.insert(tk.END, filename)
        elif isinstance(message, bytes):
            # 如果是字节串，就是文件对象，包含文件内容
            filecontent = message

            # 弹出一个文件保存器，获取要保存的文件路径
            filepath = filedialog.asksaveasfilename()

            # 判断是否选择了文件路径
            if filepath:
                # 将文件内容保存到本地，并在文本框中显示文件名
                with open(filepath, "wb") as f:
                    f.write(filecontent)
                text.insert(tk.END, f"File {filepath.split('/')[-1]} saved.\n")
        

# 创建一个线程，执行receive_message函数
thread = threading.Thread(target=receive_message)

# 启动线程
thread.start()

# 进入图形用户界面的主循环
window.mainloop()