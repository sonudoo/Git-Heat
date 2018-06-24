from diffiehellman.diffiehellman import DiffieHellman
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import socket, json, _thread, sys


def receiveData(s, length):
	data = b''
	ldata = 0
	while ldata < length:
		receivedData = s.recv(1024)
		ldata += len(receivedData)
		data += receivedData
	return data

def padInteger(i, length):
	i = str(i)
	i = i[::-1]
	j = len(i)
	while j < length:
		i += '0'
		j += 1

	return i[::-1]


progress = 0

def showProgress():
	global progress
	while progress < fileSize:
		pc = (progress*100)//fileSize
		i = 0
		print("\r"+"[", end='')
		while i < (pc//2):
			print("\u2588", end='')
			i += 1
		while i < 50:
			print(" ", end='')
			i += 1
		print("] ", end='')
		print(str(pc), end='')
		print("% Complete", end='')
	i = 0
	print("\r"+"[", end='')
	while i < 50:
		print("\u2588", end='')
		i += 1
	print("] ", end='')
	print("100% Complete", end='')


dh = DiffieHellman()
dh.generate_public_key()
publicKey = dh.public_key
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)

ip = input("Enter the IP address of the server: ")

try:
	s.connect((ip, 23548))
except Exception as e:
	print("Connections Failed.")
	exit(0)

data = receiveData(s, 2479)

messageType = data.decode('utf-8', errors='ignore').split('\n')[0]

if messageType != 'KEY_EXCHANGE':
	print("The server sent an illegal response. Closing connection..")
	s.close()
	exit(0)

serverPublicKey = int(data.decode('utf-8', errors='ignore').split('\n')[1])

s.sendall(('KEY_EXCHANGE\n' + str(publicKey)).encode('utf-8', errors='ignore'))

sharedKey = ''
try:
	dh.generate_shared_secret(serverPublicKey)
	sharedKey = bytes.fromhex(dh.shared_key)
except Exception as e:
	print("The server sent an illegal response. Closing connection..")
	s.close()
	exit(0)

print('Key exchange successful: ' + dh.shared_key)


print('Generating Ciphers..')

cipher = AES.new(sharedKey, AES.MODE_CBC, 'jdirlfhixhtkwlif'.encode('utf-8'))

print('Waiting for file list..')

data = receiveData(s, 29).decode('utf-8', errors='ignore').split('\n');

if(data[0] != 'FILELIST'):
	print("The server sent an illegal response. Closing connection..")
	s.close()
	exit(0)

fileListSize = int(data[1])

s.send("READY".encode('utf-8', errors='ignore'))


encryptedFileList = receiveData(s, fileListSize)

print('File list received successful..')
	
print('Sending Acknowledgement..')

s.send("ACK".encode('utf-8', errors='ignore'))

fileList = unpad(cipher.decrypt(encryptedFileList), AES.block_size)
sharedFiles = fileList.decode('utf-8').split('\n')

print("Listing..")

print("\nChoose a file to Download: ")
j = 0
for i in sharedFiles:
	print(str(j+1)+'. '+i)
	j += 1

x = ''
while True:
	x = int(input())
	if x<1 or x>len(sharedFiles):
		print('Invalid choice.. Try again..')
	else:
		break

s.send(("REQUEST\n"+padInteger(x-1, 20)).encode('utf-8', errors='ignore'))

print('The file has been requested. Waiting for the server to send back headers..')

data = receiveData(s, 25).decode('utf8', errors='ignore').split('\n')

if(data[0] != 'FILE'):
	print("The server sent an illegal response. Closing connection..")
	s.close()
	exit(0)

fileName = sharedFiles[x-1].split('/')[len(sharedFiles[x-1].split('/'))-1]
fileSize = int(data[1])
encryptedFileData = b''

print(fileSize)
s.send("READY".encode('utf-8', errors='ignore'))

print('Your file is being downloaded..\n0% Complete', end='')


file = open(fileName, 'wb')

_thread.start_new_thread(showProgress,())
while progress < fileSize:
	receivedData = s.recv(1024)
	file.write(receivedData)
	progress += len(receivedData)
file.close()

print('\n\nFile download complete..')
file = open(fileName, 'rb')
encryptedData = file.read()
file.close()

print('Decrypting File..')
file = open(fileName, 'wb')
try:
	cipher = AES.new(sharedKey, AES.MODE_CBC, 'jdirlfhixhtkwlif'.encode('utf-8'))
	decryptedData = unpad(cipher.decrypt(encryptedData), AES.block_size)
	file.write(decryptedData)
	file.close()
	s.send("ACK".encode('utf-8', errors='ignore'))
	print('Your file has been saved successfully in the current working directory..')
except Exception as e:
	print('File decryption error occured. Please re-download the file')
	s.send("FAILED".encode('utf-8', errors='ignore'))
s.close()
