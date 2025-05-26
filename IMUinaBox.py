# coding: utf-8
#!python2.7
# IMU data reader 
# Built on the UI and socket module
# classes. This initial version is 
# limited to roll, pitch, and yaw, 
# including temp and humidity. 
# Chipset: 
#	BME280 	: temp,humid,psi
#	FXAS21002 : Gyro
#	FXOS8700: Accel, Magnetometer
#	ADS11...: 16-bit ADC
# Data from IMU sent via UDP from port
# 8888 to 6767 currently hard coded on
# the IMU in a box. 
# TODO:
# 	- watchdog (?) on opening socket
#		* timeout on read
#	- add IMU.will_close() tasks

import logging
import socket,sys
import ui
import time
import console
import os

from numpy import sign, absolute
# for image 
from scene import *
#global to break out of while loop
run = False
#UDP_IP="192.168.1.128"
UDP_PORT=6767

class IMU(ui.View):
	''' Gui gives constant readout of pitch roll yaw temp and humidity of  Johnny-inc IMU in a Box.
	'''
	def __init__(self):
		# Class static variables; initialize rpy for graph non-divide by zero
		self.rpy = (('0.1',(2)),('0.1',(2)),('0.1',(2)),('',(2)),('',(2)),'')
		self.running=False
		self.pitchroll_max=[0.0,0.0]
		self.width,self.height = ui.get_screen_size()
		
		# UI instances
		self.title= ui.Label(frame=(36,6,286,74),bg_color=(.63, .82, .79,0.5),text_color=('black'),font=('Copperplate',40),lines=2 ,text=('Inclinometer'),border_color=('#000000'),border_width=5,border_radius=2,alignment=ui.ALIGN_CENTER)
		
		self.switch_label= ui.TextView(frame=(36,483,260,64),bg_color=None,text_color=('white'),font=('Copperplate',17),text=('   Reverse Pitch\n   and roll'),border_color=('#412190'),border_width=3,border_radius=20,alignment=ui.ALIGN_LEFT,alpha=0.5,selected=(False),editable=False)
		
		self.error= ui.TextView(frame=(36,553,138,44),bg_color=None,text_color=('#ffffff'),font=('Copperplate',15),lines=(1),text=('error placeholder'),alignment=ui.ALIGN_LEFT,selected=(False),editable=(False),flex=('W'))
		
		self.switch1= ui.Switch(frame=(216,500,51,31),bg_color=None)
		#switch value needed to be outside definiton
		self.switch1.value=False
		
		self.category= ui.TextView(frame=(6,147,148,195),bg_color=(.69, .76, .82, 0.5),text_color=('black'),font=('Copperplate',32),lines=(3),text=('Roll:\n\n Pitch:\n\n Yaw:'), border_color=('#412190'),border_width=5,border_radius=2, alignment=ui.ALIGN_CENTER,selected=(False),editable=(False))
		
		self.roll= ui.TextView(frame=(162,147,200,58),bg_color=(.69, .76, .82, 0.5),text_color=('black'),font=('Copperplate',35),lines=(1),text=('Roll Data'),border_color=('#412190'),border_width=5,border_radius=2,alignment=ui.ALIGN_LEFT,selected=(False),editable=(False))
		
		self.pitch= ui.TextView(frame=(162,213,200,58),bg_color=(.69, .76, .82, 0.5),text_color=('black'),font=('Copperplate',35),lines=(1),text=('Pitch Data'),border_color=('#412190'),border_width=5,border_radius=2,alignment=ui.ALIGN_LEFT,selected=(False),editable=(False))
		
		self.yaw= ui.TextView(frame=(162,283,200,58),bg_color=(.69, .76, .82,0.5),text_color=('black'),font=('Copperplate',35),lines=(1),text=('Yaw Data'),border_color=('#412190'),border_width=5,border_radius=2,alignment=ui.ALIGN_LEFT,selected=(False),editable=(False))
		
		self.temp= ui.TextView(frame=(36,424,138,44),bg_color=None,text_color=('#ffffff'),font=('Copperplate',15),lines=(1),text=('Temp C'),alignment=ui.ALIGN_LEFT,selected=(False),editable=(False),flex=('W'))
		
		self.humid= ui.TextView(frame=(189,424,138,44),bg_color=None,text_color=('#ffffff'),font=('Copperplate',15),lines=(1),text=('Humidity %'),alignment=ui.ALIGN_LEFT,selected=(False),editable=(False),flex=('W'))
	
