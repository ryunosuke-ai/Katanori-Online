import cv2
import time

#カメラの設定　デバイスIDは0, カメラIDは1
cap = cv2.VideoCapture(0)
photo_count = 1


while True:
    #カメラからの画像取得
    ret, frame = cap.read()
    #カメラの画像の出力
    jpg_filename = 'data/jpg/jpg' + str(photo_count) + ".jpg"
    
    cv2.imwrite(jpg_filename,frame)

    print(photo_count)
    photo_count += 1
    time.sleep(1)

cap.release()
cv2.destroyAllWindows()
