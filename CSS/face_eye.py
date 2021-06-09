# 라이브러리 불러오기
import cv2, dlib, os, time, datetime, math
import numpy as np
from imutils import face_utils
from keras.models import load_model


# 눈 크롭 프레임 사이즈 조정용
IMG_SIZE = (34, 26)


#얼굴 인식용 모델 설정
protoPath = "face_detector/deploy.prototxt"
modelPath = "face_detector/res10_300x300_ssd_iter_140000.caffemodel"
detector = cv2.dnn.readNetFromCaffe(protoPath, modelPath)

#얼굴 랜드마크 & 눈인식 모델 설정
predictor = dlib.shape_predictor('models/shape_predictor_68_face_landmarks.dat')
model = load_model('models/2018_12_17_22_58_35.h5')
model.summary()


#동영상 저장용 설정
cap = cv2.VideoCapture(0)
cap.set(3, 640) # 윈도우 크기
cap.set(4, 480)
fc = 20
codec = cv2.VideoWriter_fourcc(*'DIVX') #Codec 설정

videoname_f = '조원 졸음동영상/2021-05-31 10h 38m 54s_sleep.mp4'

out_face = cv2.VideoWriter(videoname_f + '.mp4', codec, fc, (int(cap.get(3)), int(cap.get(4))))

#변수 초기설정

no_face = 0
no_eye = 0
start_time_f = 0
start_time_e = 0
sec_c = 0
close = 0
eye_cycle = 0



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
def predictor_eye (shapes):
    shapes = face_utils.shape_to_np(shapes) #찾은 랜드마크를 좌표로 저장하기

    eye_img_l, eye_rect_l = crop_eye(gray, eye_points=shapes[36:42]) # 저장된 랜드마크의 왼쪽 눈 좌표를 이용하여 이미지와 영상에 사각형을 그리기 위한 좌표 저장
    eye_img_r, eye_rect_r = crop_eye(gray, eye_points=shapes[42:48]) # 저장된 랜드마크의 오른쪽 눈 좌표를 이용하여 이미지와 영상에 사각형을 그리기 위한 좌표 저장

    if eye_img_l.size == 0:
        eye_img_l = np.ones(IMG_SIZE)
    if eye_img_r.size == 0:
        eye_img_r = np.ones(IMG_SIZE)

    eye_img_l = cv2.resize(eye_img_l, dsize=IMG_SIZE) # 왼쪽 눈 이미지 사이즈 변경
    eye_img_r = cv2.resize(eye_img_r, dsize=IMG_SIZE) # 오른쪽 눈 이미지 사이즈 변경
    eye_img_r = cv2.flip(eye_img_r, flipCode=1) # 오른쪽 눈 이미지 좌우반전 (왼쪽눈으로만 모델이 학습되어 있음)

    cv2.imshow('l', eye_img_l) # 왼쪽 눈 크롭 프레임 보여주기
    cv2.imshow('r', eye_img_r) # 오른쪽 눈 크롭 프레임 보여주기

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


