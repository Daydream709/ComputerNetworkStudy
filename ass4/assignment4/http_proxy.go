/*****************************************************************************
 * http_proxy.go
 * Names:
 * NetIds:
 *****************************************************************************/

package main

import (
	"bufio"
	"fmt"
	"io"
	"net"
	"net/http"
	"os"
)

func main() {
	if len(os.Args) != 2 {
		fmt.Println("Usage: ./http_proxy <port>")
		os.Exit(1)
	}

	port := os.Args[1]
	listener, err := net.Listen("tcp", ":"+port)
	if err != nil {
		fmt.Printf("Failed to listen on port %s: %v\n", port, err)
		os.Exit(1)
	}
	defer listener.Close()

	fmt.Printf("Proxy server listening on port %s\n", port)

	for {
		clientConn, err := listener.Accept()
		if err != nil {
			fmt.Printf("Failed to accept connection: %v\n", err)
			continue
		}
		
		go handleClient(clientConn)
	}
}

func handleClient(clientConn net.Conn) {
	defer clientConn.Close()

	// 读取客户端请求
	request, err := http.ReadRequest(bufio.NewReader(clientConn))
	if err != nil {
		sendErrorResponse(clientConn, http.StatusInternalServerError)
		return
	}

	// 只处理GET请求
	if request.Method != "GET" {
		sendErrorResponse(clientConn, http.StatusInternalServerError)
		return
	}

	// 解析目标地址
	host := request.URL.Host
	if host == "" {
		host = request.Host
	}
	
	// 如果URL是绝对路径，转换为相对路径
	if request.URL.Scheme != "" {
		// 将URL转换为相对路径
		request.URL.Scheme = ""
		request.URL.Host = ""
	}

	// 设置Host头
	request.Header.Set("Host", host)
	
	// 设置Connection头为close
	request.Header.Set("Connection", "close")

	// 连接到目标服务器
	serverConn, err := net.Dial("tcp", host+":80")
	if err != nil {
		// 如果80端口连接失败，尝试HTTPS端口443
		serverConn, err = net.Dial("tcp", host+":443")
		if err != nil {
			sendErrorResponse(clientConn, http.StatusInternalServerError)
			return
		}
	}
	defer serverConn.Close()

	// 发送请求到目标服务器
	err = request.Write(serverConn)
	if err != nil {
		sendErrorResponse(clientConn, http.StatusInternalServerError)
		return
	}

	// 将服务器响应转发给客户端
	_, err = io.Copy(clientConn, serverConn)
	if err != nil {
		return
	}
}

func sendErrorResponse(conn net.Conn, statusCode int) {
	response := fmt.Sprintf("HTTP/1.1 %d %s\r\n"+
		"Content-Type: text/plain\r\n"+
		"Connection: close\r\n"+
		"\r\n"+
		"Internal Error\n",
		statusCode, http.StatusText(statusCode))
	conn.Write([]byte(response))
}