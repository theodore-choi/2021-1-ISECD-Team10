# -*- coding: utf-8 -*-

from multiprocessing import Process
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import *
from PyQt5 import uic,QtWebEngineWidgets
from PyQt5.QtCore import Qt, pyqtSlot
import random, itertools, threading, os, socket, cv2, time, sys, paramiko, stat, psutil, subprocess, atexit, math
from requests import get
from DB_contorol import saveDB, getDataFrameFromPSQL
from threading import Thread
from os.path import exists
import numpy as np
from PandasModel import PandasModel
import plotly.express as px
import datetime
import pandas as pd
import dlib
from keras.models import load_model
from imutils import face_utils
import tensorflow as tf

#pool.map()
'''
/***************************************************************/
            user( 사용자 정보를 다루는 클래스 전역 선언 )
            전역 변수 초기화 
            모델 로드
            SSH 모듈 로드
            얼굴인식모델 로드 

            소켓 통신 모듈 전역 선언
            게스트 리스트 UI모듈 전역 선언
            게스트 리스트 전역선언
            일시정지에 필요한 변수 전역 선언
            app 어플리케이션 전역 선언

/*************************시작**************************************/
'''


# pip install requests
def ipcheck():
    return get("https://api.ipify.org").text


class UserInfo:
    userType = False  # presenter: false /student : True
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

user = None
ssh = None
sftp = None
procs = [] ## process thread list
FORMAT = 'utf-8'
# temp data
host = '13.124.19.47'
username = 'ec2-user'

# 눈 크롭 프레임 사이즈 조정용
IMG_SIZE = (34, 26)
protoPath = "face_detector/deploy.prototxt"
modelPath = "face_detector/res10_300x300_ssd_iter_140000.caffemodel"
model = None
PR_guestlist = None
pauseclass = False
socketClient = False
app = None
ST_page = None

# 변수 초기설정

no_face = 0
no_eye = 0
start_time_f = 0
start_time_e = 0
sec_c = 0
close = 0
eye_cycle = 0
recording_eye = 0

student_login_list = []

form_class = uic.loadUiType("CSS_Main.ui")[0]

'''/*****************************종료**********************************************/'''


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
        #DialogDataVisualization(self)
        self.setWindowIcon(QIcon('icon/online-course-icon-57.png'))
        self.Presenter_button.clicked.connect(self.btn_clicked)
        self.Student_button.clicked.connect(self.btn_st_clicked)

    def btn_clicked(self):
        # QMessageBox.about(self, "message", "clicked")
        self.setDisabled(True)
        # self.setDisabled(True)
        self.PR_login = PR_LOGIN(self)
        # self.PR_login.exec_()
        # self.show()

    def btn_st_clicked(self):
        self.setDisabled(True)
        # QMessageBox.about(self, "message", "clicked")
        # self.setDisabled(True)
        self.ST_login = ST_LOGIN(self)
        # self.show()

    def closeEvent(self, QCloseEvent):
        re = QMessageBox.question(self, "종료 확인", "종료 하시겠습니까?",
                                  QMessageBox.Yes | QMessageBox.No)

        if re == QMessageBox.Yes:
            QCloseEvent.accept()
            exit_program()
        else:
            QCloseEvent.ignore()


class PR_LOGIN(QDialog):
    def __init__(self, parent):
        super(PR_LOGIN, self).__init__(parent)
        pr_login_ui = 'PR_LOGIN.ui'
        uic.loadUi(pr_login_ui, self)
        # self.Insert_Name.textChanged.connect()

        self.Login_Button.clicked.connect(self.btn_login_clicked)
        self.Back_Button.clicked.connect(self.btn_Back)
        # Sirial Number : license key

        # self.Insert_PW.setText()
        self.show()

    def btn_Back(self):
        # self.parent.show()
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
        # serial_list = ['145XER111', '123EQQ345', '134RKGI13', 'GG36728EE', 'ER345GGHH']
        islicense = False
        if not name == '' or serial == '':  # 145XER111
            for n in serial_list:
                if serial in n:  ## serial key is matching !!
                    isalready = saveDB(f"select user_name, licencekey from room_info where licencekey='{serial}'")
                    # serial_list.remove(serial) # delete query in DB
                    if isalready[0][0] == None or (isalready[0][0] == name and isalready[0][1] == serial):  #
                        user.userType = False  # presenter
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
            QMessageBox.about(self, "Warning", "Serial key 가 맞지 않습니다, 다시 시도 하십시오")

    def closeEvent(self, QCloseEvent):
        re = QMessageBox.question(self, "종료 확인", "종료 하시겠습니까?",
                                  QMessageBox.Yes | QMessageBox.No)

        if re == QMessageBox.Yes:
            QCloseEvent.accept()
            exit_program()
        else:
            QCloseEvent.ignore()


class ST_LOGIN(QDialog):
    def __init__(self, parent):
        super(ST_LOGIN, self).__init__(parent)
        st_login_ui = 'ST_LOGIN.ui'
        uic.loadUi(st_login_ui, self)

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

        # Room_list = ['81sp236l', '65v43us9', '3ls5864c', '34i72pz6', '8ts542u1']

        Room_list = saveDB("select room_code from room_info where room_code is not null")
        isnoRoom = True
        if not st_name == '' or roomnum == '':  # 81sp236l
            for room in Room_list:
                if roomnum in room:  ## serial key is matching !!
                    # db user info insert
                    self.hide()
                    user.userType = True  # 'student'
                    user.license_number = ''
                    # 캠이 켜져있는지
                    user.cam_is_valid = True  # ?
                    # 자리에 있는지 ?
                    user.User_is_on_seat = False
                    #

                    user.sleep = False
                    user.breakaway = False

                    # db Query insert room number
                    user.classRoom_id = roomnum
                    user.name = st_name
                    global ST_page
                    isnoRoom = False
                    ST_page = ST_PAGE(self)
                    break
        if isnoRoom:
            QMessageBox.about(self, "Warning", "Room Code 가 유효하지 않습니다, 다시 시도 하십시오")

    def closeEvent(self, QCloseEvent):
        re = QMessageBox.question(self, "종료 확인", "종료 하시겠습니까?",
                                  QMessageBox.Yes | QMessageBox.No)

        if re == QMessageBox.Yes:
            QCloseEvent.accept()
            exit_program()
        else:
            QCloseEvent.ignore()

from plotly.subplots import make_subplots
import plotly.graph_objects as go

