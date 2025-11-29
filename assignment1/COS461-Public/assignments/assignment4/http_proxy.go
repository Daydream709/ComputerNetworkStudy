/*****************************************************************************
 * http_proxy.go
 * Names: Your Name
 * NetIds: Your NetId
 *****************************************************************************/

package main

import (
	"bufio"
	"fmt"
	"io"
	"net"
	"net/http"
	"os"
	"strings"
	"sync/atomic"
	"time"
)

const (
	// 超时设置
	readTimeout  = 60 * time.Second
	writeTimeout = 60 * time.Second
	dialTimeout  = 30 * time.Second
	
	// 限制最大并发连接数
	maxConcurrentConnections = 100
)

var (
	currentConnections int32
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
		
		// 限制并发连接数
		if atomic.LoadInt32(&currentConnections) >= maxConcurrentConnections {
			sendErrorResponse(clientConn, http.StatusServiceUnavailable)
			clientConn.Close()
			continue
		}

		go handleClient(clientConn)
	}
}

func handleClient(clientConn net.Conn) {
	atomic.AddInt32(&currentConnections, 1)
	defer atomic.AddInt32(&currentConnections, -1)
	defer clientConn.Close()

	// 设置读取超时
	clientConn.SetReadDeadline(time.Now().Add(readTimeout))

	// 读取客户端请求
	reader := bufio.NewReader(clientConn)
	request, err := http.ReadRequest(reader)
	if err != nil {
		sendErrorResponse(clientConn, http.StatusBadRequest)
		return
	}
	defer request.Body.Close()

	// 只处理GET请求
	if request.Method != "GET" {
		sendErrorResponse(clientConn, http.StatusMethodNotAllowed)
		return
	}

	// 解析目标地址
	host := request.Host
	if host == "" {
		// 如果请求是绝对URI形式 (http://example.com/path)
		if request.URL.Host != "" {
			host = request.URL.Host
		} else {
			sendErrorResponse(clientConn, http.StatusBadRequest)
			return
		}
	}

	// 确保端口号存在
	if !strings.Contains(host, ":") {
		host += ":80"
	}

	// 连接到目标服务器
	serverConn, err := net.DialTimeout("tcp", host, dialTimeout)
	if err != nil {
		sendErrorResponse(clientConn, http.StatusBadGateway)
		return
	}
	defer serverConn.Close()

	// 构建发送到后端服务器的请求
	var reqToServer *http.Request

	// 如果请求URL中已包含主机信息（绝对URI形式），则直接使用
	if request.URL.Host != "" {
		reqToServer = request
	} else {
		// 否则构建一个绝对URI请求
		absoluteURL := fmt.Sprintf("http://%s%s", host, request.URL.RequestURI())
		reqToServer, err = http.NewRequest(request.Method, absoluteURL, nil)
		if err != nil {
			sendErrorResponse(clientConn, http.StatusBadRequest)
			return
		}

		// 手动复制头部（兼容旧版本Go）
		reqToServer.Header = make(http.Header)
		for key, values := range request.Header {
			for _, value := range values {
				reqToServer.Header.Add(key, value)
			}
		}
	}

	// 删除代理相关的头部
	reqToServer.Header.Del("Proxy-Connection")

	// 设置Connection头为close
	reqToServer.Header.Set("Connection", "close")

	// 设置写入超时并发送请求到目标服务器
	serverConn.SetWriteDeadline(time.Now().Add(writeTimeout))
	err = reqToServer.Write(serverConn)
	if err != nil {
		sendErrorResponse(clientConn, http.StatusBadGateway)
		return
	}

	// 设置读取超时
	serverConn.SetReadDeadline(time.Now().Add(readTimeout))

	// 将服务器响应转发给客户端
	// 使用带缓冲的复制并设置适当的超时
	clientConn.SetWriteDeadline(time.Now().Add(writeTimeout))
	
	// 创建带缓冲的reader以提高效率
	bufReader := bufio.NewReader(serverConn)
	_, err = io.Copy(clientConn, bufReader)
	if err != nil {
		// 忽略连接相关的错误，这在网络编程中很常见
		if !isNetClosedError(err) {
			// 不打印日志，按照要求移除调试信息
		}
		return
	}
}

// 检查是否是网络连接关闭错误
func isNetClosedError(err error) bool {
	if err == nil {
		return false
	}
	
	// 检查是否为超时错误
	if netErr, ok := err.(net.Error); ok && netErr.Timeout() {
		return true
	}
	
	errStr := err.Error()
	return strings.Contains(errStr, "connection closed") || 
		   strings.Contains(errStr, "broken pipe") || 
		   strings.Contains(errStr, "connection reset") ||
		   strings.Contains(errStr, "i/o timeout")
}

func sendErrorResponse(conn net.Conn, statusCode int) {
	statusText := http.StatusText(statusCode)
	if statusText == "" {
		statusText = "Status " + fmt.Sprintf("%d", statusCode)
	}

	response := fmt.Sprintf("HTTP/1.1 %d %s\r\n"+
		"Content-Type: text/plain\r\n"+
		"Content-Length: %d\r\n"+
		"Connection: close\r\n"+
		"\r\n"+
		"%s\n",
		statusCode, statusText, len(statusText)+1, statusText)

	// 设置写入超时
	conn.SetWriteDeadline(time.Now().Add(writeTimeout))
	conn.Write([]byte(response))
}