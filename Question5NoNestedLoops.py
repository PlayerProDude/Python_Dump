import cv2
from djitellopy import Tello
import time
tello = Tello()
tello.connect()
tello.streamon()
frame_read = tello.get_frame_read()
x = int(input("How many flights? "))
y = int(input("How many pictures? "))
z = int(input("How many seconds between each picture? "))

total_pictures = x * y
pictures_taken = 0

tello.takeoff()
time.sleep(2)

while pictures_taken < total_pictures:
    if pictures_taken % y == 0:
        tello.move_forward(100)
    cv2.imwrite(f"target{pictures_taken}.png", frame_read.frame)
    time.sleep(z)
    pictures_taken += 1
    if pictures_taken % y == 0:
        tello.move_backward(100)

tello.land()