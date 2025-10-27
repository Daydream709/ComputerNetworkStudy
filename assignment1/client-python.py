import sys
import socket

SEND_BUFFER_SIZE = 2048


def client(server_ip, server_port):
    """Open socket and send message from sys.stdin"""
    # 创建TCP套接字
    sockfd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # 连接到服务器
        server_address = (server_ip, server_port)
        sockfd.connect(server_address)

        # 从标准输入读取二进制数据并发送到服务器
        while True:
            data = sys.stdin.buffer.read(SEND_BUFFER_SIZE)
            if not data:
                break

            # 发送数据到服务器
            # 替换现有的发送逻辑
            while data:
                bytes_sent = sockfd.send(data)
                if bytes_sent < len(data):
                    # 如果只发送了部分数据，保存剩余数据并继续发送
                    data = data[bytes_sent:]
                else:
                    # 全部发送成功，跳出循环
                    break

    except Exception as e:
        print("Client error: " + str(e), file=sys.stderr)
        return 1

    finally:
        # 关闭套接字
        sockfd.close()

    return 0


def main():
    """Parse command-line arguments and call client function"""
    if len(sys.argv) != 3:
        sys.exit("Usage: python client-python.py [Server IP] [Server Port] < [message]")
    server_ip = sys.argv[1]
    server_port = int(sys.argv[2])
    client(server_ip, server_port)


if __name__ == "__main__":
    main()
