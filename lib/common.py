import config as conf
from config import *
import matplotlib.pyplot as plt
import os
import pandas as pd
import random
import time
import numpy as np

def loadData(fname):
	data = pd.read_csv(fname, header = 0)
	
	return data
	
	
def getParams(args):
	if conf.RANDOM:
		conf.NR_NODES = int(args[1])
		conf.EXP = int(args[2])
		conf.MODEL = int(args[3])
		conf.FULL_COLLISION = bool(int(args[4])) 
		#the following 3 line are used to set the loop cycles for 1 simulation
		print "Nodes:", conf.NR_NODES
	else:
		conf.EXP = int(args[1])
		conf.MODEL = int(args[2])
		conf.FULL_COLLISION = bool(int(args[3]))	
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
	if not conf.FULL_COLLISION:
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
	if not conf.FULL_COLLISION:
			title = "simple"
	else:
		title = ""

	fname = "nodesReport_mod{}_exp{}_{}.csv".format(conf.MODEL, conf.EXP, title)
	
	if not os.path.isfile('out/report/{}'.format(fname)):
		df_new = pd.DataFrame(data, index = [0])
		df_new.to_csv('out/report/{}'.format(fname), index=False)
	else:
		df = pd.read_csv('out/report/{}'.format(fname))
		df_new = pd.DataFrame(data, index=[df.ndim-1])
		df = df.append(df_new, ignore_index = True)
		df.to_csv('out/report/{}'.format(fname), index = False)	
		

class Graph():
	def __init__(self):
		
		self.xmax = BSX + conf.RAY +1
		self.ymax = BSY + conf.RAY +1
		plt.ion()
		
		self.fig, self.ax = plt.subplots()
		if conf.RANDOM:
			plt.suptitle('Placement of {} nodes\nin a range of {}m'.format(
				conf.NR_NODES, 
				conf.RAY
			))
		else:
			plt.suptitle('Placement of nodes\nin a range of {}m'.format(
				conf.RAY
			))
		self.ax.set_xlim(-self.xmax, self.xmax)
		self.ax.set_ylim(-self.ymax, self.ymax)
		self.ax.set_axis_off()
		
		# plot the contour
		x = np.linspace(-conf.RAY, conf.RAY, 100)
		y = np.linspace(-conf.RAY, conf.RAY, 100)
		x, y = np.meshgrid(x,y)
		circ = x**2 + y**2 - conf.RAY**2
		self.ax.contour(x,y,circ,[0] ,colors='k', linestyles = "dashed", linewidths = 1)
		
		# place the base station
		self.ax.plot(BSX,BSY, marker="o", markersize = 5, color = "black")
		self.fig.canvas.flush_events()
    	time.sleep(.0001)
    	
    	
	def add(self, node):
		# place the node
		if not conf.RANDOM:
			self.ax.annotate(str(node.nodeid), (node.x, node.y))
		self.ax.plot(node.x, node.y, marker="o", markersize = 2.5, color = "grey")
		self.fig.canvas.flush_events()
    	time.sleep(.0001)


	def save(self):
		if not os.path.isdir('out/graphics'):
			os.mkdir('out/graphics')
			
		if conf.RANDOM:
			plt.savefig('out/graphics/placement_'+str(conf.NR_NODES))
		else:
			plt.savefig('out/graphics/placement')
		plt.close


