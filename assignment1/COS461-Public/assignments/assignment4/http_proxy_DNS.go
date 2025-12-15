/*****************************************************************************
 * http_proxy_DNS.go
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
	"net/url"
	"os"
	"strings"
	"sync/atomic"
	"time"

	"golang.org/x/net/html"
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
		fmt.Println("Usage: ./http_proxy_DNS <port>")
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

	// 从服务器读取响应
	resp, err := http.ReadResponse(bufio.NewReader(serverConn), reqToServer)
	if err != nil {
		sendErrorResponse(clientConn, http.StatusBadGateway)
		return
	}
	defer resp.Body.Close()

	// 检查是否为HTML内容，如果是，则启动DNS预取
	contentType := resp.Header.Get("Content-Type")
	if strings.Contains(contentType, "text/html") {
		// 创建管道用于复制响应内容
		pr, pw := io.Pipe()

		// 在另一个goroutine中进行DNS预取
		go func() {
			defer pw.Close()
			parseAndPrefetchDNS(pr)
		}()

		// 先将响应头写入客户端
		clientConn.SetWriteDeadline(time.Now().Add(writeTimeout))
		resp.Write(clientConn)

		// 创建一个多写入器，同时写入客户端连接和管道
		multiWriter := io.MultiWriter(clientConn, pw)

		// 然后复制响应体到客户端和DNS预取函数
		_, copyErr := io.Copy(multiWriter, resp.Body)
		pw.Close() // 关闭管道写入端

		if copyErr != nil && !isNetClosedError(copyErr) {
			return
		}
	} else {
		// 非HTML内容，直接转发响应
		clientConn.SetWriteDeadline(time.Now().Add(writeTimeout))
		_, err = io.Copy(clientConn, resp.Body)
		if err != nil && !isNetClosedError(err) {
			return
		}
	}
}

// parseAndPrefetchDNS 解析HTML并预取DNS
func parseAndPrefetchDNS(reader io.Reader) {
	doc, err := html.Parse(reader)
	if err != nil {
		return
	}

	// 提取所有链接并进行DNS预取
	links := extractLinks(doc)
	for _, link := range links {
		if strings.HasPrefix(link, "http") {
			// 解析URL以获取主机名
			urlObj, err := url.Parse(link)
			if err != nil {
				continue
			}

			// 异步执行DNS查找
			if urlObj.Host != "" {
				go func(host string) {
					net.LookupHost(host)
				}(urlObj.Host)
			}
		}
	}
}

// extractLinks 从HTML文档中提取所有链接
func extractLinks(n *html.Node) []string {
	var links []string

	// 递归遍历节点
	if n.Type == html.ElementNode && n.Data == "a" {
		for _, attr := range n.Attr {
			if attr.Key == "href" {
				links = append(links, attr.Val)
				break
			}
		}
	}

	// 递归处理子节点
	for c := n.FirstChild; c != nil; c = c.NextSibling {
		links = append(links, extractLinks(c)...)
	}

	return links
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