class DialogDataVisualization(QDialog):
    def __init__(self, parent):
        super(DialogDataVisualization, self).__init__(parent)
        pr_login_ui = 'DialogDataVisualization.ui'
        uic.loadUi(pr_login_ui, self)
        self.browser = QtWebEngineWidgets.QWebEngineView(self)
        self.verticalLayout_3.addWidget(self.browser)
        classid = 1  # temp data

        dataframe1 = getDataFrameFromPSQL(f"select * from order_records where classroom_id='{classid}'")
        dataframe2 = getDataFrameFromPSQL(f"select * from state_records where classroom_id='{classid}'")
        dataframe3 = getDataFrameFromPSQL(f"select * from ng_records where classroom_id='{classid}'")

        Start = dataframe1.loc[dataframe1['order_status'] == 'START']['order_time']
        ts = pd.to_datetime(str(Start.values[0]))
        StartTime = ts.strftime('%y-%m-%d %I:%M:%S')
        End = dataframe1.loc[dataframe1['order_status'] == 'EXIT']['order_time']
        ts = pd.to_datetime(str(End.values[0]))
        EndTime = ts.strftime('%y-%m-%d %I:%M:%S')
        REST = dataframe1.loc[dataframe1['order_status'] == 'REST']['order_time']
        ts = pd.to_datetime(str(REST.values[0]))
        REST = ts.strftime('%y-%m-%d %I:%M:%S')
        RESTART = dataframe1.loc[dataframe1['order_status'] == 'RESTART']['order_time']
        ts = pd.to_datetime(str(RESTART.values[0]))
        RESTART = ts.strftime('%y-%m-%d %I:%M:%S')

        self.textBrowser.append(f"수업 시작 시간: {StartTime} ~ 수업 종료 시간: {EndTime}")
        self.textBrowser.append(f"수업 쉬는 시간: {REST} ~ {RESTART}")


        da = dataframe1.loc[:, ['order_status', 'order_time']]
        da.columns = ['mode', 'time']
        db = dataframe2.loc[:, ['event_id', 'applied_time']]
        db.columns = ['mode', 'time']
        dc = dataframe3.loc[:, ['ng_mode', 'ng_time_start']]
        dc.columns = ['mode', 'time']
        df = pd.concat([da, db, dc], ignore_index=True)
        # df = df.set_index('time')
        df = df.sort_values('time')
        #df.info()
        df['time1'] = df['time'].apply(
            lambda dt: datetime.datetime(dt.year, dt.month, dt.day, dt.hour, 10 * (dt.minute // 10)))

        xticklabels = [x.strftime('%H:%M') for x in df['time1']]
        #print(xticklabels)
        df['time2'] = xticklabels

        df_group = df.groupby(by=["time2", 'mode']).size().reset_index(name="counts")
        #fig = go.Figure()
        ts = pd.Timedelta(End.values[0] - Start.values[0]).seconds

        db = dataframe2.loc[:, ['user_name', 'event_id', 'applied_time']]
        # db.columns = ['name','mode','time']
        dc = dataframe3.loc[:, ['user_name', 'ng_mode', 'ng_time_start', 'ng_time_end', 'ng_mp4']]
        # dc.columns = ['name','mode','time']
        df_temp = pd.concat([db, dc], ignore_index=True)
        df_temp['ng_time'] = df_temp['ng_time_end'] - df_temp['ng_time_start']
        df_temp = df_temp.groupby(by=['user_name'])
        self.df_temp = df_temp
        lis_pd = []
        for name, df in df_temp: # 사용자별 테이블 생성
            BadTotaltime = df['ng_time'].sum()
            print(BadTotaltime)
            # print(df['ng_mode'].size)
            score = ((ts - BadTotaltime.seconds) / ts) * 100
            print(score)
            # print(df['ng_mode'].value_counts().sum())
            total_count = df['ng_mode'].value_counts().sum()

            sleeping = len(df[df['ng_mode'] == 'SLEEP'])  # df['ng_mode'].value_counts()
            moveout = len(df[df['ng_mode'] == 'BREAKAWAY'])
            lis_pd.append([name, score, BadTotaltime, total_count, sleeping, moveout ])

        self.dataframe = pd.DataFrame(lis_pd, columns=['이름','수업태도점수','누적 시간', '총 인식횟수','졸음인식횟수','자리이탈인식횟수'])

        fig = px.bar(data_frame=df_group, x="time2", y="counts", color='mode', barmode="group")
        fig.layout = dict(title='10분 사이 분석 결과 확인',
                          xaxis=dict(type="category",
                                     categoryorder='category ascending'))
        fig.update_xaxes(nticks=10)

        # x축 type을 카테고리 형으로 설정, 순서를 오름차순으로 날짜순서가 되도록 설정


        fig.update_layout(height=500, width=700,
                          title_text="수업시간 (10분 간격) 동안 수업태도 분석 결과", barmode='group')

        self.browser.setHtml(fig.to_html(include_plotlyjs='cdn'))

        # right layout
        self.tableWidget = QTableView()
        self.tableWidget.setSortingEnabled(True)
       #self.tableWidget.setSelectionMode(QAbstractItemView.DoubleClicked)
        self.tableWidget.doubleClicked.connect(self.tableWidget_doubleClicked)


        model_sales = PandasModel(self.dataframe)
        self.tableWidget.setModel(model_sales)
        self.verticalLayout_4.addWidget(self.tableWidget)

        self.tableWidget_student = QTableView()
        self.verticalLayout_5.addWidget(self.tableWidget_student)
        # Right        mouse        action

        self.tableWidget_student.setContextMenuPolicy(Qt.ActionsContextMenu)
        save_action = QAction("mp4 파일 내려받기", self.tableWidget_student)
        self.tableWidget_student.addAction(save_action)
        save_action.triggered.connect(self.__save_mp4)
        # self.setLayout(layout)
        self.show()

    @pyqtSlot()
    def __save_mp4(self):
        row = self.tableWidget_student.currentIndex().row()
        column = self.tableWidget_student.currentIndex().column()
        print(row, column)
        item = self.df_sub.iloc[row, 0]
        file = self.df_sub.iloc[row, 6]
        if not (type(file) == float):
            key = saveDB(f"select user_id, classroom_id from user_info where "
                   f"user_name='{item}'")

            file = str(key[0][1])+'/'+str(key[0][0])+'/'+self.df_sub.iloc[row, 6]
            GetFileFromServer('file', file)

    def tableWidget_doubleClicked(self):
        row = self.tableWidget.currentIndex().row()
        column = self.tableWidget.currentIndex().column()
        print(row, column)
        #item = tableWidget.item(row, column)

        item = self.dataframe.iloc[row,0]
        print(item)
        self.df_sub = self.df_temp.get_group(item)
        self.tableWidget_student.setSortingEnabled(True)

        model_sales = PandasModel(self.df_sub)
        self.tableWidget_student.setModel(model_sales)


        return


    def closeEvent(self, QCloseEvent):
        re = QMessageBox.question(self, "종료 확인", "종료 하시겠습니까?",
                                  QMessageBox.Yes | QMessageBox.No)

        if re == QMessageBox.Yes:
            QCloseEvent.accept()
            exit_program()
        else:
            QCloseEvent.ignore()



def GetFileFromServer(type, name):  #
    remote_path = '/home/ec2-user/CSS/'
    if type == 'file':
        file = name
        remote_file = remote_path + file
        print(sftp.listdir(remote_path))
        file = file.split('/')
        file = file[-1]
        sftp.get(remote_file, file)  # 파일 업로드

    #print("done")


def CreateRawFile(type, name):  #
    remote_path = '/home/ec2-user/CSS/'
    if type == 'file':
        file = name
        remote_file = remote_path + file
        #print(sftp.listdir(remote_path))
        file = file.split('/')
        file = file[-1]
        print(file, '--파일을 리눅스 서버로 전송 where? -- ', remote_file)
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

    print("파일 서버로 전송 완료 done")


class PR_PAGE(QDialog):

    def __init__(self, parent):
        super(PR_PAGE, self).__init__(parent)
        pr_page_ui = 'PR_PAGE.ui'
        uic.loadUi(pr_page_ui, self)
        roomnumber = returnRoomNumber()
        # db Query insert room number

        self.Class_Status.currentIndexChanged.connect(self.onSelected)

        #event = threading.Event()
        #event.clear()

        # room info, user_info DB table 에 user, room code 등록
        # 기존 로그인과 동일하다면?
        currentDB = saveDB(f"select user_name, licencekey from room_info where licencekey='{user.license_number}'")
        same = True
        if not currentDB:  # 아예 정보가 없거나
            user.classRoom_id = roomnumber
            same = False
            msg = f"update room_info set user_name = '{user.name}', room_code = '{user.classRoom_id}' where licencekey = '{user.license_number}'"
            saveDB(msg)
            self.lineEdit_room.setText(roomnumber)
        else:  # 새로운 정보일때만
            if not (currentDB[0][0] == user.name and currentDB[0][1] == user.license_number):
                user.classRoom_id = roomnumber
                same = False
                msg = f"update room_info set user_name = '{user.name}', room_code = '{user.classRoom_id}' where licencekey = '{user.license_number}'"
                saveDB(msg)
                self.lineEdit_room.setText(roomnumber)
            else:
                user.classRoom_id = roomnumber = \
                    saveDB(f"select room_code from room_info where licencekey = '{user.license_number}'")[0][0]
                self.lineEdit_room.setText(roomnumber)

        forignkey = saveDB(f"select classroom_id from room_info where licencekey='{user.license_number}'")[0][0]

        # classroom_id 폴더 서버에 생성하기
        CreateRawFile('folder', str(forignkey))
        if not same:  # 기존의 로그인정보가 없는 경우 추가
            msg = f"insert into user_info values(default, " \
                  f"'{forignkey}','{user.name}','{user.address}','{user.userType}'" \
                  f", True, False, False)"
            saveDB(msg)
        user_id = saveDB(f"select user_id from user_info where user_name='{user.name}'")[0][0]
        CreateRawFile('folder', str(forignkey) + '/' + str(user_id))

        # thread 1  로그인 성공하면 그때부터 사용자 정보 DB에 전송
        global socketClient
        socketClient = thrClient(0)
        #socketClient.set_eventobj(event)
        socketClient.daemon = True
        socketClient.start()
        procs.append(socketClient)
        self.show()

    def closeEvent(self, QCloseEvent):
        re = QMessageBox.question(self, "종료 확인", "종료 하시겠습니까?",
                                  QMessageBox.Yes | QMessageBox.No)

        if re == QMessageBox.Yes:
            QCloseEvent.accept()
            exit_program()
        else:
            QCloseEvent.ignore()

    def onSelected(self):
        selected = self.Class_Status.currentText()
        # 수업시 학생이 한명이상이어야 한다.
        if selected == '수업종료':
            DialogDataVisualization(self)

        if not selected == '' and len(student_login_list) >= 1:
            user.classOrder = selected
            msg = selected + ',' + user.classRoom_id
            socketClient.send(msg)
            # dp update
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
        if not currentDB:  # 만일 조회되지 않는다면 신규 유저이므로 등록을 진행한다.
            same = False  # 동일 유저가 아니므로 false
            msg = f"insert into user_info values(default, '{forienkey}', '{user.name}','{user.address}','{user.userType}', True, True, False)"
            saveDB(msg)  # 신규 유저 정보를 user_info 테이블에 insert 한다.
            user_id = saveDB(f"select user_id from user_info where user_ip='{user.address}'")[0][0]
            # classroom_id 폴더 서버에 생성하기
            CreateRawFile('folder', str(forienkey) + '/' + str(user_id))
        else:  # 기존에 등록되어있는 정보가 조회된다면?
            if currentDB[0][1] != user.address and currentDB[0][0] == user.name:  # ip 정보가 다르다면 다른 pc에서 접속한 것이므로, 이름은 같더라도 동일 인물일 수 있음, 따라서 등록을 진행한다.
                same = False
                msg = f"insert into user_info values(default, '{forienkey}', '{user.name}','{user.address}','{user.userType}', True, True, False)"
                saveDB(msg)
                user_id = saveDB(f"select user_id from user_info where user_ip='{user.address}'")[0][0]
                # classroom_id 폴더 서버에 생성하기
                CreateRawFile('folder', str(forienkey) + '/' + str(user_id))
            else:  # 기존의 등록되어있으면 아이피가 동일하다거나, 이름이 다르기만한? 동일 유저 인경우 여기에 들어온다.
                # 유저 이름 정도 업데이트
                saveDB(f"update user_info set user_name='{user.name}' where user_ip='{user.address}'")

        #event = threading.Event()
        #event.clear()
        # thread 1  로그인 성공하면 그때부터 사용자 정보 DB에 전송
        #global socketClient
        socketClient = thrClient(0)
        #socketClient.set_eventobj(event)
        socketClient.daemon = True  # 프로그램 종료시 프로세스도 함께 종료 (백그라운드 재생 X)
        socketClient.start()
        procs.append(socketClient)
        # 전송시 ip, 사용자 이름, 사용자
        # self.message.send('주수현')

        self.show()

    def closeEvent(self, QCloseEvent):
        re = QMessageBox.question(self, "종료 확인", "종료 하시겠습니까?",
                                  QMessageBox.Yes | QMessageBox.No)

        if re == QMessageBox.Yes:
            QCloseEvent.accept()
            exit_program()
        else:
            QCloseEvent.ignore()

    def onSelected(self):
        selected = self.Class_Status.currentText()
        # self.process.paused = 'pause'

        global pauseclass
        # DB update
        # select student list

        if selected == 'OFF' and (user.classOrder == '수업시작' or user.classOrder == '수업재개'):
            pauseclass = False  # 얼굴인식,프로세스 킬 일시 중지.
            # db update status order item
            # select student list
            user.User_is_on_seat = False
            # DB에 상태 변환됬다구 저장. 유저 인포에도 저장.
            uesr_search = saveDB(f"select user_id, classroom_id from user_info where user_ip='{user.address}'")[0]
            # 현재 캠 정보랑
            saveDB(
                f"update user_info set cam_status='{user.cam_is_valid}',emergency_status='{user.User_is_on_seat}' where user_ip='{user.address}'")

            msg = f"insert into state_records values(default, " \
                  f"'{uesr_search[0]}','{user.name}','{uesr_search[1]}','{selected}','{user.cam_is_valid}','{user.User_is_on_seat}',current_timestamp)"
            saveDB(msg)
        if selected == 'On' and (user.classOrder == '수업시작' or user.classOrder == '수업재개'):
            user.User_is_on_seat = True
            # DB에 상태 변환됬다구 저장. 유저 인포에도 저장.
            uesr_search = saveDB(f"select user_id, classroom_id from user_info where user_ip='{user.address}'")[0]
            saveDB(
                f"update user_info set cam_status='{user.cam_is_valid}',emergency_status='{user.User_is_on_seat}' where user_ip='{user.address}'")

            msg = f"insert into state_records values(default, " \
                  f"'{uesr_search[0]}','{user.name}','{uesr_search[1]}','{selected}','{user.cam_is_valid}','{user.User_is_on_seat}',current_timestamp)"
            saveDB(msg)

            pauseclass = True  # 얼굴인식,프로세스 킬 일시 중지.
            # self.process.set_eventobj(None) # thread 종료


'''
class CSS_CAM_POPUP(QDialog):
    def __init__(self):
        #super(CSS_CAM_POPUP, self).__init__(parent)
        super().__init__()
        css_popup_ui = 'CSS_CAM_POPUP.ui'
        uic.loadUi(css_popup_ui, self)
        self.setModal(True)
        self.show()

    def closeEvent(self, QCloseEvent):
        re = QMessageBox.question(self, "종료 확인", "종료 하시겠습니까?",
                                  QMessageBox.Yes | QMessageBox.No)

        if re == QMessageBox.Yes:
            QCloseEvent.accept()
            # exit_program()
        else:
            QCloseEvent.ignore()
'''


class PR_GUEST_LIST(QDialog):
    def __init__(self, parent):
        super(PR_GUEST_LIST, self).__init__(parent)
        pr_guestlist_ui = 'PR_GUEST_LIST.ui'
        uic.loadUi(pr_guestlist_ui, self)
        self.move(1250, 250)
        self.show()

    def closeEvent(self, QCloseEvent):
        re = QMessageBox.question(self, "종료 확인", "종료 하시겠습니까?",
                                  QMessageBox.Yes | QMessageBox.No)

        if re == QMessageBox.Yes:
            QCloseEvent.accept()
            exit_program()
        else:
            QCloseEvent.ignore()


class thrClient(Process):
    #event = None
    def __init__(self, id):
        super(Process, self).__init__()
        self.id = id
        self.processid = os.getpid()
        PORT = 6129

        SERVER = '13.124.19.47'  # '211.243.176.12'#'13.124.19.47'
        # '13.124.19.47' aws #'localhost'#'211.243.176.12'

        ADDR = (SERVER, PORT)

        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect(ADDR)

        t = Thread(target=self.rcvMsg, args=(),daemon=True)
        t.start()

        self.client.send(str(user.name + ',' + user.classRoom_id).encode())  # 서버에서 유저를 최초로 등록을 한다.
        # 그 이후 메시지는 자율적으로 보낸다. self.client.send

    def rcvMsg(self):  ## 서버로부터 메세지를 수신 받는 부분
        global PR_guestlist
        bStop = True
        print("Current thread: ", threading.current_thread().getName())
        while bStop:
            try:
                data = self.client.recv(1024)
                if not data:
                    break
                if user.userType == True:  # student
                    msg = data.decode()
                    print(msg)

                    global pauseclass

                    global ST_page
                    global detector
                    if msg == '수업시작':
                        ST_page.C_S.setText("수업중")
                        font1 = ST_page.C_S.font()
                        font1.setPointSize(12)
                        font1.setBold(True)
                        ST_page.C_S.setFont(font1)
                        ST_page.C_S.setStyleSheet("Color : green")
                        user.classOrder = msg
                        event = threading.Event()
                        event.clear()
                        facedetector = thrFaceDetection(detector,2)

                        # thread 2 수업시작 명령시 얼굴인식 Thread on
                        facedetector.set_eventobj(event)
                        facedetector.daemon = True
                        facedetector.start()
                        # thread 3 수업 시작 명령시 게임, 메신저 프로세스 감시 thread on
                        process = thrProcessKill(1)
                       # process.set_eventobj(event)
                        process.daemon = True
                        #process.set_eventobj(event)
                        process.start()
                        procs.append(process)
                    if msg == '쉬는시간':
                        ST_page.C_S.setText("쉬는시간")
                        font1 = ST_page.C_S.font()
                        font1.setPointSize(12)
                        font1.setBold(True)
                        ST_page.C_S.setFont(font1)
                        ST_page.C_S.setStyleSheet("Color : yellow")
                        user.classOrder = msg
                        pauseclass = True
                    if msg == '수업재개':
                        ST_page.C_S.setText("수업중")
                        font1 = ST_page.C_S.font()
                        font1.setPointSize(12)
                        font1.setBold(True)
                        ST_page.C_S.setFont(font1)
                        ST_page.C_S.setStyleSheet("Color : green")
                        user.classOrder = msg
                        pauseclass = False
                    if msg == '수업종료':
                        # 프로세스 감시와 통신 스레드 및 얼굴분석 종료
                        for p in procs:
                            p.terminate()
                            p.join()
                        facedetector.set_eventobj(None)
                        #process.set_eventobj(None)

                        ST_page.C_S.setText("수업종료")
                        font1 = ST_page.C_S.font()
                        font1.setPointSize(12)
                        font1.setBold(True)
                        ST_page.C_S.setFont(font1)
                        ST_page.C_S.setStyleSheet("Color : red")
                        user.classOrder = msg
                        bStop = False

                elif user.userType == False:  # 교수는 학생 이름을 모니터링 할 수 있다.
                    msg = data.decode()
                    notmsg = []
                    notmsg.append(user.name)  # 자신의 이름
                    notmsg.append('수업시작')  # 수업명령
                    notmsg.append('쉬는시간')
                    notmsg.append('수업재개')
                    notmsg.append('수업종료')
                    if msg[:6] == 'remove':
                        msg = msg[7:]
                        for x in range(PR_guestlist.student_list.count()):  ## logout
                            if msg == PR_guestlist.student_list.item(x).text():
                                PR_guestlist.student_list.takeItem(x)
                                del student_login_list[x]
                                break
                        # find = PR_guestlist.student_list.findItems(QtCore.QString(msg))
                        # PR_guestlist.student_list.removeItemWidget(find)
                    else:
                        if msg not in notmsg:  # 학생인 경우만 add Item
                            PR_guestlist.student_list.addItem(msg)
                            student_login_list.append(msg)  ## 출석 체크한 학생 추가
                    print(msg)

            except:
                pass

    #def set_eventobj(self, Event):
    #    self.event = Event

    def run(self):
        while True:
            tt = 0
            #if not self.event:
            #   break

    def send(self, msg):
        # 여기서 문자열을 전송할 때 encode()을 이용한다
        # 파이썬 문자열의 encode() 메소드는 문자열을 byte로 변환해주는 메소드이기 때문이다.

        self.client.send(msg.encode())
        # print(self.client.recv(2048).decode())
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
            # print(processName, ' - ', processID)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):  # 예외처리
            pass
    return pc_list


class thrProcessKill(Process):
    #event = None

    def __init__(self, id):
        super(Process, self).__init__()
        self.id = id
        self.processid= os.getpid()
        print(self.processid)

    #def set_eventobj(self, Event):
    #    self.event = Event

    def run(self):
        # if self.event == None:
        #    return
        # global paused
        global pauseclass
        # prevCamStatus = False
        while True:
            if not pauseclass:
                # prevCamStatus = self.camOn
                time.sleep(5)
                myprocesslist = getProcessRunList()  # 현재 실행중인 프로세스 리스트 불러오기
                myset = set(myprocesslist)  # 중복값 제거
                my_list = list(myset)  # 리스트로 변환

                block_Process_list = ['KakaoTalk.exe', 'LeagueClient.exe', 'RiotClientServices.exe',
                                      'fifa4launcher.exe', 'fifa4zf.exe', 'nProtect.exe', 'Webview-render.exe',
                                      'GnAgent.exe', 'GameBar.exe', 'GameBarFTServer.exe', 'NGM64.exe', 'GnStart.exe',
                                      'BlackCipher64.aes', 'Discord.exe', 'kakaotalk.exe', 'Gersang.exe', 'Gunz.exe',
                                      'BlackDesert32.exe', 'BlackDesert64.exe', 'PSkin.exe', 'goonzu.exe',
                                      'Client_Shipping.exe   ', 'nal.exe', 'NoxGame.exe', 'poker.exe', 'Baduk2.exe',
                                      'JangGi.exe', 'Northgard.exe', 'NX.exe', 'NFSEdge.exe', 'Dungeons3.exe',
                                      'deadcells.exe', 'destiny2.exe', 'ActionSquad.exe', 'dota2.exe', 'DragonNest.exe',
                                      'dro_client.exe', 'Droiyan Online.exe', 'Zero Ragexe.exe', 'Layers Of Fear.exe',
                                      'RainbowSix.exe', 'RailwayEmpire.exe', 'LoR.exe', 'lodoss.exe', 'LOSTARK.exe',
                                      'League of Legends.exe', 'LolClient.exe', 'LolClient.exe', 'LeagueClient.exe',
                                      'Lineage2M.exe', 'Ma9Ma9Remaster.exe', 'Marvel End Time Arena.exe',
                                      'MarvelHeroes2016.exe', 'client.exe', 'Mafia3.exe', 'MapleStory2.exe',
                                      'MapleStory.exe', 'FTGame.exe', 'MULegend.exe', 'mir2.exe', 'mir2_WinMode.exe',
                                      'vikings.exe', 'VALORANT-Win64-Shipping.exe', 'TslGame.exe', 'Battlerite.exe',
                                      'BattleriteRoyale.exe', 'Borderlands2.exe', 'BorderlandsPreSequel.exe',
                                      'BoilingBolt-Win64-Shipping.exe', 'VictorVran.exe', 'puyopuyoesports.exe',
                                      'Syberia3.exe', 'Cyphers.exe', 'ShadowArena64.exe', 'shadows.exe',
                                      'SuddenStrike4.exe', 'suddenattack.exe', 'seiya.exe', 'Sherlock.exe', 'smc.exe',
                                      'SoulWorker.exe', 'SuperPixelRacers.exe', 'SSF_Release.exe', 'starcraft.exe',
                                      'Steredenn.exe', 'StrikersEdge.exe', 'Splasher.exe', 'CivilizationV_DX11.exe',
                                      'CivilizationVI.exe', 'CivBE_Win32_DX11.exe', 'Client.exe', 'Arpiel.exe',
                                      'Asgard.exe', 'Astellia.exe', 'game.bin', 'Indiana-Win64-Shipping.exe',
                                      'iron_sight.exe', 'Atlantica.exe', 'Ancestors-Win64-Shipping.exe', 'Legend.exe',
                                      'AscendantOne-Win64-Shipping.exe', 'EOS.exe', 'ACEonline.atm',
                                      'shooter_win64_release.exe', 'XCom2.exe', 'XCom2_WOTC.exe', 'ELYON.exe', 'x2.exe',
                                      'YG2.exe', 'EternalReturn.exe', 'OrO20.exe', 'OldSchoolMusical.exe',
                                      'TheObserver-Win64-Shipping.exe', 'WB.exe', 'Warcraft III.exe',
                                      'WorldOfWarships.exe', 'ImmortalRealms.exe', 'City3.exe', 'Elancia.exe',
                                      'Genesis4Live.exe', 'PSkinII.exe', 'Sky.exe', 'Sky_x64.exe', 'MFishing.exe',
                                      'MCGame-Final.exe', 'TslGame.exe', 'engine.exe', 'ctgo2.exe', 'CoreMasters.exe',
                                      'ModernWarfare.exe', 'BlackOps4.exe', 'BlackOpsColdWar.exe', 'crossfire.exe',
                                      'Crookz.exe', 'CW.EXE', 'TygemBaduk.exe', 'InphaseNXD.exe', 'Tropico5.exe',
                                      'Tropico6-Win64-Shipping.exe', 'Client_tos.exe', '  Client_tos_x64.exe',
                                      'PointBlank.exe', 'FortniteClient-Win64-Shipping.exe', 'FortressV2.exe',
                                      'Furi.exe', 'HitGame.exe', 'FSeFootball.exe', 'pmangPoker.exe', 'pmangvegas.exe',
                                      'PMANGSLOTS.exe', 'fifazf.exe', 'PillarsOfEternity.exe', 'Hearthstone.exe',
                                      'HoundsApp.exe', 'HyperUniverse.exe', 'duelgo.exe', 'Hanjanggi.exe',
                                      'Hand of Fate 2.exe', 'Hover.exe', 'Holic2.exe   ', 'Among US.exe', 'r5apex.exe',
                                      'borealblade_64bit.exe', 'Cities.exe', 'CookingSim.exe', 'disco.exe',
                                      'DyingLightGame.exe', 'Eco.exe', 'fifa4zf.exe', 'Forge and Fight.exe',
                                      'FuryUnleashed.exe', 'hl2.exe', 'GasGuzzlers.exe', 'GTFO.exe',
                                      'HelloNeighbor-Win64-Shipping.exe', 'HouseFlipper.exe', 'HuntGame.exe',
                                      'Injustice2.exe', 'INSIDE.exe', 'Game-Win64-Shipping.exe', 'KingdomCome.exe',
                                      'left4dead2.exe', 'Mordhau-Win64-Shipping.exe', 'LF-Win64-Shipping.exe',
                                      'Phasmophobia.exe', 'hl2.exe', 'SpaceAssault-Win64-Shipping.exe',
                                      'RimWorldWin64.exe', 'Shieldwall-Win64-Shipping.exe', 'Sky Force Reloaded.exe',
                                      'Stardew Valley.exe', 'SH.exe', 'SuperliminalSteam.exe', 'Terraria.exe',
                                      'TheForest.exe', 'witcher3.exe', 'TheyAreBillions.exe', 'thief.exe',
                                      'Thrones.exe', 'Trailmakers.exe', 'trine4.exe', 'UltimateZombieDefense_64.exe',
                                      'UnrailedGame.exe', 'YAZD_HD.exe']  # ['KakaoTalk.exe', 'LeagueClient.exe']
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
                    print(process, 'is killed')
                continue


# 눈 Crop 함수
def crop_eye(img, eye_points):
    x1, y1 = np.amin(eye_points, axis=0)
    x2, y2 = np.amax(eye_points, axis=0)
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2

    w = (x2 - x1) * 1.2
    h = w * IMG_SIZE[1] / IMG_SIZE[0]

    margin_x, margin_y = w / 2, h / 2

    min_x, min_y = int(cx - margin_x), int(cy - margin_y)
    max_x, max_y = int(cx + margin_x), int(cy + margin_y)

    eye_rect = np.rint([min_x, min_y, max_x, max_y]).astype(np.int)

    eye_img = img[eye_rect[1]:eye_rect[3], eye_rect[0]:eye_rect[2]]

    return eye_img, eye_rect


# 눈인식 함수
def predictor_eye(gray, shapes):
    global model
    shapes = face_utils.shape_to_np(shapes)  # 찾은 랜드마크를 좌표로 저장하기

    eye_img_l, eye_rect_l = crop_eye(gray,
                                     eye_points=shapes[36:42])  # 저장된 랜드마크의 왼쪽 눈 좌표를 이용하여 이미지와 영상에 사각형을 그리기 위한 좌표 저장
    eye_img_r, eye_rect_r = crop_eye(gray,
                                     eye_points=shapes[42:48])  # 저장된 랜드마크의 오른쪽 눈 좌표를 이용하여 이미지와 영상에 사각형을 그리기 위한 좌표 저장
    if eye_img_l.size == 0:
        eye_img_l = np.ones(IMG_SIZE)
    if eye_img_r.size == 0:
        eye_img_r = np.ones(IMG_SIZE)

    eye_img_l = cv2.resize(eye_img_l, dsize=IMG_SIZE)  # 왼쪽 눈 이미지 사이즈 변경
    eye_img_r = cv2.resize(eye_img_r, dsize=IMG_SIZE)  # 오른쪽 눈 이미지 사이즈 변경
    eye_img_r = cv2.flip(eye_img_r, flipCode=1)  # 오른쪽 눈 이미지 좌우반전 (왼쪽눈으로만 모델이 학습되어 있음)

    #cv2.imshow('l', eye_img_l)  # 왼쪽 눈 크롭 프레임 보여주기
    #cv2.imshow('r', eye_img_r)  # 오른쪽 눈 크롭 프레임 보여주기

    eye_input_l = eye_img_l.copy().reshape((1, IMG_SIZE[1], IMG_SIZE[0], 1)).astype(np.float32) / 255.
    eye_input_r = eye_img_r.copy().reshape((1, IMG_SIZE[1], IMG_SIZE[0], 1)).astype(np.float32) / 255.

    pred_l = model.predict(eye_input_l)
    pred_r = model.predict(eye_input_r)

    # visualize
    state_l = 'O %.1f' if pred_l > 0.1 else '- %.1f'
    state_r = 'O %.1f' if pred_r > 0.1 else '- %.1f'

    state_l = state_l % pred_l
    state_r = state_r % pred_r

    return eye_rect_l, eye_rect_r, state_l, state_r, pred_l, pred_r

class thrFaceDetection(Thread):
    event = None

    def __init__(self, detector, id):
        super(thrFaceDetection, self).__init__()
        self.id = id
        self.detector = detector
        self.capture = cv2.VideoCapture(0)
        self.capture.set(3, 640)  # 윈도우 크기
        self.capture.set(4, 480)
        self.fc = 20.0
        self.codec = cv2.VideoWriter_fourcc(*'DIVX')  # Codec 설정
        # self.frame = None
        self.prevCamStatus = False
    def set_eventobj(self, Event):
        self.event = Event

    def run(self):
        print("Current thread: ", threading.current_thread().getName())
        # Read the next frame from the stream in a different thread
        global pauseclass

        global no_face
        global no_eye
        global start_time_f
        global start_time_e
        global sec_c
        global close
        global eye_cycle
        global recording_eye
        sleep = 0
        start_time = 0
        end_time = 0
        self.thread = Thread(target=self.update, args=())
        self.thread.daemon = True
        self.thread.start()
        self.prevCamStatus = False

        #out = cv2.VideoWriter('new.mp4', self.codec, self.fc, (640, 480))
        while (self.event):
            if not pauseclass:
                if self.capture.isOpened():
                    (self.camOn, self.frame) = self.capture.read()
                    if self.camOn:
                        str_cam_is_valid = 'CAM_ON'
                    else:
                        str_cam_is_valid = 'CAM_OFF'
                    user.cam_is_valid = self.camOn

                    # 이전 상태와 현 상태가 다르다면?
                    if self.prevCamStatus != self.camOn:
                        # DB에 상태 변환됬다구 저장. 유저 인포에도 저장.
                        uesr_search = \
                            saveDB(f"select user_id, classroom_id from user_info where user_ip='{user.address}'")[0]

                        saveDB(f"update user_info set cam_status='{user.cam_is_valid}' where user_ip='{user.address}'")

                        msg = f"insert into state_records values(default, " \
                              f"'{uesr_search[0]}','{user.name}','{uesr_search[1]}','{str_cam_is_valid}','{user.cam_is_valid}'," \
                              f"'{user.User_is_on_seat}',current_timestamp)"
                        saveDB(msg)

                    self.prevCamStatus = self.camOn

                    # 캠이 켜져 있다면?
                    if (self.camOn):
                        (h, w) = self.frame.shape[:2]

                        self.img = self.frame.copy()  # 복사본 생성
                        self.img = cv2.flip(self.img, 1)  # 화면 좌우 반전
                        gray = cv2.cvtColor(self.img, cv2.COLOR_BGR2GRAY)  # Frame 색상을 회색으로 변경

                        imageBlob = cv2.dnn.blobFromImage(cv2.resize(self.img, (300, 300)), 1.0, (300, 300),
                                                          (104.0, 177.0, 123.0), swapRB=False, crop=False)

                        self.detector.setInput(imageBlob)
                        detections = self.detector.forward()

                        face = []
                        for i in range(0, detections.shape[2]):
                            confidence = detections[0, 0, i, 2]

                            if confidence > 0.5:
                                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                                (startX, startY, endX, endY) = box.astype("int")

                                face = self.img[startY:endY, startX:endX]

                                cv2.rectangle(self.img, (startX, startY), (endX, endY), (255, 255, 255), 2)

                                shapes = predictor(gray, dlib.rectangle(startX, startY, endX,
                                                                        endY))  # 얼굴의 랜드마크 (눈, 코, 입, 턱선, 눈썹) 찾기
                                eye_rect_l, eye_rect_r, state_l, state_r, p_l, p_r = predictor_eye(gray, shapes)
                                white = (255, 255, 255)
                                red = (255,0,0)



                                cv2.rectangle(self.img, pt1=tuple(eye_rect_l[0:2]), pt2=tuple(eye_rect_l[2:4]),
                                              color=white if p_l > 0.5 else red,
                                              thickness=2)
                                cv2.rectangle(self.img, pt1=tuple(eye_rect_r[0:2]), pt2=tuple(eye_rect_r[2:4]),
                                              color=white if p_r > 0.5 else red,
                                              thickness=2)
                                cv2.putText(self.img, state_l, tuple(eye_rect_l[0:2]), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                                            white if p_l > 0.5 else red, 2)
                                cv2.putText(self.img, state_r, tuple(eye_rect_r[0:2]), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                                            white if p_r > 0.5 else red, 2)

                        #self.frame = cv2.flip(self.frame, 1)
                        cv2.putText(self.img, text=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())),
                                    org=(30, 460),
                                    fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=1,
                                    color=(0, 255, 0), thickness=2)
                        self.showframe = self.img
                        #out.write(self.showframe)
                        # cv2.imshow("Frame", self.frame)

                        if len(face) == 0:
                            no_face = no_face + 1
                            if no_face == 1:
                                no_face_time = 0
                                recording_face = 1

                                videoname_f = time.strftime('%Y-%m-%d %Hh %Mm %Ss_breakaway',
                                                          time.localtime(time.time()))
                                out_face = cv2.VideoWriter(videoname_f + '.mp4', self.codec, self.fc,
                                                      (int(self.capture.get(3)),
                                                       int(self.capture.get(4))))
                                out_face.write(self.img)
                                start_time_f = time.time()
                                print('파일 생성:', videoname_f + '.mp4')
                                #start_sleep_time = time.time()
                                #st_timestamp = time.strftime("%d-%b-%Y (%H:%M:%S.%f)")
                                ts = datetime.datetime.now()  # needs to be converted to a string
                                st_timestamp = ts.strftime("%d-%b-%Y (%H:%M:%S.%f)")
                                start_time = time.time()
                            if recording_eye == 1:
                                out_eye.release()
                                recording_eye = 0
                                sec_c = 0
                                eye_cycle = 0
                                close = 0
                                if no_eye >= 1:
                                    no_eye_time = 30 * no_eye
                                    print(str(datetime.timedelta(seconds=no_eye_time)) + ' 동안 졸았음')
                                    no_eye = 0
                                else:
                                    print("remove " + videoname_e + " video")
                                    os.remove(videoname_e + '.mp4')
                            no_face_time = time.time() - start_time_f

                            if no_face_time <= 300:
                                out_face.write(self.img)
                            elif no_face_time > 300 and recording_face == 1:
                                out_face.release()
                                recording_face = 0
                        else:
                            if no_face >= 1:
                                no_face = 0
                                if recording_face == 1:
                                    out_face.release()
                                    recording_face = 0
                                if no_face_time < 30:
                                    print("remove " + videoname_f + " video")
                                    os.remove(videoname_f + '.mp4')
                                else: # 자리이탈 인식
                                    print(str(datetime.timedelta(seconds=math.floor(no_face_time))) + ' 동안 얼굴이 인식 안 됨')
                                    # 자리이탈 인식 했으니 DB에 정보 insert 및 소켓통신으로 서버에 파일 저장
                                    ngmode = 'BREAKAWAY'
                                    user.breakaway = True
                                    ts = datetime.datetime.now()  # needs to be converted to a string
                                    end_timestamp = ts.strftime("%d-%b-%Y (%H:%M:%S.%f)")
                                    user_id = saveDB(f"select user_id from user_info where user_ip='{user.address}'")[0][0]
                                    classroom_id = saveDB(f"select classroom_id from user_info where user_ip='{user.address}'")[0][0]
                                    msg = f"insert into ng_records values(default, '{classroom_id}'," \
                                          f"'{user_id}','{user.name}','{ngmode}', '{st_timestamp}','{end_timestamp}','{videoname_f + '.mp4'}')"
                                    saveDB(msg)
                                    #print(checked_time)
                                    print('졸음이 인식 됨')
                                    # 소켓통신으로 서버에 파일 저장

                                    # socketClient.send_file(videoname+'.mp4')
                                    # classroom_id/user_id/.mp4
                                    userinfo = \
                                        saveDB(
                                            f"select classroom_id, user_id from user_info where user_ip='{user.address}'")[
                                            0]

                                    filepath = str(userinfo[0]) + '/' + str(userinfo[1]) + '/' + videoname_f + '.mp4'
                                    # global socketClient
                                    # socketClient.send_file(videoname+'.mp4')
                                    thr= Thread(target=CreateRawFile, args=('file', filepath), daemon=True)
                                    thr.start()

                            eye_cycle = eye_cycle + 1
                            if eye_cycle == 1:
                                eye_cycle_time = 0
                                start_time_e = time.time()

                            if eye_cycle == 1 and no_eye == 0:
                                recording_eye = 1
                                videoname_e = time.strftime('%Y-%m-%d %Hh %Mm %Ss_sleep', time.localtime(time.time()))
                                out_eye = cv2.VideoWriter(videoname_e + '.mp4', self.codec, self.fc,
                                                          (int(self.capture.get(3)), int(self.capture.get(4))))
                                print('파일 생성:', videoname_e + '.mp4')
                                out_eye.write(self.img)

                                ts = datetime.datetime.now()  # needs to be converted to a string
                                st_timestamp = ts.strftime("%d-%b-%Y (%H:%M:%S.%f)")
                            eye_cycle_time = time.time() - start_time_e

                            if recording_eye == 1:
                                out_eye.write(self.img)
                            if math.floor(eye_cycle_time) == sec_c:
                                sec_c = sec_c + 1
                                if math.floor(max(p_l, p_r) * 10) == 0:
                                    close = close + 1

                            if sec_c == 30:
                                sec_c = 0
                                eye_cycle = 0
                                if close >= 24:
                                    no_eye = no_eye + 1
                                    if no_eye == 1:
                                        print('졸음이 인식되었습니다.')
                                    elif no_eye == 10:
                                        out_eye.release()
                                        recording_eye = 0
                                else:
                                    if recording_eye == 1:
                                        out_eye.release()
                                        recording_eye = 0
                                    if no_eye >= 1:
                                        no_eye_time = 30 * no_eye
                                        print(str(datetime.timedelta(seconds=no_eye_time)) + ' 동안 졸았음')
                                        no_eye = 0
                                        # 졸음 인식 했으니 DB에 정보 insert 및 소켓통신으로 서버에 파일 저장
                                        ngmode = 'SLEEP'

                                        user.sleep = True
                                        ts = datetime.datetime.now()  # needs to be converted to a string
                                        end_timestamp = ts.strftime("%d-%b-%Y (%H:%M:%S.%f)")
                                        user_id = \
                                        saveDB(f"select user_id from user_info where user_ip='{user.address}'")[0][0]
                                        classroom_id = \
                                        saveDB(f"select classroom_id from user_info where user_ip='{user.address}'")[0][
                                            0]
                                        msg = f"insert into ng_records values(default, '{classroom_id}'," \
                                              f"'{user_id}','{user.name}','{ngmode}', '{st_timestamp}','{end_timestamp}','{videoname_e + '.mp4'}')"
                                        saveDB(msg)
                                        # print(checked_time)
                                        print('졸음이 인식 됨')
                                        # 소켓통신으로 서버에 파일 저장

                                        # socketClient.send_file(videoname+'.mp4')
                                        # classroom_id/user_id/.mp4
                                        userinfo = \
                                            saveDB(
                                                f"select classroom_id, user_id from user_info where user_ip='{user.address}'")[
                                                0]

                                        filepath = str(userinfo[0]) + '/' + str(
                                            userinfo[1]) + '/' + videoname_e + '.mp4'
                                        # global socketClient
                                        # socketClient.send_file(videoname+'.mp4')
                                        thr = Thread(target=CreateRawFile, args=('file', filepath), daemon=True)
                                        thr.start()
                                    else:
                                        print("remove " + videoname_e + " video")
                                        os.remove(videoname_e + '.mp4')
                                close = 0


                    else:
                        user.cam_is_valid = False
                        str_cam_is_valid = 'CAM_OFF'

                        uesr_search = saveDB(f"select user_id, classroom_id from user_info where user_ip='{user.address}'")[0]

                        saveDB(f"update user_info set cam_status='{user.cam_is_valid}' where user_ip='{user.address}'")

                        msg = f"insert into state_records values(default, '{uesr_search[0]}','{user.name}','{uesr_search[1]}','{str_cam_is_valid}','{user.cam_is_valid}','{user.User_is_on_seat}',current_timestamp)"
                        saveDB(msg)

                        msgBox = QMessageBox()
                        msgBox.setWindowTitle("카메라 확인 필요")  # 메세지창의 상단 제목
                        msgBox.setIcon(QMessageBox.Information)  # 메세지창 내부에 표시될 아이콘
                        msgBox.setText("카메라 확인 요청 메세지")  # 메세지 제목

                        msgBox.setInformativeText(
                            "카메라가 다른 앱에서 사용중이거나 연결되어있지 않습니다.\n 수업태도 분석을 위해 다른 앱에서 카메라를 꺼주십시오.")  # 메세지 내용

                        msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)  # 메세지창의 버튼

                        msgBox.setDefaultButton(QMessageBox.Yes)  # 포커스가 지정된 기본 버튼

                        msgBox.exec_()  # 클릭한 버튼 결과 리턴

                        # if re == QMessageBox.Yes:
                        #
                        # exit_program()
                        # else:
                        #
                        print('Please turn off other camera program!')
                        break
                else:
                    msgBox = QMessageBox()
                    msgBox.setWindowTitle("카메라 연결 확인")  # 메세지창의 상단 제목
                    msgBox.setIcon(QMessageBox.Information)  # 메세지창 내부에 표시될 아이콘
                    msgBox.setText("카메라 연결 요청 메세지")  # 메세지 제목
                    msgBox.setInformativeText(
                        "카메라가 연결되어있지 않습니다. 카메라를 설치해주세요.\n ")  # 메세지 내용
                    msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)  # 메세지창의 버튼
                    msgBox.setDefaultButton(QMessageBox.Yes)  # 포커스가 지정된 기본 버튼
                    msgBox.exec_()  # 클릭한 버튼 결과 리턴
                    break
                time.sleep(.01)

        pauseclass = True
        self.capture.release()
        cv2.destroyAllWindows()
        # cv2.destroyAllWindows()

    def update(self):
        # Display frames in main program
        # frame = imutils.resize(self.frame, width=400)
        # self.frame =
        global pauseclass

        print("Current thread: ", threading.current_thread().getName())
        while self.event:
            try:
                if not pauseclass:
                    cv2.imshow('For presenting', self.showframe)
                    time.sleep(.01)
                    #self.out.write(self.showframe)
                    key = cv2.waitKey(1)
                    if key == ord('q') and pauseclass:
                        #out.release()
                        self.capture.release()
                        cv2.destroyAllWindows()
                        pauseclass = True
                        exit(1)

            except AttributeError:
                pass


