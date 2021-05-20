# -*- coding: utf-8 -*-

import sys
from PyQt5.QtWidgets import *
from PyQt5 import uic
import random
import itertools
import threading
from requests import get
from DB_contorol import saveDB
from threading import Thread
import os
import socket
import time
import cv2
import sys
from os.path import exists
import numpy as np
import psutil,subprocess
import paramiko, stat
FORMAT = 'utf-8'
# temp data

PR_guestlist =None
pauseclass = False
socketClient = False
sftp = None



form_class = uic.loadUiType("CSS_Main.ui")[0]
# pip install requests
def ipcheck():
	return get("https://api.ipify.org").text

class UserInfo:
    userType = False #  presenter: false /student : True
    cam_is_valid = True
    User_is_on_seat = True
    classRoom_id = ''
    classOrder = ''
    license_number = ''
    sleep = ''
    breakaway = ''
    name = ''
    address = ''
    def __init__(self):
        self.address = ipcheck()


user = UserInfo()

def returnRoomNumber():
    numbers = list(itertools.combinations('123456789', 5))
    numbers2 = list(itertools.combinations('abcdefghijklmnopqrstuvwxyz', 3))

    number = random.choice(numbers)
    number2 = random.choice(numbers2)

    RoomNumberlist = list(number + number2)
    random.shuffle(RoomNumberlist)
    RoomNumber = ''.join(RoomNumberlist)

    print(RoomNumber)
    return RoomNumber


class MyWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.Presenter_button.clicked.connect(self.btn_clicked)
        self.Student_button.clicked.connect(self.btn_st_clicked)

    def btn_clicked(self):
        #QMessageBox.about(self, "message", "clicked")
        self.hide()
        #self.setDisabled(True)
        self.PR_login = PR_LOGIN(self)
        #self.PR_login.exec_()
        #self.show()

    def btn_st_clicked(self):
        self.hide()
        # QMessageBox.about(self, "message", "clicked")
        #self.setDisabled(True)
        self.ST_login = ST_LOGIN(self)
        #self.show()

class PR_LOGIN(QDialog):
    def __init__(self,parent):
        super(PR_LOGIN,self).__init__(parent)
        pr_login_ui = 'PR_LOGIN.ui'
        uic.loadUi(pr_login_ui,self)
        #self.Insert_Name.textChanged.connect()

        self.Login_Button.clicked.connect(self.btn_login_clicked)
        self.Back_Button.clicked.connect(self.btn_Back)
        # Sirial Number : license key

        # self.Insert_PW.setText()
        self.show()
    def btn_Back(self):
        #self.parent.show()
        self.close()
    def btn_login_clicked(self):
        # name is valid
        name = self.Insert_Name.text()
        # S/N is valid
        serial = self.Insert_PW.text()
        if name == '':
            QMessageBox.about(self, "Warning", "이름을 입력해주세요!")
        elif serial == '':
            QMessageBox.about(self, "Warning", "serial number을 입력해주세요!")

        serial_list = saveDB("select licencekey from room_info")
        # 5 item or serial
        #serial_list = ['145XER111', '123EQQ345', '134RKGI13', 'GG36728EE', 'ER345GGHH']
        islicense = False
        if not name == '' or serial =='': # 145XER111
            for n in serial_list:
                if serial in n: ## serial key is matching !!
                    isalready = saveDB(f"select user_name, licencekey from room_info where licencekey='{serial}'")
                    #serial_list.remove(serial) # delete query in DB
                    if isalready[0][0] == None or (isalready[0][0] == name and isalready[0][1] == serial): #
                        user.userType = False # presenter
                        user.license_number = serial
                        user.name = name
                        islicense = True
                        self.hide()

                        global PR_guestlist
                        self.PR_page = PR_PAGE(self)
                        PR_guestlist = PR_GUEST_LIST(self)

                        break
                    else:
                        QMessageBox.about(self, "Warning", "이미 등록된 사용자가 있습니다")
                        break
        if not islicense:
            QMessageBox.about(self, "Warning", "Serial key is not matching, Please retry")

