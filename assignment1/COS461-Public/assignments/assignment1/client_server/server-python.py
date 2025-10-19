###############################################################################
# server-python.py
# Name:
# NetId:
###############################################################################

import sys
import socket

RECV_BUFFER_SIZE = 2048
QUEUE_LENGTH = 10


def server(server_port):
    """Listen on socket and print received message to sys.stdout"""
    # 创建TCP套接字
    sockfd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # 设置套接字选项，允许地址重用
        sockfd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # 绑定地址和端口
        server_address = ("", server_port)
        sockfd.bind(server_address)

        # 开始监听连接
        sockfd.listen(QUEUE_LENGTH)
        print(f"Server listening on port {server_port}")

        while True:
            # 接受客户端连接
            client_fd, client_addr = sockfd.accept()
            print(f"Client connected: {client_addr[0]}:{client_addr[1]}")

            try:
                # 接收并处理客户端消息
                while True:
                    data = client_fd.recv(RECV_BUFFER_SIZE)
                    if not data:
                        break

                    # 输出到标准输出
                    sys.stdout.write(data.decode("utf-8"))
                    sys.stdout.flush()

            except Exception as e:
                print(f"Error receiving data: {e}")

            finally:
                # 关闭客户端连接
                client_fd.close()

    except KeyboardInterrupt:
        print("\nServer shutting down...")

    except Exception as e:
        print(f"Server error: {e}")

    finally:
        # 关闭服务器套接字
        sockfd.close()


def main():
    """Parse command-line argument and call server function"""
    if len(sys.argv) != 2:
        sys.exit("Usage: python server-python.py [Server Port]")
    server_port = int(sys.argv[1])
    server(server_port)


if __name__ == "__main__":
    main()
