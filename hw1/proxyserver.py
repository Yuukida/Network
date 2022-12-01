from socket import *


def start():
    serverPort = 4001
    serverSocket = socket(AF_INET, SOCK_STREAM)
    ip = gethostbyname(gethostname())
    serverSocket.bind((ip, serverPort))  # bind the socket with the server
    serverSocket.listen(1)  # listening to only one request
    while True:
        print(ip)
        print("running on port: 4001")
        print("server running")
        connectionSocket, addr = serverSocket.accept()  # set up a new connection
        firstRequest = True
        hostname = b''
        while True:
            try:
                connectionSocket.settimeout(3)
                print("receiving")
                request = connectionSocket.recv(4096)  # receive the request from the client
                if len(request) == 0:  # handle empty request
                    continue
                print(request)
                filename = request.split()[1]
                if "http://".encode() in filename:  # rid of http/https
                    filename = filename[7:]
                elif "https://".encode() in filename:
                    filename = filename[8:]
                filename = filename.removeprefix('/'.encode())  # rid of /
                filename = filename.removesuffix('/'.encode())
                cachename = b""
                if firstRequest:
                    if "/".encode() in filename:
                        directories = filename.split("/".encode())
                        hostname = directories[0]
                        filename = filename[filename.index("/".encode()) + 1:]
                        firstRequest = False
                        line = '.-.-.-.'.encode()
                        cachename = line.join(directories)
                    else:
                        hostname = filename
                        cachename = filename
                else:
                    if filename not in cachename:
                        directories = filename.split("/".encode())
                        line = '.-.-.-.'.encode()
                        cachename = hostname + ".-.-.-.".encode() + line.join(directories)
                chars = ['<'.encode(), '>'.encode(), ':'.encode(), '\"'.encode(), '?'.encode(), '|'.encode(), '\\'.encode()]
                for char in chars:
                    cachename = cachename.replace(char, "".encode())
                try:  # open file
                    file = open((cachename.removeprefix('www.'.encode()) + ".txt".encode()).decode(), 'rb')
                    print("opened cache")
                    response = file.read()  # read from the file, check if file in cache

                    print('read')
                    # if the cached response is a 301
                    if "HTTP/1.1 301 Moved Permanently\r\n".encode() in response:
                        connectionSocket.sendto(response, addr)  # send the 301 directly
                        print(response)
                    else:  # else send properly
                        connectionSocket.send("HTTP/1.1 200 OK\r\n".encode())  # send http header
                        connectionSocket.send("Content-Type:text/html\r\n".encode())  # specify context
                        connectionSocket.send(response)  # send line by line
                        print(response)
                    print("read from cached")
                    firstRequest = False
                    file.close()

                except IOError:
                    print("IOError")
                    requestSocket = socket(AF_INET, SOCK_STREAM)  # create a request socket
                    print("hostname:" + hostname.decode())
                    try:
                        requestSocket.connect((hostname.decode(), 80))  # connect to host
                        print(filename)
                        if firstRequest:
                            header = "GET / HTTP/1.1\r\nHost: " + hostname.decode() + "\r\n\r\n"
                            firstRequest = False
                        else:
                            header = "GET /" + filename.decode() + " HTTP/1.1\r\nHost: " + hostname.decode() + "\r\n\r\n"
                        requestSocket.send(header.encode())  # send get header
                        message = requestSocket.recv(4096)  # receive request
                        cache = None
                        if "client_204".encode() in filename:
                            cache = None
                        else:
                            cache = open((cachename.removeprefix('www.'.encode()) + ".txt".encode()).decode(), 'wb')
                        try:  # getting full response
                            while True:
                                connectionSocket.send(message)  # send message to client
                                requestSocket.settimeout(3)  # timeout waiting for message
                                print(message)
                                if cache is not None:
                                    cache.write(message)
                                message = requestSocket.recv(4096)  # receive request
                                if len(message) == 0:
                                    break

                        except timeout:
                            print('finish receiving and sending')
                            if cache is not None:
                                cache.close()
                            requestSocket.close()  # close request socket

                    except gaierror:
                        connectionSocket.send("HTTP/1.1 404 Not Found\r\n\r\n".encode())  # send http response header
                        #  send 404 not found in html
                        connectionSocket.send(
                            "<html><head></head><body><h1>404 Not Found</h1></body></html>\r\n".encode())
                        requestSocket.close()
                        print("404 Not Found")
            except timeout:
                connectionSocket.close()
                print("\r\n")
                break


def main():
    start()


if __name__ == '__main__':
    main()