class ST_LOGIN(QDialog):
    def __init__(self,parent):
        super(ST_LOGIN,self).__init__(parent)
        st_login_ui = 'ST_LOGIN.ui'
        uic.loadUi(st_login_ui,self)

        self.Login.clicked.connect(self.btn_login_clicked)
        self.Cancle.clicked.connect(self.btn_Close)
        self.show()
    def btn_Close(self):
        self.close()
    def btn_login_clicked(self):
        st_name = self.StudentName.text()
        roomnum = self.ClassRoom.text()

        if st_name == '':
            QMessageBox.about(self, "Warning", "이름을 입력해주세요!")
        elif roomnum == '':
            QMessageBox.about(self, "Warning", "Room Code을 입력해주세요!")

        #Room_list = ['81sp236l', '65v43us9', '3ls5864c', '34i72pz6', '8ts542u1']

        Room_list = saveDB("select room_code from room_info where room_code is not null")
        isnoRoom = True
        if not st_name == '' or roomnum =='': # 81sp236l
            for room in Room_list:
                if roomnum in room: ## serial key is matching !!
                    # db user info insert
                    self.hide()
                    user.userType = True #'student'
                    user.license_number = ''
                    # 캠이 켜져있는지
                    #user.cam_is_valid = False # ?
                    # 자리에 있는지 ?
                    #user.User_is_on_seat = False
                    #

                    user.sleep = False
                    user.breakaway = False


                    # db Query insert room number
                    user.classRoom_id = roomnum
                    user.name = st_name
                    self.ST_page = ST_PAGE(self)
                    isnoRoom = False
                    break
        if isnoRoom:
            QMessageBox.about(self, "Warning", "Room Code is not valid, Please retry")


def CreateRawFile(type, name): #
    remote_path = '/home/ec2-user/CSS/'

    if type == 'file':
        file = name
        remote_file = remote_path + file
        print(sftp.listdir(remote_path))
        file = file.split('/')
        file = file[-1]
        sftp.put(file, remote_file)  # 파일 업로드
    elif type == 'folder':
        folder = name
        remote_file = remote_path + folder
        # for i in sftp.listdir(remote_file):

        try:
            fileattr = sftp.lstat(remote_file)
            if not stat.S_ISDIR(fileattr.st_mode):  ## 이미 폴더가 있을 때
                sftp.mkdir(remote_file)
        except:  ## folder 가 없을 때
            sftp.mkdir(remote_file)

        # if not (sftp.chdir(remote_file)):
        # sftp.mkdir(remote_file)
        print(sftp.listdir(remote_file))

    print("done")

class PR_PAGE(QDialog):

    def __init__(self, parent):
        super(PR_PAGE, self).__init__(parent)
        pr_page_ui = 'PR_PAGE.ui'
        uic.loadUi(pr_page_ui, self)
        roomnumber = returnRoomNumber()
        # db Query insert room number

        self.Class_Status.currentIndexChanged.connect(self.onSelected)

        event = threading.Event()
        event.clear()

        # room info, user_info DB table 에 user, room code 등록
        # 기존 로그인과 동일하다면?
        currentDB= saveDB(f"select user_name, licencekey from room_info where licencekey='{user.license_number}'")
        same = True
        if not currentDB:  # 아예 정보가 없거나
            user.classRoom_id = roomnumber
            same = False
            msg = f"update room_info set user_name = '{user.name}', room_code = '{user.classRoom_id}' where licencekey = '{user.license_number}'"
            saveDB(msg)
            self.lineEdit_room.setText(roomnumber)
        else:           # 새로운 정보일때만
            if not (currentDB[0][0] == user.name and currentDB[0][1] == user.license_number):
                user.classRoom_id = roomnumber
                same = False
                msg = f"update room_info set user_name = '{user.name}', room_code = '{user.classRoom_id}' where licencekey = '{user.license_number}'"
                saveDB(msg)
                self.lineEdit_room.setText(roomnumber)
            else:
                user.classRoom_id = roomnumber = saveDB(f"select room_code from room_info where licencekey = '{user.license_number}'")[0][0]
                self.lineEdit_room.setText(roomnumber)


        forignkey = saveDB(f"select classroom_id from room_info where licencekey='{user.license_number}'")[0][0]

        # classroom_id 폴더 서버에 생성하기
        CreateRawFile('folder',str(forignkey))
        if not same:    # 기존의 로그인정보가 없는 경우 추가
            msg = f"insert into user_info values(default, " \
                  f"'{forignkey}','{user.name}','{user.address}','{user.userType}'" \
                  f", True, True, False)"
            saveDB(msg)
        user_id = saveDB(f"select user_id from user_info where user_ip='{user.address}'")[0][0]
        CreateRawFile('folder', str(forignkey) + '/' + str(user_id))

        # thread 1  로그인 성공하면 그때부터 사용자 정보 DB에 전송
        global socketClient
        socketClient = thrClient(user)
        socketClient.set_eventobj(event)
        socketClient.start()


        self.show()

    def onSelected(self):
        selected = self.Class_Status.currentText()
        if not selected == '':
            user.classOrder = selected
            msg = selected + ',' + user.classRoom_id
            socketClient.send(msg)
            #dp update
            forignkey = saveDB(f"select classroom_id from room_info where room_code='{user.classRoom_id}'")[0][0]
            msg = f"insert into order_records values(default, " \
                  f"'{forignkey}','{selected}',current_timestamp)"
            saveDB(msg)

