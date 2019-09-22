import config as conf
from packet import *
import random
import math
from common import *

random.seed(SEED)

class RandomNode():
	def __init__(self, nodeid, bs, packetlen):
		self.nodeid = nodeid
		self.bs = bs
		self.x = 0
		self.y = 0
		
		found = False
		while not found:
			a = random.random()
			b = random.random()
			if b<a:
				a,b = b,a
			#posx = b*conf.MAXDIST*math.cos(2*math.pi*a/b)+BSX
			#posy = b*conf.MAXDIST*math.sin(2*math.pi*a/b)+BSY
			posx = b*conf.RAY*math.cos(2*math.pi*a/b)+BSX
			posy = b*conf.RAY*math.sin(2*math.pi*a/b)+BSY
			if len(conf.NODES) > 0:
				for index, n in enumerate(conf.NODES):
					dist = np.sqrt(((abs(n.x-posx))**2)+((abs(n.y-posy))**2))
					if dist >= 10:
						found = 1
						self.x = posx
						self.y = posy
			else:
				self.x = posx
				self.y = posy
				found = True
				
		dist_2d = np.sqrt((self.x-BSX)*(self.x-BSX)+(self.y-BSY)*(self.y-BSY))
		#self.dist = np.sqrt((dist_2d)**2+(HB-HM)**2)
		self.dist = dist_2d
		self.packet = Packet(self.nodeid, packetlen, self.dist)
		self.sent = 0

		
class fixedNode():
	def __init__(self, nodeid, bs, packetlen, posx, posy, h, dist):
		self.nodeid = nodeid
		self.bs = bs
		self.x = posx
		self.y = posy
		self.height = h
		self.dist = dist

		self.packet = Packet(self.nodeid, packetlen, self.dist)
		self.sent = 0
		
		data = {
			"nodeId":self.nodeid,
			"posx":self.x,
			"posy":self.y,
			"posz":self.height,
			"distance":self.dist,
			"rssi":self.packet.rssi,
		}
		
		nodeReport(data)
		
			



