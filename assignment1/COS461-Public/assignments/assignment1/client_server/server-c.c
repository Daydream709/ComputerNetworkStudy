/*****************************************************************************
 * server-c.c
 * Name:
 * NetId:
 *****************************************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <errno.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <netdb.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <signal.h>
#include <errno.h>

#define QUEUE_LENGTH 10
#define RECV_BUFFER_SIZE 2048

int sockfd; // 全局socket描述符，用于信号处理时关闭

/* TODO: server()
 * Open socket and wait for client to connect
 * Print received message to stdout
 * Return 0 on success, non-zero on failure
 */

void signal_handler(int sig)
{
    if (sockfd >= 0)
    {
        close(sockfd);
    }
    exit(0);
}

int server(char *server_port)
{
    int port = atoi(server_port);
    if (port <= 0)
    {
        fprintf(stderr, "Invalid port number\n");
        return 1;
    }

    // 注册信号处理器
    signal(SIGINT, signal_handler);

    // 创建socket
    sockfd = socket(AF_INET, SOCK_STREAM, 0);
    if (sockfd < 0)
    {
        perror("socket");
        return 1;
    }

    // 设置socket选项，允许地址重用
    int yes = 1;
    if (setsockopt(sockfd, SOL_SOCKET, SO_REUSEADDR, &yes, sizeof(int)) == -1)
    {
        perror("setsockopt");
        close(sockfd);
        return 1;
    }

    // 配置服务器地址信息
    struct sockaddr_in server_addr;
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = INADDR_ANY; // 监听所有接口
    server_addr.sin_port = htons(port);       // 端口号转换为网络字节序

    // 绑定地址和端口
    if (bind(sockfd, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0)
    {
        perror("bind");
        close(sockfd);
        return 1;
    }

    // 开始监听连接
    if (listen(sockfd, QUEUE_LENGTH) < 0)
    {
        perror("listen");
        close(sockfd);
        return 1;
    }

    printf("Server listening on port %d\n", port);

    // 循环接受客户端连接
    while (1)
    {
        struct sockaddr_in client_addr;
        socklen_t client_len = sizeof(client_addr);

        // 接受客户端连接
        int client_fd = accept(sockfd, (struct sockaddr *)&client_addr, &client_len);
        if (client_fd < 0)
        {
            perror("accept");
            continue; // 继续处理下一个连接请求
        }

        // 获取客户端信息
        char client_ip[INET_ADDRSTRLEN];
        inet_ntop(AF_INET, &(client_addr.sin_addr), client_ip, INET_ADDRSTRLEN);
        printf("Client connected: %s:%d\n", client_ip, ntohs(client_addr.sin_port));

        // 接收并处理客户端消息
        char buffer[RECV_BUFFER_SIZE];
        ssize_t bytes_received;

        while ((bytes_received = recv(client_fd, buffer, RECV_BUFFER_SIZE - 1, 0)) > 0)
        {
            buffer[bytes_received] = '\0'; // 确保字符串结束
            printf("%s", buffer);          // 输出到标准输出
            fflush(stdout);
        }

        // 处理接收错误
        if (bytes_received < 0)
        {
            perror("recv");
        }

        // 关闭客户端连接
        close(client_fd);
    }

    // 正常不会执行到这里
    close(sockfd);
    return 0;
}

/*
 * main():
 * Parse command-line arguments and call server function
 */
int main(int argc, char **argv)
{
    char *server_port;

    if (argc != 2)
    {
        fprintf(stderr, "Usage: ./server-c [server port]\n");
        exit(EXIT_FAILURE);
    }

    server_port = argv[1];
    return server(server_port);
}