class ST_PAGE(QDialog):
    def __init__(self, parent):
        super(ST_PAGE, self).__init__(parent)
        st_page_ui = 'ST_PAGE.ui'
        uic.loadUi(st_page_ui, self)
        self.Class_Status.currentIndexChanged.connect(self.onSelected)

        # thread 1  로그인 성공하면 그때부터 사용자 정보 DB에 전송
        # clinet는 DB와 연결 한다
        # 최초 라이센스 사용 및 사용자 정보 각 테이블에 등록
        # 클래스 id를 room info 테이블에서 가져온다. (학생이 들어가고자하는 room_code를 가진 클래스 id를)
        forienkey = saveDB(f"select classroom_id from room_info where room_code='{user.classRoom_id}'")[0][0]
        # 기존 로그인정보를 확인하기 위해 현재 입장하려는 유저의 ip가 등록되어 있는지 user info 에서 찾는다.
        currentDB = saveDB(f"select user_name, user_ip from user_info where user_ip='{user.address}'")
        # 동일 유저인지확인하는 변수 same
        same = True
        if not currentDB: # 만일 조회되지 않는다면 신규 유저이므로 등록을 진행한다.
            same = False            # 동일 유저가 아니므로 false
            msg = f"insert into user_info values(default, '{forienkey}', '{user.name}','{user.address}','{user.userType}', True, True, False)"
            saveDB(msg) # 신규 유저 정보를 user_info 테이블에 insert 한다.
            user_id = saveDB(f"select user_id from user_info where user_ip='{user.address}'")[0][0]
            # classroom_id 폴더 서버에 생성하기
            CreateRawFile('folder', str(forienkey) + '/' + str(user_id))
        else:# 기존에 등록되어있는 정보가 조회된다면?
            if currentDB[0][1] != user.address and currentDB[0][0] == user.name: # ip 정보가 다르다면 다른 pc에서 접속한 것이므로, 이름은 같더라도 동일 인물일 수 있음, 따라서 등록을 진행한다.
                same = False
                msg = f"insert into user_info values(default, '{forienkey}', '{user.name}','{user.address}','{user.userType}', True, True, False)"
                saveDB(msg)
                user_id = saveDB(f"select user_id from user_info where user_ip='{user.address}'")[0][0]
                # classroom_id 폴더 서버에 생성하기
                CreateRawFile('folder', str(forienkey)+ '/' + str(user_id))
            else:   #기존의 등록되어있으면 아이피가 동일하다거나, 이름이 다르기만한? 동일 유저 인경우 여기에 들어온다.
                #유저 이름 정도 업데이트
                saveDB(f"update user_info set user_name='{user.name}' where user_ip='{user.address}'")

        event = threading.Event()
        event.clear()
        #thread 1  로그인 성공하면 그때부터 사용자 정보 DB에 전송
        global socketClient
        socketClient = thrClient(user)
        socketClient.set_eventobj(event)
        socketClient.start()
        #전송시 ip, 사용자 이름, 사용자
        #self.message.send('주수현')

        self.show()
    def onSelected(self):
        selected = self.Class_Status.currentText()
        self.process.paused = 'pause'

        # DB update
        # select student list
        if selected == 'OFF':
            # db update status order item
            # select student list
            user.User_is_on_seat = False
            # DB에 상태 변환됬다구 저장. 유저 인포에도 저장.
            uesr_search = saveDB(f"select user_id, classroom_id from user_info where user_ip='{user.address}'")[0]
            saveDB(f"update user_info set cam_status='{self.camOn}' where user_ip='{user.address}'")

            msg = f"insert into state_records values(default, " \
                  f"'{uesr_search[0]}','{user.name}','{uesr_search[1]}','{selected}','{user.cam_is_valid}','{user.User_is_on_seat}',current_timestamp)"
            saveDB(msg)
        if selected == 'On':
            user.User_is_on_seat = False
            # DB에 상태 변환됬다구 저장. 유저 인포에도 저장.
            uesr_search = saveDB(f"select user_id, classroom_id from user_info where user_ip='{user.address}'")[0]
            saveDB(f"update user_info set cam_status='{self.camOn}' where user_ip='{user.address}'")

            msg = f"insert into state_records values(default, " \
                  f"'{uesr_search[0]}','{user.name}','{uesr_search[1]}','{selected}','{user.cam_is_valid}','{user.User_is_on_seat}',current_timestamp)"
            saveDB(msg)

            global pauseclass
            pauseclass = True # 얼굴인식,프로세스 킬 일시 중지.
            #self.process.set_eventobj(None) # thread 종료

