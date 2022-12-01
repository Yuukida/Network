import os
from socket import*

serverPort = 8888
#create TCP welcome socket
serverSocket = socket(AF_INET, SOCK_STREAM)
ipAddress = gethostbyname(gethostname())
serverSocket.bind((ipAddress, serverPort))
#server begins listening for incoming TCP requests
serverSocket.listen(1)
print('The server is ready to receive...')
#server waits for acception for incoming requests, new socket created on return 
#make a connection
print(f"{ipAddress} is running on port: {serverPort}. Paste address : {ipAddress}:{serverPort}/")
connectionSocket, addr = serverSocket.accept()
hostname = ''
while True:
    msg_ls = []
    try:
        connectionSocket.settimeout(3)
        while True:
            message = connectionSocket.recv(8192).decode()
            if len(message) == 0:
                break
            msg_ls.append(message)
    except timeout:
        if not msg_ls:
            continue
        
        hostname = ''
        for message in msg_ls:
            if not hostname:
                filename = message.split()[1]
                filename = filename.replace('http://', '').replace('https://', '')
                filename = filename.removeprefix('/').removesuffix('/')
                if '/' in filename:
                    path = filename.split('/')
                    hostname = path[0]
                    pathname = filename.find(path[1])
                else:
                    hostname = filename
                    pathname = ''
            
            if os.path.exists(filename):
                with open(filename, 'rb') as file: # file = open(filename)
                    message = file.read()

                    if "HTTP/1.1 301 Moved Permanently\r\n".encode() in message:
                        connectionSocket.sendto(message, addr)  # send the 301 directly
                    else:  # else send properly
                        connectionSocket.send("HTTP/1.1 200 OK\r\n".encode())  # send http header
                        connectionSocket.send("Content-Type:text/html\r\n".encode())  # specify context
                        connectionSocket.send(message)  # send line by line
            else:
                requestSocket = socket(AF_INET, SOCK_STREAM)

                try:
                    requestSocket.connect((hostname, 80))
                    requestSocket.send( ("GET /" + pathname + " HTTP/1.1\r\nHost: " + hostname + "\r\n\r\n").encode() )

                    req_msg = requestSocket.recv(8192)
                    with open((filename + ".txt"), 'wb') as cache:
                        while req_msg:
                            connectionSocket.send(req_msg)
                            cache.write(req_msg)
                            req_msg = requestSocket.recv(4096)
                except gaierror:
                    connectionSocket.send("HTTP/1.1 404 Not Found \r\n\r\n".encode())
                    connectionSocket.close()
                    break

