import socket
HOST = "127.0.0.1"
PORT = 5555

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind((HOST, PORT))

s.listen()
print("waiting for a connection...")

conn, addr = s.accept()
print("connected by", addr)

data = conn.recv(1024)
print ("client said:", data.decode())

conn.send("hi back".encode())

conn.close()
s.close()