class CSS_CAM_POPUP(QDialog):
    def __init__(self, parent):
        super(CSS_CAM_POPUP, self).__init__(parent)
        css_popup_ui = 'CSS_CAM_POPUP.ui'
        uic.loadUi(css_popup_ui, self)
        self.show()

class PR_GUEST_LIST(QDialog):
    def __init__(self, parent):
        super(PR_GUEST_LIST, self).__init__(parent)
        pr_guestlist_ui = 'PR_GUEST_LIST.ui'
        uic.loadUi(pr_guestlist_ui, self)
        self.move(1250, 250)
        self.show()


def rcvMsg(sock, userInfo): ## 서버로부터 메세지를 수신 받는 부분
    global PR_guestlist
    if userInfo.userType == True:
        event = threading.Event()
        event.clear()
        facedetector = thrFaceDetection()
        process = thrProcessKill()
    while True:
        try:
            data = sock.recv(1024)
            if not data:
                break
            if userInfo.userType == True: # student
                msg = data.decode()
                print(msg)

                global pauseclass
                if msg == '수업시작':
                    # thread 2 수업시작 명령시 얼굴인식 Thread on
                    facedetector.set_eventobj(event)
                    facedetector.start()
                    # thread 3 수업 시작 명령시 게임, 메신저 프로세스 감시 thread on
                    process.set_eventobj(event)
                    process.start()
                if msg == '쉬는시간':
                    pauseclass = True
                if msg == '수업재개':
                    pauseclass = False
                if msg == '수업종료':
                    process.set_eventobj(None)
                    facedetector.set_eventobj(None)


            elif userInfo.userType == False: # 교수는 학생 이름을 모니터링 할 수 있다.
                msg = data.decode()
                notmsg = []
                notmsg.append(userInfo.name)# 자신의 이름
                notmsg.append('수업시작')   # 수업명령
                notmsg.append('쉬는시간')
                notmsg.append('수업재개')
                notmsg.append('수업종료')
                if msg[:6] == 'remove':
                    msg = msg[7:]
                    for x in range(PR_guestlist.student_list.count()): ## logout
                        if msg == PR_guestlist.student_list.item(x).text():
                            PR_guestlist.student_list.takeItem(x)
                            break
                    #find = PR_guestlist.student_list.findItems(QtCore.QString(msg))
                    #PR_guestlist.student_list.removeItemWidget(find)
                else:
                    if not msg in notmsg: # 학생인 경우만 add Item
                        PR_guestlist.student_list.addItem(msg)

                print(msg)

        except:
            pass

class thrClient(Thread):
    event = None
    def __init__(self, userInfo):
        super(thrClient, self).__init__()
        PORT = 6129

        SERVER = '211.243.176.12'#'13.124.19.47'
        #'13.124.19.47' aws #'localhost'#'211.243.176.12'

        ADDR = (SERVER, PORT)

        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect(ADDR)

        t = Thread(target=rcvMsg, args=(self.client,userInfo))
        t.daemon = True
        t.start()
        self.client.send(str(userInfo.name+','+ userInfo.classRoom_id).encode()) # 서버에서 유저를 최초로 등록을 한다.
        # 그 이후 메시지는 자율적으로 보낸다. self.client.send

    def set_eventobj(self, Event):
        self.event = Event

    def run(self):
        while True:
            if not self.event:
                break


    def send(self, msg):
        # 여기서 문자열을 전송할 때 encode()을 이용한다
        # 파이썬 문자열의 encode() 메소드는 문자열을 byte로 변환해주는 메소드이기 때문이다.

        self.client.send(msg.encode())
        #print(self.client.recv(2048).decode())
        # print(client.recv(2048).decode(FORMAT))
        # client.close()

    def send_file(self, filename):
        self.client.send(filename.encode())

        file_size = os.path.getsize(filename)
        print("Find the file (%d bytes)" % file_size)
        self.client.sendall((file_size).to_bytes(length=8, byteorder="big"))

        data_transferred = 0
        if not exists(filename):
            print("no file")
            sys.exit()

        client_status = self.client.recv(1)
        if client_status == bytes([255]):
            print("파일 %s 전송 시작" % filename)

            # client.sendall(getFileSize(filename).encode())

            with open(filename, 'rb') as f:
                data = f.read(1024)  # 1024바이트 읽는다
                while data:  # 데이터가 없을 때까지
                    data_transferred += self.client.send(data)  # 1024바이트 보내고 크기 저장
                    data = f.read(1024)  # 1024바이트 읽음
                # client.sendall(bytes([255]))
        else:
            print("Client's Rejection")
        print("전송완료 %s, 전송량 %d" % (filename, data_transferred))
        print(self.client.recv(2048).decode())
        # print(client.recv(2048).decode(FORMAT))
        # client.close()

        # send(DISCONNECT_MESSAGE)

