from socket import *


def start():
    serverPort = 4000
    serverSocket = socket(AF_INET, SOCK_STREAM)
    ip = gethostbyname(gethostname())
    serverSocket.bind((ip, serverPort))  # bind the socket with the server
    serverSocket.listen(1)  # listening to only one request
    while True:
        print(ip)
        print("running on port: 4000")
        print("server running")
        connectionSocket, addr = serverSocket.accept()  # set up a new connection
        request = connectionSocket.recv(4096)

        try:
            filename = request.split()[1]
            file = open(filename[1:])  # open the file name from the request if it exist
            response = file.read()  # read from the file
            connectionSocket.sendto("HTTP/1.1 200 OK\r\n\r\n".encode(), addr)  # send the http header to the client addr
            connectionSocket.sendto(response.encode(), addr)  # send the response
            print(response)  # printing what is being send from the file
            connectionSocket.close()

        except IOError:
            connectionSocket.send("HTTP/1.1 404 Not Found\r\n\r\n".encode())  # send http response header
            #  send 404 not found in html
            connectionSocket.send("<html><head></head><body><h1>404 Not Found</h1></body></html>\r\n".encode())
            print("404 Not Found")
            connectionSocket.close()
        print("\r\n")


def main():
    start()


if __name__ == '__main__':
    main()