while True:
    ret, img_ori = cap.read()

    if(ret) : # 캠 값을 잘 읽어 오는 경우
    
        (h, w) = img_ori.shape[:2]
        
        img = img_ori.copy() #복사본 생성
        img = cv2.flip(img,1) # 화면 좌우 반전
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) # Frame 색상을 회색으로 변경

        # 얼굴인식을 위한 캠화면 전처리
        imageBlob = cv2.dnn.blobFromImage(cv2.resize(img,(300,300)),1.0, (300,300),(104.0,177.0,123.0), swapRB=False, crop=False)
        
        detector.setInput(imageBlob) # DNN에 전처리 이미지 입력
        detections = detector.forward() # 얼굴 인식 결과 가져오기
        

        face = [] # 얼굴의 인식이 안 되는 경우를 파악하기 위한 변수 값 초기화
        for i in range(0,detections.shape[2]):
            confidence = detections[0,0,i,2]
            
            if confidence > 0.5: # 확률이 50% 이상일 경우

                # 인식된 얼굴 주변 사각형 그리기
                
                box = detections[0,0,i,3:7] * np.array([w,h,w,h])
                (startX, startY, endX, endY) = box.astype("int")
                
                face = img[startY:endY, startX:endX]
                                    
                cv2.rectangle(img, (startX, startY), (endX, endY), (255, 255, 255), 2) 


                # 눈 인식 및 인식된 눈 주변 사각형 그리기
                
                shapes = predictor(gray, dlib.rectangle(startX, startY, endX, endY)) #얼굴의 랜드마크 (눈, 코, 입, 턱선, 눈썹) 찾기
                eye_rect_l, eye_rect_r, state_l, state_r, p_l, p_r = predictor_eye(shapes)

                white = (255, 255, 255)
                red = (255, 0, 0)

                cv2.rectangle(img, pt1=tuple(eye_rect_l[0:2]), pt2=tuple(eye_rect_l[2:4]),
                              color=white if p_l > 0.5 else red,
                              thickness=2)
                cv2.rectangle(img, pt1=tuple(eye_rect_r[0:2]), pt2=tuple(eye_rect_r[2:4]),
                              color=white if p_r > 0.5 else red,
                              thickness=2)

                cv2.putText(img, state_l, tuple(eye_rect_l[0:2]), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                            white if p_l > 0.5 else red, 2)
                cv2.putText(img, state_r, tuple(eye_rect_r[0:2]), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                            white if p_r > 0.5 else red, 2)

        cv2.putText(img, text=time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())), org=(30, 460), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=1, color=(0,255,0), thickness=2)

        print('파일 생성:', videoname_f + '.mp4')
        out_face.write(img)
        cv2.imshow('result', img)
        '''
        if len(face) == 0:
            no_face = no_face + 1
            if no_face == 1:
                no_face_time = 0
                recording_face = 1
                videoname_f = time.strftime('%Y-%m-%d %H시 %M분 %S초',time.localtime(time.time()))
                out_face = cv2.VideoWriter(videoname_f+'.mp4', codec, fc, (int(cap.get(3)), int(cap.get(4))))
                print('파일 생성:',videoname_f+'.mp4')
                out_face.write(img)
                start_time_f = time.time()

            if recording_eye == 1 :
                out_eye.release()
                recording_eye = 0
                sec_c = 0
                eye_cycle = 0
                close = 0
                if no_eye >= 1 :
                    no_eye_time = 30 * no_eye
                    print(str(datetime.timedelta(seconds=no_eye_time))+' 동안 졸았음')
                    no_eye = 0
                else :
                    print("remove "+videoname_e+" video")
                    os.remove(videoname_e + '.mp4')
                

            no_face_time = time.time() - start_time_f

            if no_face_time <= 300 :
                out_face.write(img) # img_ori로 저장할지?
            elif no_face_time > 300 and recording_face == 1 :
                out_face.release()
                recording_face = 0
        else :
            if no_face >= 1:
                no_face = 0
                if recording_face == 1:
                    out_face.release()
                    recording_face = 0
                if no_face_time < 30 :
                    print("remove "+videoname_f+" video")
                    os.remove(videoname_f+'.mp4')
                else :
                    print(str(datetime.timedelta(seconds=math.floor(no_face_time)))+' 동안 얼굴이 인식 안 됨')
            eye_cycle = eye_cycle + 1

            if eye_cycle == 1 :
                eye_cycle_time = 0
                start_time_e = time.time()

            if eye_cycle == 1 and no_eye == 0 :
                recording_eye = 1
                videoname_e = time.strftime('%Y-%m-%d %H시 %M분 %S초',time.localtime(time.time()))
                out_eye = cv2.VideoWriter(videoname_e+'.mp4', codec, fc, (int(cap.get(3)), int(cap.get(4))))
                print('파일 생성:',videoname_e+'.mp4')
                out_eye.write(img)

            eye_cycle_time = time.time() - start_time_e

            if recording_eye == 1 :
                out_eye.write(img)
            
            if math.floor(eye_cycle_time) == sec_c :
                sec_c = sec_c + 1
                if math.floor(max(p_l, p_r)*10) == 0 :
                    close = close + 1

            if sec_c == 30 :
                sec_c = 0
                eye_cycle = 0
                if close >= 24 :
                    no_eye = no_eye + 1
                    if no_eye == 1 :
                        print('졸음이 인식되었습니다.')
                    elif no_eye == 10 :
                        out_eye.release()
                        recording_eye = 0
                else :
                    if recording_eye == 1:
                        out_eye.release()
                        recording_eye = 0
                    if no_eye >= 1 :
                        no_eye_time = 30 * no_eye
                        print(str(datetime.timedelta(seconds=no_eye_time))+' 동안 졸았음')
                        no_eye = 0
                    else :
                        print("remove "+videoname_e+" video")
                        os.remove(videoname_e + '.mp4')
                close = 0
                       
                  
        if cv2.waitKey(1) == ord('q'):
            break
        
    else : # 다른 카메라 시스템이 켜져서 캠 값을 못 읽어오는 경우
        print('Please turn off other camera program!')
        break


if recording_face == 1 :
    out_face.release()
if recording_eye == 1 :
    out_eye.release()
if no_face >= 1 :
    print('수업 종료 할 때까지, ')
    print(str(datetime.timedelta(seconds=math.floor(no_face_time)))+' 동안 얼굴이 인식 안 됨')
if no_eye >= 1 :
    no_eye_time = 30 * no_eye
    print('수업 종료 할 때까지, ')
    print(str(datetime.timedelta(seconds=no_eye_time))+' 동안 졸았음')
'''
out_face.release()
out_eye.release()


cap.release()
cv2.destroyAllWindows()