def getProcessRunList():
    pc_list = []
    for proc in psutil.process_iter():
        try:
            # 프로세스 이름, PID값 가져오기
            processName = proc.name()
            processID = proc.pid
            pc_list.append(processName)
            #print(processName, ' - ', processID)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):  # 예외처리
            pass
    return pc_list

class thrProcessKill(threading.Thread):
    event = None
    def __init__(self):
        super(thrProcessKill, self).__init__()
    def set_eventobj(self, Event):
        self.event = Event

    def run(self):
        #if self.event == None:
        #    return
        #global paused
        global pauseclass
        #prevCamStatus = False
        while (self.event):
            if not pauseclass:
                #prevCamStatus = self.camOn
                myprocesslist = getProcessRunList()  # 현재 실행중인 프로세스 리스트 불러오기
                myset = set(myprocesslist)  # 중복값 제거
                my_list = list(myset)  # 리스트로 변환

                block_Process_list = ['KakaoTalk.exe', 'LeagueClient.exe', 'RiotClientServices.exe','fifa4launcher.exe','fifa4zf.exe','nProtect.exe','Webview-render.exe','GnAgent.exe','GameBar.exe','GameBarFTServer.exe','NGM64.exe','GnStart.exe','BlackCipher64.aes','Discord.exe','kakaotalk.exe','Gersang.exe','Gunz.exe','BlackDesert32.exe','BlackDesert64.exe','PSkin.exe','goonzu.exe','Client_Shipping.exe   ','nal.exe','NoxGame.exe','poker.exe','Baduk2.exe','JangGi.exe','Northgard.exe','NX.exe','NFSEdge.exe','Dungeons3.exe','deadcells.exe','destiny2.exe','ActionSquad.exe','dota2.exe','DragonNest.exe','dro_client.exe','Droiyan Online.exe','Zero Ragexe.exe','Layers Of Fear.exe','RainbowSix.exe','RailwayEmpire.exe','LoR.exe','lodoss.exe','LOSTARK.exe','League of Legends.exe','LolClient.exe','LolClient.exe','LeagueClient.exe','Lineage2M.exe','Ma9Ma9Remaster.exe','Marvel End Time Arena.exe','MarvelHeroes2016.exe','client.exe','Mafia3.exe','MapleStory2.exe','MapleStory.exe','FTGame.exe','MULegend.exe','mir2.exe','mir2_WinMode.exe','vikings.exe','VALORANT-Win64-Shipping.exe','TslGame.exe','Battlerite.exe','BattleriteRoyale.exe','Borderlands2.exe','BorderlandsPreSequel.exe','BoilingBolt-Win64-Shipping.exe','VictorVran.exe','puyopuyoesports.exe','Syberia3.exe','Cyphers.exe','ShadowArena64.exe','shadows.exe','SuddenStrike4.exe','suddenattack.exe','seiya.exe','Sherlock.exe','smc.exe','SoulWorker.exe','SuperPixelRacers.exe','SSF_Release.exe','starcraft.exe','Steredenn.exe','StrikersEdge.exe','Splasher.exe','CivilizationV_DX11.exe','CivilizationVI.exe','CivBE_Win32_DX11.exe','Client.exe','Arpiel.exe','Asgard.exe','Astellia.exe','game.bin','Indiana-Win64-Shipping.exe','iron_sight.exe','Atlantica.exe','Ancestors-Win64-Shipping.exe','Legend.exe','AscendantOne-Win64-Shipping.exe','EOS.exe','ACEonline.atm','shooter_win64_release.exe','XCom2.exe','XCom2_WOTC.exe','ELYON.exe','x2.exe','YG2.exe','EternalReturn.exe','OrO20.exe','OldSchoolMusical.exe','TheObserver-Win64-Shipping.exe','WB.exe','Warcraft III.exe','WorldOfWarships.exe','ImmortalRealms.exe','City3.exe','Elancia.exe','Genesis4Live.exe','PSkinII.exe','Sky.exe','Sky_x64.exe','MFishing.exe','MCGame-Final.exe','TslGame.exe','engine.exe','ctgo2.exe','CoreMasters.exe','ModernWarfare.exe','BlackOps4.exe','BlackOpsColdWar.exe','crossfire.exe','Crookz.exe','CW.EXE','TygemBaduk.exe','InphaseNXD.exe','Tropico5.exe','Tropico6-Win64-Shipping.exe','Client_tos.exe','  Client_tos_x64.exe','PointBlank.exe','FortniteClient-Win64-Shipping.exe','FortressV2.exe','Furi.exe','HitGame.exe','FSeFootball.exe','pmangPoker.exe','pmangvegas.exe','PMANGSLOTS.exe','fifazf.exe','PillarsOfEternity.exe','Hearthstone.exe','HoundsApp.exe','HyperUniverse.exe','duelgo.exe','Hanjanggi.exe','Hand of Fate 2.exe','Hover.exe','Holic2.exe   ','Among US.exe','r5apex.exe','borealblade_64bit.exe','Cities.exe','CookingSim.exe','disco.exe','DyingLightGame.exe','Eco.exe','fifa4zf.exe','Forge and Fight.exe','FuryUnleashed.exe','hl2.exe','GasGuzzlers.exe','GTFO.exe','HelloNeighbor-Win64-Shipping.exe','HouseFlipper.exe','HuntGame.exe','Injustice2.exe','INSIDE.exe','Game-Win64-Shipping.exe','KingdomCome.exe','left4dead2.exe','Mordhau-Win64-Shipping.exe','LF-Win64-Shipping.exe','Phasmophobia.exe','hl2.exe','SpaceAssault-Win64-Shipping.exe','RimWorldWin64.exe','Shieldwall-Win64-Shipping.exe','Sky Force Reloaded.exe','Stardew Valley.exe','SH.exe','SuperliminalSteam.exe','Terraria.exe','TheForest.exe','witcher3.exe','TheyAreBillions.exe','thief.exe','Thrones.exe','Trailmakers.exe','trine4.exe','UltimateZombieDefense_64.exe','UnrailedGame.exe','YAZD_HD.exe']#['KakaoTalk.exe', 'LeagueClient.exe']
                # ,'RiotClientServices.exe','fifa4launcher.exe','fifa4zf.exe','nProtect.exe','Webview-render.exe','GnAgent.exe','GameBar.exe','GameBarFTServer.exe','NGM64.exe','GnStart.exe','BlackCipher64.aes','Discord.exe','kakaotalk.exe','Gersang.exe','Gunz.exe','BlackDesert32.exe','BlackDesert64.exe','PSkin.exe','goonzu.exe','Client_Shipping.exe   ','nal.exe','NoxGame.exe','poker.exe','Baduk2.exe','JangGi.exe','Northgard.exe','NX.exe','NFSEdge.exe','Dungeons3.exe','deadcells.exe','destiny2.exe','ActionSquad.exe','dota2.exe','DragonNest.exe','dro_client.exe','Droiyan Online.exe','Zero Ragexe.exe','Layers Of Fear.exe','RainbowSix.exe','RailwayEmpire.exe','LoR.exe','lodoss.exe','LOSTARK.exe','League of Legends.exe','LolClient.exe','LolClient.exe','LeagueClient.exe','Lineage2M.exe','Ma9Ma9Remaster.exe','Marvel End Time Arena.exe','MarvelHeroes2016.exe','client.exe','Mafia3.exe','MapleStory2.exe','MapleStory.exe','FTGame.exe','MULegend.exe','mir2.exe','mir2_WinMode.exe','vikings.exe','VALORANT-Win64-Shipping.exe','TslGame.exe','Battlerite.exe','BattleriteRoyale.exe','Borderlands2.exe','BorderlandsPreSequel.exe','BoilingBolt-Win64-Shipping.exe','VictorVran.exe','puyopuyoesports.exe','Syberia3.exe','Cyphers.exe','ShadowArena64.exe','shadows.exe','SuddenStrike4.exe','suddenattack.exe','seiya.exe','Sherlock.exe','smc.exe','SoulWorker.exe','SuperPixelRacers.exe','SSF_Release.exe','starcraft.exe','Steredenn.exe','StrikersEdge.exe','Splasher.exe','CivilizationV_DX11.exe','CivilizationVI.exe','CivBE_Win32_DX11.exe','Client.exe','Arpiel.exe','Asgard.exe','Astellia.exe','game.bin','Indiana-Win64-Shipping.exe','iron_sight.exe','Atlantica.exe','Ancestors-Win64-Shipping.exe','Legend.exe','AscendantOne-Win64-Shipping.exe','EOS.exe','ACEonline.atm','shooter_win64_release.exe','XCom2.exe','XCom2_WOTC.exe','ELYON.exe','x2.exe','YG2.exe','EternalReturn.exe','OrO20.exe','OldSchoolMusical.exe','TheObserver-Win64-Shipping.exe','WB.exe','Warcraft III.exe','WorldOfWarships.exe','ImmortalRealms.exe','City3.exe','Elancia.exe','Genesis4Live.exe','PSkinII.exe','Sky.exe','Sky_x64.exe','MFishing.exe','MCGame-Final.exe','TslGame.exe','engine.exe','ctgo2.exe','CoreMasters.exe','ModernWarfare.exe','BlackOps4.exe','BlackOpsColdWar.exe','crossfire.exe','Crookz.exe','CW.EXE','TygemBaduk.exe','InphaseNXD.exe','Tropico5.exe','Tropico6-Win64-Shipping.exe','Client_tos.exe','  Client_tos_x64.exe','PointBlank.exe','FortniteClient-Win64-Shipping.exe','FortressV2.exe','Furi.exe','HitGame.exe','FSeFootball.exe','pmangPoker.exe','pmangvegas.exe','PMANGSLOTS.exe','fifazf.exe','PillarsOfEternity.exe','Hearthstone.exe','HoundsApp.exe','HyperUniverse.exe','duelgo.exe','Hanjanggi.exe','Hand of Fate 2.exe','Hover.exe','Holic2.exe   ','Among US.exe','r5apex.exe','borealblade_64bit.exe','Cities.exe','CookingSim.exe','disco.exe','DyingLightGame.exe','Eco.exe','fifa4zf.exe','Forge and Fight.exe','FuryUnleashed.exe','hl2.exe','GasGuzzlers.exe','GTFO.exe','HelloNeighbor-Win64-Shipping.exe','HouseFlipper.exe','HuntGame.exe','Injustice2.exe','INSIDE.exe','Game-Win64-Shipping.exe','KingdomCome.exe','left4dead2.exe','Mordhau-Win64-Shipping.exe','LF-Win64-Shipping.exe','Phasmophobia.exe','hl2.exe','SpaceAssault-Win64-Shipping.exe','RimWorldWin64.exe','Shieldwall-Win64-Shipping.exe','Sky Force Reloaded.exe','Stardew Valley.exe','SH.exe','SuperliminalSteam.exe','Terraria.exe','TheForest.exe','witcher3.exe','TheyAreBillions.exe','thief.exe','Thrones.exe','Trailmakers.exe','trine4.exe','UltimateZombieDefense_64.exe','UnrailedGame.exe','YAZD_HD.exe']
                #
                # 중복하는가?
                #print('runing')
                isrunning = list(set(my_list).intersection(block_Process_list))
                for process in isrunning:
                    subprocess.call('taskkill /F /IM ' + process)
                    time.sleep(0.001)  # 밀리초(1/1000초
                    CREATE_NO_WINDOW = 0x08000000
                    subprocess.call('taskkill /F /IM ' + process, creationflags=CREATE_NO_WINDOW)
                continue

