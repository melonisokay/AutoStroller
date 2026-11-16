# -*- coding:utf-8 -*-

'''!
  @file demo_get_distance.py
  @brief Get ranging data.
  @n Connect board with raspberryPi.
  @n --------------------------------------------
  @n sensor pin |         raspberry pi          |
  @n     VCC    |            5V/3V3             |
  @n     GND    |             GND               |
  @n     RX     |          (BCM)14 TX           |
  @n     TX     |          (BCM)15 RX           |
  @n --------------------------------------------
  @n
  @Copyright   Copyright (c) 2010 DFRobot Co.Ltd (http://www.dfrobot.com)
  @license     The MIT License (MIT)
  @author [Arya](xue.peng@dfrobot.com)
  @version  V1.0
  @date  2019-8-31
  @url https://github.com/DFRobot/DFRobot_RaspberryPi_A02YYUW
  @sudo raspi-config
  @ No to log shell Yes to serial port hardware
enable serial 
'''

import sys
import os
import time

#sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from DFRobot_RaspberryPi_A02YYUW import DFRobot_A02_Distance as Board

board = Board()

def print_distance(dis):
  if board.last_operate_status == board.STA_OK:
    print("Distance %d mm" %dis)
  elif board.last_operate_status == board.STA_ERR_CHECKSUM:
    print("ERROR")
  elif board.last_operate_status == board.STA_ERR_SERIAL:
    print("Serial open failed!")
  elif board.last_operate_status == board.STA_ERR_CHECK_OUT_LIMIT:
    print("Above the upper limit: %d" %dis)
  elif board.last_operate_status == board.STA_ERR_CHECK_LOW_LIMIT:
    print("Below the lower limit: %d" %dis)
  elif board.last_operate_status == board.STA_ERR_DATA:
    print("No data!")

def distance_change(dis):
  global previdis, duty
  slowinc = 5
  fastinc = 15
  closefactor = 1
  farfactor = 0.5
  change = previdis-dis

  if dis >= 150:
    factor = farfactor
  elif dis < 150:
    factor = closefactor

  if change <= 50:
    pass
  elif change <= 150:
    #decrease dis
    duty = duty - factor*slowinc
  elif change > 150:
    duty = duty - factor*fastinc
  print(f"change = {change}")
  print(f"duty cycle = {duty}")
  
  previdis = dis  

# function if mathematical methods are used to determine stationary and moving objects
# Required to determine diameter of wheel(d) and ratio factor = duty cycle/rotation(rpm)
def algormethod():
  d = 10.3
  circum = d * 3.1415
  dcrot_ratio = 25 # duty cycle / rotation/m 25 to test
  caldistravel = circum * (duty/dcrot_ratio)
  if (caldistravel - (previdis-distance)) <= 10 and (caldistravel - (previdis-distance)) >= -10:
    print("Stationary Object")
  elif (caldistravel - (previdis-distance)) < -10:
    print("Approaching Object")
  elif (caldistravel - (previdis-distance)) > 10:
    print("Distancing Object")
  print(f"calculated distance: {caldistravel}")
  print(f"previous distance: {previdis} current distance: {distance}")


if __name__ == "__main__":
  #Minimum ranging threshold: 0mm
  dis_min = 0 
  #Highest ranging threshold: 4500mm  
  dis_max = 4500 
  board.set_dis_range(dis_min, dis_max)
  previdis = 0
  duty = 50
  while True:
    distance = board.getDistance()
    if previdis == 0:
      previdis = distance
    print_distance(distance)
    #Delay time < 0.6s
    #time.sleep(0.3) 
    #distance_change(distance)
    algormethod()
    print(" ")
    time.sleep(1)
