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
 
conn = None
semantic_map = {}
goal = Pose2D()
host = ''
port = 5001
HEADERS = {'content-type': 'application/json'}
rospack = rospkg.RosPack()
dir = rospack.get_path('lu4r_ros_interface')

def listener():
	global semantic_map
	global conn
	motion = Twist()
	rospy.init_node('android_interface', anonymous = True)
	v_joyopad = rospy.Publisher('cmd_vel', Twist, queue_size = 1)
	max_tv = rospy.get_param("~max_tv", 0.6)
	max_rv = rospy.get_param("~max_rv", 0.8)
	port = rospy.get_param("~port", 5001)
	print port
	lu4r_ip = rospy.get_param("~lu4r_ip", '127.0.0.1')
	lu4r_port = rospy.get_param("~lu4r_port", '9090')
	lu4r_url = 'http://' + lu4r_ip + ':' + str(lu4r_port) + '/service/nlu' 
	sem_map = rospy.get_param('~semantic_map','semantic_map.txt')
	entities = open(dir + "/semantic_maps/" + sem_map).read()
	json_string = json.loads(entities)
	print 'Entities into the semantic map:'
	for entity in json_string['entities']:
		semantic_map[entity['type']] = Pose2D()
		semantic_map[entity['type']].x = entity["coordinate"]["x"]
		semantic_map[entity['type']].y = entity["coordinate"]["y"]
		semantic_map[entity['type']].theta = entity["coordinate"]["angle"]
		print '\t' + entity['type']
		print str(semantic_map[entity['type']])
		print
	currentFragment = ''
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	print 'Socket created'
	try:
		s.bind((host, port))
	except socket.error as msg:
		print 'Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
		sys.exit()
	print 'Socket bind complete'
	s.listen(10)
	
	while not rospy.is_shutdown():
		print "Waiting for connection on " + ni.ifaddresses('wlan0')[2][0]['addr'] + ':' + str(port)
		conn, addr = s.accept()
		print 'Connected with ' + addr[0] + ':' + str(addr[1])
		while not rospy.is_shutdown():
			data = conn.recv(512)
			print 'Received: '+data
			if data and not data.isspace():
				if "KEEP_AWAKE" in data:
					data = data.replace("KEEP_AWAKE\n","")
					if len(data) == 0:
						continue
				if '$' in data:
					currentFragment = data[1:-1]
					continue				
				if currentFragment == "HOME":
					continue				
				elif currentFragment == "JOY":
					rho_theta = data.split()
					rho = float(rho_theta[0])
					theta = radians(float(rho_theta[1]))
					motion.linear.x = max_tv * rho * sin(theta)
					motion.angular.z = max_rv * -1 * rho * cos(theta)
					v_joyopad.publish(motion)
				elif currentFragment == "SLU":
					toSend = {'hypo': data, 'entities': entities}
					response = requests.post(lu4r_url, toSend, headers = HEADERS)
					predicates = xdg.find_predicates(response.text)
					#conn.send(predicates+'\r\n')
					print predicates
				else:
					print "Unknown service"
			else:
				print 'Disconnected from ' + addr[0] + ':' + str(addr[1])
				currentFragment = ''
				break
	s.close()

if __name__ == '__main__':
	listener()