class thrFaceDetection(Thread):
    event = None
    def __init__(self):
        super(thrFaceDetection, self).__init__()
        self.protoPath = "face_detector/deploy.prototxt"
        self.modelPath = "face_detector/res10_300x300_ssd_iter_140000.caffemodel"
        self.detector = cv2.dnn.readNetFromCaffe(self.protoPath, self.modelPath)

    def set_eventobj(self, Event):
        self.event = Event

    def run(self):
        #if self.event == None:
        #    return
        #global paused

        cap = cv2.VideoCapture(0)
        cap.set(3, 640)  # 윈도우 크기
        cap.set(4, 480)
        fc = 20.0
        codec = cv2.VideoWriter_fourcc(*'DIVX')  # Codec 설정

        sleep = 0
        start_time = 0
        end_time = 0

        time.sleep(2.0)
        global pauseclass
        prevCamStatus = False
        while (self.event):
            if not pauseclass:
                self.camOn, frame = cap.read()
                if self.camOn:
                    cam_is_valid = 'CAM_ON'
                else:
                    cam_is_valid = 'CAM_OFF'
                user.cam_is_valid = self.camOn
                if prevCamStatus != self.camOn: # 이전 상태와 현 상태가 다르다면?
                    #DB에 상태 변환됬다구 저장. 유저 인포에도 저장.
                    uesr_search = saveDB(f"select user_id, classroom_id from user_info where user_ip='{user.address}'")[0]

                    saveDB(f"update user_info set cam_status='{self.camOn}' where user_ip='{user.address}'")

                    msg = f"insert into state_records values(default, " \
                          f"'{uesr_search[0]}','{user.name}','{uesr_search[1]}','{cam_is_valid}','{self.camOn}','{user.User_is_on_seat}',current_timestamp)"
                    saveDB(msg)

                prevCamStatus = self.camOn
                if (self.camOn):
                    (h, w) = frame.shape[:2]

                    imageBlob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 1.0, (300, 300),
                                                      (104.0, 177.0, 123.0), swapRB=False, crop=False)

                    self.detector.setInput(imageBlob)
                    detections = self.detector.forward()

                    face = []
                    for i in range(0, detections.shape[2]):
                        confidence = detections[0, 0, i, 2]

                        if confidence > 0.5:
                            box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                            (startX, startY, endX, endY) = box.astype("int")

                            face = frame[startY:endY, startX:endX]

                            #cv2.rectangle(frame, (startX, startY), (endX, endY), (255, 255, 255), 2)

                    #frame = cv2.flip(frame, 1)
                    #cv2.putText(frame, text=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())),
                    #            org=(30, 460),
                    #            fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=1,
                    #           color=(0, 255, 0), thickness=2)

                    #cv2.imshow("Frame", frame)

                    if len(face) == 0:
                        sleep = sleep + 1
                        if sleep == 1:
                            videoname = time.strftime('%Y-%m-%d %Hh %Mm',
                                                      time.localtime(time.time()))
                            out = cv2.VideoWriter(videoname + '.mp4', codec, fc, (int(cap.get(3)),
                                                                                  int(cap.get(4))))
                            print('파일 생성:', videoname + '.mp4')
                            start_time = time.time()
                        else:
                            out.write(frame)
                    else:
                        if sleep >= 1:
                            sleep = 0
                            end_time = time.time()
                            checked_time = end_time - start_time
                            out.release()
                            if checked_time < 30:
                                print("ok")
                                os.remove(videoname + '.mp4')
                            else:
                                # 자리이탈 인식 했으니 DB에 정보 insert 및 소켓통신으로 서버에 파일 저장
                                ngmode='BREAKAWAY'
                                user.breakaway = True
                                user_id = saveDB(f"select user_id from user_info where user_ip='{user.address}'")[0][0]
                                msg = f"insert into ng_records values(default, " \
                                      f"'{user_id}','{ngmode}', current_timestamp,'{videoname+'.mp4'}')"
                                saveDB(msg)
                                print(checked_time)
                                print('졸음이 인식 됨')
                                #소켓통신으로 서버에 파일 저장

                                #socketClient.send_file(videoname+'.mp4')
                                # classroom_id/user_id/.mp4
                                userinfo = saveDB(f"select classroom_id, user_id from user_info where user_ip='{user.address}'")[0]
                                filepath = str(userinfo[0])+'/'+str(userinfo[1])+'/'+ videoname+'.mp4'
                                #global socketClient
                                #socketClient.send_file(videoname+'.mp4')
                                CreateRawFile('file',filepath)

                    '''
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        break
                    elif key == ord('s'):
                        cv2.imwrite(time.strftime('%Y%m%d%H%M%S') + '.png', frame)
                    '''
                else:
                    CSS_CAM_POPUP(self)
                    print('Please turn off other camera program!')
                    break

        cap.release()



if __name__ == "__main__":
    host = '13.124.19.47'
    username = 'ec2-user'
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=username, key_filename='jusu.pem')
    sftp = ssh.open_sftp()

    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()
    app.exec_()
    sftp.close()
    ssh.close()
