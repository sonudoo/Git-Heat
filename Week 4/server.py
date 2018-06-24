import os, sys, socket, _thread, json
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from diffiehellman.diffiehellman import DiffieHellman


def receiveData(conn, length):
	data = b''
	ldata = 0
	while ldata < length:
		receivedData = conn.recv(1024)
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


def requestHandler(conn, addr):
	dh = DiffieHellman()
	dh.generate_public_key()
	publicKey = dh.public_key

	conn.sendall(('KEY_EXCHANGE\n' + str(publicKey)).encode('utf-8', errors='ignore'))
	
	data = receiveData(conn, 2479)

	messageType = data.decode('utf-8', errors='ignore').split('\n')[0]
	if messageType != 'KEY_EXCHANGE':
		print("The client sent an illegal response. Closing connection..")
		conn.close()
		return

	clientPublicKey = int(data.decode('utf-8', errors='ignore').split('\n')[1])
	sharedKey = ''

	try:
		dh.generate_shared_secret(clientPublicKey)
		sharedKey = bytes.fromhex(dh.shared_key)
	except Exception as e:
		print("The client sent an illegal response. Closing connection..")
		conn.close()
		return

	print('Key exchange successful: ' + dh.shared_key)
	
	print('Generating Ciphers..')
	
	cipher = AES.new(sharedKey, AES.MODE_CBC, 'jdirlfhixhtkwlif'.encode('utf-8'))

	print('Encrypting File list..')

	sharedFilesList = []
	
	for i in sharedFiles:
		sharedFilesList.append(i)

	fileList = ('\n'.join(sharedFilesList)).encode('utf-8')
	encryptedFileList = cipher.encrypt(pad(fileList, AES.block_size))
	requiredSize = len(encryptedFileList)
	
	print('Sending File List..')
	
	conn.sendall(('FILELIST\n'+padInteger(requiredSize, 20)).encode('utf-8', errors='ignore'))
	
	data = receiveData(conn, 5).decode('utf-8', errors='ignore')

	if data != 'READY':
		print('Client is not ready to receive file list..')
		conn.close()
		return
	conn.sendall(encryptedFileList)

	data = receiveData(conn, 3).decode('utf-8', errors='ignore')
	if data == 'ACK':
		print('File list was received successfully by client..')
	else:
		print('No Acknowledgement received..')
		conn.close()
		return
	print('Waiting for request..')

	data = receiveData(conn, 28).decode('utf-8', errors='ignore').split('\n')
	idx = int(data[1])
	if data[0] == 'REQUEST':
		if idx < 0 or idx >= len(sharedFilesList):
			print('\n\nThe client sent an illegal response. Closing connection..')
			conn.close()
			return
		else:
			fileName = sharedFilesList[idx].split('/')
			fileName = fileName[len(fileName) - 1]
			file = open(sharedFilesList[idx], 'rb')
			unencryptedData = file.read()
			file.close()
			cipher = AES.new(sharedKey, AES.MODE_CBC, 'jdirlfhixhtkwlif'.encode('utf-8'))
			encryptedData = cipher.encrypt(pad(unencryptedData, AES.block_size))
			requiredPackets = len(encryptedData)
			conn.sendall(('FILE\n'+padInteger(requiredPackets, 20)).encode('utf-8', errors='ignore'))
			data = receiveData(conn, 5).decode('utf-8', errors='ignore')
			if data != 'READY':
				print('Client is not ready to receive the file..')
				conn.close()
				return
			print("Sending the file '"+fileName+"'.")
			
			conn.sendall(encryptedData)
			print("Sent! Awaiting Acknowledgement..")
			
			data = receiveData(conn, 3).decode('utf-8', errors='ignore')
			if data == 'ACK':
				print('Client received the file successfully')
				conn.close()
			else:
				print('An unknown error occured in file transfer')
				conn.close()
	else:
		print('The client sent an illegal response. Closing connection..')
		conn.close()
		return

sharedFiles = set()
sys.stdin = open(".config", "r")

while True:
	file = ''
	try:
		file = input()
		file = file.replace('\\','/')
		if not os.path.isfile(file):
			print('File \"' + file + '\" was not found. Skipping..')
		else:
			sharedFiles.add(file)
	except EOFError as e:
		break

sys.stdin.close()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('', 23548))
s.listen(5)
print('Listening on port 23548...')

while True:
	conn, addr = s.accept()
	_thread.start_new_thread(requestHandler, (conn, addr));
