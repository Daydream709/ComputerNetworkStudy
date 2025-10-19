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
            # 直接读取二进制数据而不是文本
            data = sys.stdin.buffer.read(SEND_BUFFER_SIZE)
            if not data:
                break

            # 发送数据到服务器
            bytes_sent = sockfd.send(data)

            # 检查是否完整发送了数据
            if bytes_sent != len(data):
                print(
                    "Partial send: sent " + str(bytes_sent) + " of " + str(len(data)) + " bytes",
                    file=sys.stderr,
                )
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