#		print('width',self.width)
		
		self.start= ui.Button(frame=(50,96,self.width-6,32),bg_color=(.78, .78, .78, 0.5), text_color=('#ffffff'), font=('Copperplate',26),lines=(1),title=('    Start Listening    '),border_color=('#ffffff'),border_width=3,border_radius=15,alignment=ui.ALIGN_CENTER,selected=(False),editable=(False),action=(start_action),flex=(''))
		
		self.stop= ui.Button(frame=(50,377,self.width-6,32),bg_color=(.78, .78, .78, 0.5),text_color=('black'),font=('Copperplate',26),lines=(1),title=('    Stop Listening    '),border_color=('#ffffff'),border_width=3,border_radius=15,alignment=ui.ALIGN_CENTER,selected=(False),editable=(False),action=(stop_action),flex=(''))
		
		#add items to the View
		self.add_subview(self.title)
		self.add_subview(self.category)
		self.add_subview(self.roll)
		self.add_subview(self.pitch)
		self.add_subview(self.yaw)
		self.add_subview(self.start)
		self.add_subview(self.stop)
		self.add_subview(self.temp)
		self.add_subview(self.humid)
		self.add_subview(self.switch_label)
		self.add_subview(self.switch1)
		self.add_subview(self.error)
	def normalize(self,data,switch):
		''' Adapt graph of roll (and pitch) to fill entire span; keep track of max val'''
		if (absolute(data)> self.pitchroll_max[switch]):
			self.pitchroll_max[switch]= absolute(data)
			return (sign(data)*100)
		else: 
			return ((data/self.pitchroll_max[switch])*100)
			
	def draw(self):
		'''Called when the view's content needs to be drawn.You can use any of the ui module's drawing functions here to render content into the view's visible rectangle. Do not call this method directly to redraw its content, call set_needs_display().
		'''
		#add pic/etc to the background (must be in local diectory) pics/rects layered in order back to front
		img= ui.Image.named('IMG_8843.JPG')
		img.draw(0, 0, self.width,self.height)

		# variable for switch value true when on. false otherwise
		switch = self.switch1.value
		
		# adjustment for rev pitch roll signs
		roll_sign = -1
		roll = self.rpy[switch][0]
		roll = -(float (roll))
		# Update data: reverse pitch and roll based on switch. 
		self.roll.text=str(-float(self.rpy[switch][0]))
		self.pitch.text=str(self.rpy[not(switch)][0])
		
		# create a yaw variable for heading and graph
		yaw=float(self.rpy[2][0])
		#adjust for negative yaw
		if ((sign(yaw)==-1)):
			yaw += 360
		self.yaw.text=str(yaw)
		
		self.temp.text=(str(self.rpy[3][0])+' C\nInternal Temp')
		self.humid.text=(str(self.rpy[4][0])+' % \nHumidity')	
		
		self.error.text=(self.rpy[5])
		
		# Add graphic for rpy below utilize switch for pitch/roll
		#roll position (162,147,200,58)
		roll= self.normalize(float(self.rpy[switch][0]),switch)
		path_roll = ui.Path.rect(262,147,roll,58)
		ui.set_color('red')
		path_roll.fill()
		
		# Pitch pos: (162,213,200,58)
		pitch= self.normalize(float(self.rpy[not(switch)][0]),not(switch))
		path_pitch = ui.Path.rect(262,213,pitch,58)
		ui.set_color('red')
		path_pitch.fill()
		
		# Yaw position (162,283,200,58)  Yaw —> 360
		path_yaw = ui.Path.rect(162,283,yaw/360*200,58)
		ui.set_color('red')
		path_yaw.fill()
		
	def will_close(self):
		''' This will be called when a presented view is about to be dismissed. Save data here. Close ports etc
		'''
		global run
		run=False
		console.hud_alert('bye bye')
		
#button actions		
def start_action(sender):
	'''Start indefinite readout of rpyth until stop_action is pressed
	'''
	running = True
	#get the root view:
	v = sender.superview
	# change buttons:
	v.start.title= 'Running...'
	v.running=True	
	v.pitchroll_max=[0.1,0.1]
	# ~display() needed to clear fault display for this start attempt
	v.set_needs_display()
	
def stop_action(sender):
	'''Stop reading rpyth and reset readouts to default. 
	'''
	#get the root view:
	v = sender.superview
	# Update the view
	v.running=False
	v.roll.text = 'Roll Data'
	v.pitch.text = 'Pitch Data'
	v.yaw.text = 'Yaw Data'
	v.start.title= 'Start Listening'

def udpRead():
	''' Simple UDP data read method. It is possible to receive data out of order. Currently blocking - i.e. gui halts without connection. 
	todo: get timeout working: DONE: timeoout needed on read
	'''
	try:
		s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
		s.bind(("",6767))
	except:
		print("exception")
		print("fail to open socket")
		s.close()		
		y=('0.0',(2))
		e='socket error'
		return (y,y,y,y,y,e)
		
	# Timeout on first read only; need more graceful exit
	try:
		s.settimeout(3)	
		r=s.recvfrom(10)	
	except :
		print('timeout error')
		s.close()
		e='UDP Read Timeout Error!'
		y=('0.0',(2))
		return (y,y,y,y,y,e)
	p=s.recvfrom(10)
	y=s.recvfrom(10)
	t=s.recvfrom(10)
	h=s.recvfrom(10)
	#clear error
	e=''
	s.close()
	return (r,p,y,t,h,e)

def main():
	console.clear()
	view=IMU()
	view.present('sheet',title_bar_color= (.0, .0, .0, 0.1))
	while (1):
		# Run if 'started' and no 'error' last cycle
		if (view.running and view.rpy[5]==''):
			view.rpy=udpRead()
			#update view gui display
			view.set_needs_display()
			time.sleep(0.1)
		# Error occured: stop 'running' and clear error for next 'start listening'
		elif(view.rpy[5]!=''):
			e=''
			y=('0.0',(2))
			view.rpy = (y,y,y,y,y,e)
			stop_action(view.stop)
		else:
			# Sleep avoids massive battery drain
			time.sleep(0.5)
		if (run==False):
			break
if __name__ == "__main__":
#	global run
	run=True
	main()
	

