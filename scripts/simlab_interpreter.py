#!/usr/bin/env python
# encoding=utf8

# encoding=utf8

import rospy
from std_msgs.msg import String
import socket
import sys
import requests
import rospkg
import json
from math import radians, sin, cos
from geometry_msgs.msg import Pose2D
from geometry_msgs.msg import Twist
import xmltodict
import xdg_extract as xdg
import netifaces as ni

reload(sys)
sys.setdefaultencoding('utf8')

goal = Pose2D()
HEADERS = {'content-type': 'application/json'}
rospack = rospkg.RosPack()
directory = rospack.get_path('lu4r_ros_interface')

#Subscriber
sub_interpreter = None
sub_arnl = None

# Publisher (RosARNL)
pub = None

possible_actions = ['ARRIVING',                	# 0
				'ATTACHING',    			   	# 1
				'BEING_IN_CATEGORY',			# 2
				'BEING_LOCATED', 				# 3
				'BRINGING', 					# 4
				'CHANGE_DIRECTION', 			# 5
				'CHANGE_OPERATIONAL_STATE', 	# 6
				'CLOSURE', 						# 7
				'COTHEME', 						# 8
				'GIVING', 						# 9
				'INSPECTING',					# 10
				'LOCATING', 					# 11
				'MANIPULATING', 				# 12
				'MOTION', 						# 13
				'PERCEPTION_ACTIVE',			# 14
				'PLACING', 						# 15
				'RELEASING',					# 16
				'TAKING'						# 17
				]

command_list = []
goals = [
	["Goal0","initial","start","beginning"],
	["Goal1","kitchen","knife","oven","spoon","fork"],
	["Goal2","bathroom","toilet","bath","sink","toothbrush"],
	["Goal3","exit","door","escape"]]


#current_action = ""
isWorking = False

def interpretercallback(data):
	global isWorking

	def getContent():
		return data.data.split('(')[1].split(')')[0]

	print 'Received: ' + data.data
	action = data.data.split('(')[0]
	# content = data.data.split('(')[1].split(')')[0]

	# BRINGING
	# Example of transcription received: BRINGING(beneficiary:"me",theme:"the book")
	# if action == possible_actions[4]:

    # CHANGE_OPERATIONAL_STATE (STOP)
	if action == possible_actions[6]:
		rospy.wait_for_service('/rosarnl_node/stop')
		try:
			stop = rospy.ServiceProxy('/rosarnl_node', stop)
			stop()

		except rospy.ServiceException, e:
			print "Service call failed: %s"%e

	# MOTION
	# Example of transcription received: MOTION(goal:"to the bathroom")
	if action == possible_actions[13]:
		# Getting whole content
		content = getContent()
		content = content.split(":")[1]
		content = content.replace("\"","")
		# Splitting content into words
		content = content.split(" ")

		# Checking if any of the words is a goal
		for word in content:
			index = checkList(word, goals)

			if(index != -1):
				goal = goals[index][0]
				# Giving order to go to the indicated goal if there are no other orders yet.
				if not isWorking:
					print("MOTION: Going to ",goal)
					command_list.append(goal)
			else:
				print("I did not understand you, please repeat.")

	if not isWorking and len(command_list) is not 0:
		isWorking = True
		# Sending work to the arnl node
		pub.publish(command_list.pop()) # Getting First command.

def stateCallback(data):
	print "State: " + data.data
	print("Command_List:")
	print(command_list)
	if(data.data) == "REACHED_GOAL":
		if len(command_list) == 0:
			isWorking = False
			print "Aqui llego"
		else:
			pub.publish(command_list.pop())

def checkList(x,l):
	for elem in l:
		if x in elem:
			return l.index(elem)
	return -1
'''
	for elem in l:
		if elem == x:
			return True
		if isinstance(elem,list):
			return checkList(x,elem)
	return False
'''

def listener():
	global sub_interpreter
	global sub_arnl
	global pub

	rospy.init_node('simlab_interpreter', anonymous=True)
	sub_interpreter = rospy.Subscriber('/interpretation', String, interpretercallback)

	sub_arnl = rospy.Subscriber('/rosarnl_node/arnl_path_state', String, stateCallback)

	pub = rospy.Publisher('/rosarnl_node/goalname',String, queue_size = 1000)





	rospy.spin()

if __name__ == '__main__':
	listener()