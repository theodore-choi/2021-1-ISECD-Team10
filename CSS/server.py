import socket
import socketserver
import threading
import os
from collections import defaultdict

HEADER = 64
PORT = 6129
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
print(ADDR)
lock = threading.Lock()

class UserManager:
    def __init__(self):
        self.users = defaultdict(list)
    def addUser(self, username, room_code, conn, addr):
        # 쿼리로 insert DB 에 사용자 추가
        lock.acquire()
        self.users[room_code].append([conn, addr, username])
        lock.release()

        self.sendMsgToAll('%s' %username, room_code)
        return username

    def removeUser(self, connector, userip):  # 사용자를 제거하는 함수

        lock.acquire()

        breaker = False

        for key, value in self.users.items():
            i = 0
            for conn, addr, username in value:
                if addr[0] == userip and conn == connector:
                    del self.users[key][i]
                    if self.users[key].size(): # 아직 남았다면 !
                        self.users[key][0][0].send(('remove/'+username).encode()) #교수에게만 메세지 보내기 최초 사용자 등록은 교수가 먼저기 때문에 0번임
                    breaker = True
                    break
                i = i + 1
            if breaker==True:
                break
        lock.release()
        #for conn, addr, name in self.users[room]:
        #    conn.send(msg.encode())
        #self.sendMessageToAll('[%s]님이 퇴장했습니다.' % username)
        #print('--- 대화 참여자 수 [%d]' % len(self.users))
    def messageHandler(self, msg):
        #클라이언트에서 메시지로 단축어 사용해서 뭔가를 요청할때 처리 할 수 있음
        msg = msg.split(',')

        #if msg[0] == '수업시작' or msg[0] == '쉬는시간' or msg[0] == '수업재개' or msg[0] =='수업종료':
        if msg[0][-4:] == '.mp4':
           #self.recv_mp4(msg)
           return 1
        else:
            self.sendMsgToAll('%s'% msg[0], msg[1])

    def sendMsgToAll(self, msg, room):
        # DB 조회
        # 특정 클래스 룸안에 학생들 ip list 조회해서 user values를 가져오게끔 짜야함
        #for room in self.users:
        for conn, addr, name in self.users[room]:
            conn.send(msg.encode())



class TCPHandler(socketserver.BaseRequestHandler):

    userman = UserManager()

    def handle(self):
        print('[%s] 연결됨' % self.client_address[0])
        try:
            # 클라이언트의 이름을 가져오기
            username = self.registerUserInfo()
            # 그이후 while True에서 보내는 메시지 받기
            msg = self.request.recv(1024) # 전송 유형 수신 먼저 받는다 . #수신 받는다는걸 요청하는건가 보다
            while msg:
                print(msg.decode())
                mode = self.userman.messageHandler(msg.decode())
                if  mode == -1: # exit server
                    break
                if mode == 1: # send mp4 files
                    filename = msg.decode()
                    nowdir = os.getcwd()

                    file_size = int.from_bytes(self.request.recv(4096), byteorder="big")

                    self.request.sendall(bytes([255]))
                    # mp4 파일 받기
                    data = self.request.recv(1024)
                    if not data:
                        print('파일 %s 가 서버에 존재하지 않음' % filename)
                        self.request.close()
                        return
                    print(nowdir + "\\" + filename, file_size)

                    data_transferred = 0
                    # downbuff_size = 1048576
                    with open(nowdir + "\\" + filename, 'wb') as f:  # 현재dir에 filename으로 파일을 받는다
                        try:
                            while True:
                                if data_transferred < file_size:
                                    size = file_size - data_transferred
                                    if (size < 1024):
                                        data_transferred += size
                                    else:
                                        f.write(data)  # 1024바이트 쓴다
                                        data_transferred += len(data)
                                        data = self.request.recv(1024)  # 1024바이트를 받아 온다
                                else:
                                    break
                        except Exception as ex:
                            print(ex)
                    self.request.send("File received".encode())
                    print('파일 %s 받기 완료. 전송량 %d' % (filename, data_transferred))
                msg = self.request.recv(1024) # 수신 받는다는걸 요청하는건가 보다
        except Exception as e:
            print(e)

        print('[%s] 접속종료'% self.client_address[0])
        self.userman.removeUser(self.request, self.client_address[0])


    def registerUserInfo(self):
        while True:
            #self.request.send(''.encode()) # 로그인 ID: 라는 글을 클라이언트에게 보냄
            # rcvMsg 함수에서 바로 받고 출력해준다.
            username = self.request.recv(1024) # 인풋값이 들어오게 되면 메세지를 받게 된다.
            username = username.decode().split(',')

            if self.userman.addUser(username[0], username[1], self.request, self.client_address):
                return username[0]

class ChatingServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

def runServer():
    try:
        server = ChatingServer((SERVER, PORT), TCPHandler)
        server.serve_forever()
    except KeyboardInterrupt: # control + c 로 프로그램 종료
        server.shutdown()
        server.server_close()

print("[STARTING] server is starting...")
#start_server()
runServer()
