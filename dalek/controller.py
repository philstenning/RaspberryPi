#!/usr/bin/env python
if __name__ == "__main__":
   '''
   This if statement is needed for testing, to locate the modules needed
   if we are running the file directly.
   '''
   import sys
   from os import path
   sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )
   from dalek import settings
   from dalek import sound_player
   import RPi.GPIO as GPIO  
   from dalek import spi  

import os.path
import struct
import time
from dalek import drive 
from dalek import debug
from dalek import ui
from challenges import slightly_deranged_golf
from challenges import the_duck_shoot

###
### SETUP 
###

# the '/dev/input/js0' file is in the sudo root of the file system.
# it only apears once the device has paired.
# use the setup guide from https://www.piborg.org/blog/rpi-ps3-help

# wait until the joystick is paired...
def init():
    fn = '/dev/input/js0'
    
    debug.print_to_all_devices("Testing for joystick: {}...".format(fn))
    
    file_exists = False
    while file_exists == False:
     
      file_exists = os.path.exists(fn)
      debug.print_to_all_devices('joystick paired: {} '.format(os.path.exists(fn)))
      time.sleep(3)
    
    
    jsdev = open(fn, 'rb')
    debug.print_to_all_devices('Joystick paired. Ok \n', "Prd")
    
# Ps3 controller settings.
def use(dalek_settings, dalek_sounds):

  current_challenge = 1

  # this is the joystick file we stream data from.
  jsdev = open("/dev/input/js0", 'rb')

  joystickD_padCurrentButton = 0  # used for debounce of switches on dpad.
  
  # The Main Mode we are in
  # 1 Drive mode
  # 2 Challenge Select Mode
   # 3 Exterminate Mode this mode does nothing so is standby and disables the paddles on    
   #   the controller
  ps3_ControllerMode=1 
  tank_drive_on = True           

  axisX = 0        # main  axis variables nomalized
  axisY = 0        # main  axis variables nomalized
  minusX= False    # used for nomalizing the data
  minusY=False     # used for nomalizing the data
  
  leftPaddle = 0   # raw axis data
  rightPaddle = 0  # raw axis data

  # initialize the challanges
  # these are classes that implement the threading.Thread module
  # def current_challenge_thread_create(name=None):
  #   # if current_challenge_thread.is_alive():
  #   #   print("thread still alive...")

  #   # if current_challenge_thread.running == True:
  #   #         # Make sure current thread has stoped.
  #   #         print("thread stopping...")
  #   #         current_challenge_thread.stop_runnning()
  #   #         current_challenge_thread.join()

  #   if name == "7": 
  #       return slightly_deranged_golf.Challange()
  #   elif name == None:
  #       return slightly_deranged_golf.Challange()    
    
  # challange_slightly_deranged_golf.start()
  
  current_challenge_thread = slightly_deranged_golf.Challange(dalek_settings, dalek_sounds)

  def challenge_select(value):
    nonlocal current_challenge
    number_of_challenges = 7
    currentChallenge = current_challenge
    
    if value == 0: #Up Button
      if currentChallenge > 1:
        currentChallenge -=1
      else:
        currentChallenge = number_of_challenges
    
    else:         #Down Button
      if number_of_challenges >= (currentChallenge + 1): # so we dont exceed max number of missions
        currentChallenge +=1
      else:
        currentChallenge = 1
 
    current_challenge = currentChallenge
    ui.display_selected_challenge(current_challenge)

  ###########################################################
  ###  DPad Buttons on ps3 controller (Left hand buttons) ##
  ###########################################################
  
  def dpad_up_button_pressed():
    if ps3_ControllerMode == 2: # 2 Mission Select Mode
      challenge_select(0) 
    else:
      debug.print_to_all_devices('Forwards', "FW") 
      drive.forward(dalek_settings.speed)

  def dpad_down_button_pressed():
    if ps3_ControllerMode == 2: # 2 Mission Select Mode
      challenge_select(1)
    else:
      debug.print_to_all_devices('Backwards', "BW")  
      drive.backward(dalek_settings.speed)
    
    
  def dpad_right_button_pressed():
    if ps3_ControllerMode != 2:
      debug.print_to_all_devices('Spin Rigrt', "SR") 
      drive.spinRight(dalek_settings.speed)


  def dpad_left_button_pressed():
    if ps3_ControllerMode != 2:
      debug.print_to_all_devices('Spin Left', "SL") 
      drive.spinLeft(dalek_settings.speed)

  
  def dpad_button_pressed(value,number, _joystickD_padCurrentButton):
    if (value==0) and (number == _joystickD_padCurrentButton):
      drive.stop()
      if ps3_ControllerMode ==1:
        debug.print_to_all_devices("Stop", "SP")
    #Up button
    else:
      if number == 4:
        if value: # value is 1 for pressed 0 for released.
          dpad_up_button_pressed()
    
      #Right button
      elif number == 5:
        if value:
          dpad_right_button_pressed()
      
      # Down button
      elif number == 6:
        if value:
          dpad_down_button_pressed()
      
      # Left button
      elif number == 7: 
        if value:
          dpad_left_button_pressed()
  
  def tank_drive( _leftPaddle, _rightPaddle):
    debug.print_to_all_devices("left: {}  Right: {}".format(_leftPaddle,_rightPaddle ))
    
    if (_leftPaddle == 0) and (_rightPaddle == 0):
      drive.stop()
      debug.clear()
    elif (_leftPaddle < 0) and (_rightPaddle < 0):
      drive.paddleForward(- _leftPaddle, - _rightPaddle)
      debug.print_to_all_devices("forwards","Fw")
    elif (_leftPaddle > 0) and (_rightPaddle > 0):
      drive.paddleBackward( _leftPaddle, _rightPaddle)
      debug.print_to_all_devices("Backwards", "Bw")
    elif (_leftPaddle <= 0) and (_rightPaddle >= 0):
      drive.turnForwardRight(- _leftPaddle,  _rightPaddle)
      debug.print_to_all_devices("Spin Right", "SR")
    elif (_leftPaddle >= 0) and (_rightPaddle <= 0):
      drive.turnForwardLeft(  _leftPaddle,- _rightPaddle)
      debug.print_to_all_devices("Spin Left", "SL")

  ###########################################################
  ###  Symbol Buttons on the Controller                    ##
  ###########################################################
  def button_circle():
    # if ps3_ControllerMode == 1:
    #   pass
    # elif ps3_ControllerMode ==2:
    if current_challenge_thread.running == True:
         current_challenge_thread.circle_button_pressed()

    # elif ps3_ControllerMode ==3:
    #   pass
    dalek_sounds.play_sound("Must Survive")
    # debug.print_to_all_devices("Circle Button Pressed")

  def button_square():
    if current_challenge_thread.running == True:
         current_challenge_thread.square_button_pressed()
    dalek_sounds.play_sound("exterminate")
    # debug.print_to_all_devices("Exterminate...")

  def button_triangle():
    if current_challenge_thread.running == True:
         current_challenge_thread.triangle_button_pressed()
    dalek_sounds.play_sound("Stay")
    # debug.print_to_all_devices("Triangle Button Pressed")
  def button_cross():

    if current_challenge_thread.running == True:
         current_challenge_thread.cross_button_pressed()
    dalek_sounds.play_sound("Time is right")
    # debug.print_to_all_devices("Cross Button Pressed")
  
  ###########################################################
  ###  Lower Butons on the Controller                      ##
  ###########################################################
  def button_L1():
    debug.print_to_all_devices("L1 Button Pressed", "L1")
   
  def button_L2():
    dalek_sounds.decreese_volume_level()
    debug.print_to_all_devices("L2 Button Pressed" , "L2")

  def button_R1():
    debug.print_to_all_devices("R1 Button Pressed", "R1")
    
  def button_R2():
    dalek_sounds.increese_volume_level()
    debug.print_to_all_devices("R2 Button Pressed", "R2" )
  ###########################################################
  ###  Main Buttons on the Controller                      ## 
  ###########################################################

  def button_select(ps3_controller_mode):
    nonlocal current_challenge_thread
    if ps3_controller_mode == 2: # Challenge Select Mode

        

        ui.you_selected_challenge(current_challenge)
        
        if current_challenge == 1:  ## output for onboard device
           debug.print_to_all_devices("TODO: Obstacle Course")
        elif current_challenge == 2: 
           debug.print_to_all_devices("TODO: Straight-Line Speed Test")
        elif current_challenge == 3: 
           debug.print_to_all_devices("TODO: Minimal Maze")
        elif current_challenge == 4: 
           debug.print_to_all_devices("TODO: Somewhere Over The Rainbow ")
        elif current_challenge == 5: 
           debug.print_to_all_devices("TODO: PiNoon")
        elif current_challenge == 6: 
           os.system('clear') # clear the stout
           current_challenge_thread = the_duck_shoot.Challange(dalek_settings, dalek_sounds)
           current_challenge_thread.start()

        elif current_challenge == 7: 
           tank_drive_on =  True
          #  dalek_settings.in_challange=True
           os.system('clear')
           current_challenge_thread = slightly_deranged_golf.Challange(dalek_settings, dalek_sounds)
           current_challenge_thread.start()

           
           
         
    return 1 # resets ps3_ControllerMode  to Drive Mode
       
 
  def button_start():  
    debug.print_to_all_devices("Start Button Pressed")
  
  def button_PS3(_ps3_ControllerMode):
    nonlocal current_challenge_thread
   
     # # change the controller Mode.
    _ps3_ControllerMode  +=1  
 
    if _ps3_ControllerMode == 1:
      tank_drive_on = True
      os.system('clear')
      debug.print_to_all_devices("You are in Drive Mode" .format(_ps3_ControllerMode),"-D")

    elif _ps3_ControllerMode == 2:
      # debug.print_to_all_devices("is_in_chalange({})".format(dalek_settings.in_challange))
      if current_challenge_thread.running == True:
        debug.print_to_all_devices("Quiting Challange.")
        current_challenge_thread.stop_runnning()
        current_challenge_thread.join() # wait for thread to stop

        # dalek_settings.in_challange = False # end the challange you are in
        debug.print_to_all_devices("Challang has ended")
      # else:
      
      ui.display_selected_challenge(current_challenge)
      tank_drive_on = False 

      
    elif _ps3_ControllerMode == 3:
      tank_drive_on = False
      _ps3_ControllerMode = 0
      os.system('clear')
      debug.print_to_all_devices("You are in Exterminate Mode" .format(_ps3_ControllerMode),"-E")

    return _ps3_ControllerMode

  ###########################################################
  ###  paddle Buttons on the Controller                    ##
  ###########################################################  
  def button_left_paddle():
    debug.print_to_all_devices("Left Paddle Button Pressed")

  def button_right_paddle():
    debug.print_to_all_devices("Right Paddle Button Pressed")

  #####################################################################
  ###                            Main loop                           ##
  ###  this is where we read the data from the joystick file/device  ##
  #####################################################################
  
  while True:
    #read 8 bits from the event buffer.
    evbuf = jsdev.read(8)
    if evbuf:
        time, value, type, number = struct.unpack('IhBB', evbuf)
        
        #  Button pressed event
        if type & 0x01:
          ########################
          # D-Pad button pressed #
          ########################
          if (number >=4 ) and (number <= 7):
            dpad_button_pressed(value,number,joystickD_padCurrentButton )
                      
            #only change current button when it is pressed not released
            if value:
              joystickD_padCurrentButton = number
          #########################
          # All buttons NOT D-pad #
          #########################

          # Select button
          elif number == 0:
            
            if value: # dont increment on release.
              ps3_ControllerMode = button_select(ps3_ControllerMode)
              
           #  Right paddle button
          elif number == 1:
            if value:
              button_right_paddle()

          #  Left Paddle button
          elif number == 2:
            if value:
              button_left_paddle()

          #  Start Paddle button
          elif number == 3:
            if value:
              button_start()

          # L2 button
          elif number == 8:
            if value:
              button_L2()   
          
           # R2 button
          elif number == 9:
            if value:
              button_R2()
  
          # L1 button
          elif number == 10:
            if value:
              button_L1()
          # R1 button
          elif number == 11:
            if value:
              button_R1()

          # triangle button
          elif number == 12:
            if value:
              button_triangle()

          # circle button
          elif number == 13:
            if value:
              button_circle()

          #  Cross button
          elif number == 15:
            if value:
              button_square()
          
          #  Cross button
          elif number == 14:
            if value:
              button_cross()

          #  PS3  button
          elif number == 16:
            if value:
              ps3_ControllerMode = button_PS3(ps3_ControllerMode)
 
         
          else :
            debug.print_to_all_devices("you pressed {}" .format(number))
  
        # Axis movement event
        elif type & 0x02:
          #debug.print_to_all_devices('number{}'.format(number))
          
          
         
          
          #Tank mode
          if tank_drive_on == True:
            
            if number == 1:
               #debug.print_to_all_devices("left side {}  {} ".format(leftPaddle , rightPaddle))
             
               leftPaddle= int( value / 327.67)
               
               tank_drive(leftPaddle , rightPaddle)
              
            
            elif number == 3:
              # debug.print_to_all_devices("right side..")
              rightPaddle= int( value / 327.67)
              tank_drive(leftPaddle , rightPaddle)
  return dalek_settings.speed
 

def main(dalek_settings, dalek_sounds):
  init()
  use(dalek_settings, dalek_sounds)


if __name__ == "__main__":
    debug.debug_on = True
    dalek_settings = settings.Settings()
    dalek_sounds = sound_player.Mp3Player(True) # initialize the sound player
    
    debug.turn_debug_on()                  # use the debug and turn on output 
    debug.set_output_device("scrollphat")  # if left empty then default is just stout 

    GPIO.setmode(GPIO.BOARD)   # Set the GPIO pins as numbering - Also set in drive.py
    GPIO.setwarnings(False)    # Turn GPIO warnings off - CAN ALSO BE Set in drive.py

    drive.init()               # Initialise the software to control the motors
    spi.init()   
    main(dalek_settings, dalek_sounds)