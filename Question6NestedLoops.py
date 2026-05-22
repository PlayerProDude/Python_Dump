
import cv2
from djitellopy import Tello
import time
tello = Tello()
tello.connect()
tello.streamon()
frame_read = tello.get_frame_read()
 
x = int(input("How many flights?"))
y = int(input("How many pictures?"))
z = int(input("How many seconds between each picture?"))
 
 
for i in range(x):
  tello.takeoff()
  time.sleep(2)
  tello.move_forward(100)
  for b in range(y):
    cv2.imwrite(f"target{b}.png", frame_read.frame)
    time.sleep(z)
  tello.move_backward(100)
  tello.land()
 

