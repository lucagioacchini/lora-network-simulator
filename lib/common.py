import config as conf
from config import *
import matplotlib.pyplot as plt
import os
import pandas as pd
import random
import time
import numpy as np

def getParams(args):
	conf.NR_NODES = int(args[1])
	conf.EXP = int(args[2])
	conf.MODEL = int(args[3])
	conf.RANDOM = bool(int(args[4]))
	if len(args) > 5:
		conf.FULL_COLLISION = bool(int(args[5])) 
	#the following 3 line are used to set the loop cycles for 1 simulation
	print "Nodes:", conf.NR_NODES
	print "Random: ", conf.RANDOM
	print "AvgSendTime (exp. distributed):", AVGSENDTIME
	print "Experiment: ", conf.EXP
	print "Simtime: ", SIMTIME
	print "Model: ", conf.MODEL
	print "Full Collision: ", conf.FULL_COLLISION
	
	if not os.path.isdir('out'):
		os.mkdir('out')
		os.mkdir('out/report')
		os.mkdir('out/graphics')


def finalReport(data):	
	if conf.FULL_COLLISION:
		title = "simple"
	else:
		title = ""
	
	fname = "finalReport_{}.csv".format(title)
	
	if not os.path.isfile('out/report/{}'.format(fname)):
		df_new = pd.DataFrame(data, index = [0])
		df_new.to_csv('out/report/{}'.format(fname), index=False)
	else:
		df = pd.read_csv('out/report/{}'.format(fname))
		df_new = pd.DataFrame(data, index=[df.ndim-1])
		df = df.append(df_new, ignore_index = True)
		df.to_csv('out/report/{}'.format(fname),index=False)		

def nodeReport(data):
	if conf.FULL_COLLISION:
			title = "simple"
	else:
		title = ""

	fname = "nodesReport_mod{}_exp{}_{}.csv".format(conf.MODEL, conf.EXP, title)

	if not os.path.isfile('out/report/{}'.format(fname)):
		df_new = pd.DataFrame(data, index = [0])
		df_new.to_csv('out/report/{}'.format(fname))
	else:
		df = pd.read_csv('out/report/{}'.format(fname))
		df_new = pd.DataFrame(data, index=[df.ndim-1])
		df.append(df_new, ignore_index = True)
		df.to_csv('out/report/{}'.format(fname))	

class Graph():
	def __init__(self):
		
		self.xmax = BSX + conf.MAXDIST +1
		self.ymax = BSY + conf.MAXDIST +1
		plt.ion()
		
		self.fig, self.ax = plt.subplots()
		plt.suptitle('Placement of '+str(conf.NR_NODES)+' nodes\nin a range of '+str(int(conf.MAXDIST))+' m')
		self.ax.set_xlim(-self.xmax, self.xmax)
		self.ax.set_ylim(-self.ymax, self.ymax)
		self.ax.set_axis_off()
		
		# plot the contour
		x = np.linspace(-conf.MAXDIST, conf.MAXDIST, 100)
		y = np.linspace(-conf.MAXDIST, conf.MAXDIST, 100)
		x, y = np.meshgrid(x,y)
		circ = x**2 + y**2 - conf.MAXDIST**2
		self.ax.contour(x,y,circ,[0] ,colors='k', linestyles = "dashed", linewidths = 1)
		
		# place the base station
		self.ax.plot(BSX,BSY, marker="o", markersize = 5, color = "black")
		self.fig.canvas.flush_events()
    	time.sleep(.0001)
    	
    	
	def add(self, node):
#		# place the node
		self.ax.plot(node.x, node.y, marker="o", markersize = 2.5, color = "grey")
		self.fig.canvas.flush_events()
    	time.sleep(.0001)


	def save(self):
		if not os.path.isdir('out/graphics'):
			os.mkdir('out/graphics')
			
		plt.savefig('out/graphics/placement_'+str(conf.NR_NODES))
		plt.close