def savecounter():
    # DB user 등록 되어있으면
    # 해당 user정보에 로그인 = 0 으로 저장한다.
    userid = saveDB(
        f"select user_id from user_info where user_name='{user.name}' and classroom_id=(select classroom_id from room_info where room_code='{user.classRoom_id}')")
    if len(userid) > 0:  ## user 정보가 조회가 된다면 로그인 0
        saveDB(
            f"update user_info set login_status=False,cam_status='{user.cam_is_valid}',emergency_status='{user.User_is_on_seat}' "
            f"where user_id='{userid[0][0]}'")
    # exit_program()


def exit_program():
    savecounter()
    for n in procs:
        n.terminate()
        n.join()
    sftp.close()
    ssh.close()
    sys.exit()
def initialize():
    global user, sftp, predictor, detector,model,ssh
    config = tf.compat.v1.ConfigProto()
    config.gpu_options.per_process_gpu_memory_fraction = 0.4
    session = tf.compat.v1.Session(config=config)
    user = UserInfo()

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=username, key_filename='jusu.pem')
    sftp = ssh.open_sftp()

    # 얼굴 랜드마크 & 눈인식 모델 설정
    predictor = dlib.shape_predictor('models/shape_predictor_68_face_landmarks.dat')
    model = load_model('models/2018_12_17_22_58_35.h5')
    detector = cv2.dnn.readNetFromCaffe(protoPath, modelPath)
    model.summary()
    eye_img_l = np.ones(IMG_SIZE)
    eye_input_l = eye_img_l.copy().reshape((1, IMG_SIZE[1], IMG_SIZE[0], 1)).astype(np.float32) / 255.
    print(eye_input_l.shape)
    model.predict(eye_input_l)


if __name__ == "__main__":
    atexit.register(savecounter)  # 프로그램 종료 시 이벤트 발생
    initialize()
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('icon/online-course-icon-57.png'))
    myWindow = MyWindow()
    myWindow.show()

    app.exec_()
    savecounter()
    sftp.close()
    ssh.close()