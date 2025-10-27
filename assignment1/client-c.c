/*****************************************************************************
 * client-c.c
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
#include <errno.h>

#define SEND_BUFFER_SIZE 2048

/* TODO: client()
 * Open socket and send message from stdin.
 * Return 0 on success, non-zero on failure
 */
int client(char *server_ip, char *server_port)
{
  int sockfd;
  struct sockaddr_in server_addr;
  char buffer[SEND_BUFFER_SIZE];
  ssize_t bytes_read;

  // 创建socket
  sockfd = socket(AF_INET, SOCK_STREAM, 0);
  if (sockfd < 0)
  {
    perror("socket");
    return 1;
  }

  // 配置服务器地址信息
  memset(&server_addr, 0, sizeof(server_addr));
  server_addr.sin_family = AF_INET;
  server_addr.sin_port = htons(atoi(server_port));

  // 将点分十进制IP地址转换为二进制格式
  if (inet_pton(AF_INET, server_ip, &server_addr.sin_addr) <= 0)
  {
    fprintf(stderr, "Invalid address/ Address not supported\n");
    close(sockfd);
    return 1;
  }

  // 连接到服务器
  if (connect(sockfd, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0)
  {
    perror("connect");
    close(sockfd);
    return 1;
  }

  // 从标准输入读取数据并发送到服务器
  while ((bytes_read = read(STDIN_FILENO, buffer, SEND_BUFFER_SIZE)) > 0)
  {
    ssize_t total_bytes_sent = 0;

    // 循环发送直到所有数据都被发送出去
    while (total_bytes_sent < bytes_read)
    {
      ssize_t bytes_sent = send(sockfd, buffer + total_bytes_sent,
                                bytes_read - total_bytes_sent, 0);

      if (bytes_sent < 0)
      {
        perror("send");
        close(sockfd);
        return 1;
      }

      total_bytes_sent += bytes_sent;
    }
  }

  // 检查读取是否出错
  if (bytes_read < 0)
  {
    perror("read");
    close(sockfd);
    return 1;
  }

  // 关闭套接字
  close(sockfd);
  return 0;
}

/*
 * main()
 * Parse command-line arguments and call client function
 */
int main(int argc, char **argv)
{
  char *server_ip;
  char *server_port;

  if (argc != 3)
  {
    fprintf(stderr, "Usage: ./client-c [server IP] [server port] < [message]\n");
    exit(EXIT_FAILURE);
  }

  server_ip = argv[1];
  server_port = argv[2];
  return client(server_ip, server_port);
}