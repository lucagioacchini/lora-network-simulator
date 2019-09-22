#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""
 LoRaSim 2.0.1: simulate collisions in LoRa

 SYNOPSIS:
   ./loraSim.py <freq> <experiment> <model> [collision]
 DESCRIPTION:
	nodes
		number of nodes to simulate
	experiment
		experiment is an integer that determines with what radio settings the
		simulation is run. All nodes are configured with a fixed transmit power
		and a single transmit frequency, unless stated otherwise.
		0   use the settings with the the slowest datarate (SF12, BW125, CR4/8).
			It's like SN1 on paper "Do LoRa Low-Power Wide-Area Networks Scale?"
		1   similair to experiment 0, but use a random choice of 3 transmit
			frequencies.
		2   use the settings with the fastest data rate (SF6, BW500, CR4/5).
			It's like SN2 on paper 
		3   optimise the setting per node based on the distance to the gateway.
			It's like SN4 on paper 
		4   use the settings as defined in LoRaWAN (SF12, BW125, CR4/5).
			It's like SN3 on paper 
		5   similair to experiment 3, but also optimises the transmit power.
			It's like SN5 on paper 
		7	use the settings of the onfield measurements at the UnivPM campus
			(SF7, BW125, CR4/5) The frequencies are:
			[ 868.1 868.3 868.5 867.1 867.3 867.5 867.7 867.9 868.8 ]

	model
		model is referred to the path loss model. The two models used are the Log-
		Distance one and the Okumura Hata one. The second dipens on the height of 
		the Base Station HB and the Mobile Station HM, so the have to be changed into
		the "main" section.
		0 	set the log-distance model
		1 	set the Okumura-Hata for small and medium-size cities model
		2 	set the Okumura-Hata for metropolitan areas
		3 	set the Okumura-Hata for suburban enviroments
		4 	set the Okumura-Hata for rural areas
		5 	set the 3GPP for suburban macro-cell
		6 	set the 3GPP for metropolitan macro-cell
	random
		setting random_placement = 0 user is passing the right position of nodes with
		a file called "Position.txt". At the end of the simulation in the "Report" 
		file he can find some info about each node like Position, Distance or Rssi
		1 	random placement for nodes
		0 	placement for nodes passed as input
	collision
		set to 1 to enable the full collision check, 0 to use a simplified check.
		With the simplified check, two messages collide when they arrive at the
		same time, on the same frequency and spreading factor. The full collision
		check considers the 'capture effect', whereby a collision of one or the
 OUTPUT
	The result of every simulation run will be appended to a file named expX.dat,
	whereby X is the experiment number. The file contains a space separated table
	of values for nodes, collisions, transmissions and total energy spent. The
	data file can be easily plotted using e.g. gnuplot.

2019 Luca Gioacchini
"""

import simpy
import random
import numpy as np
import math
import sys
import os
import time
from lib.node import *
import lib.config as conf
from lib.config import *
from lib.common import *
from lib.collision import *

# main discrete event loop, runs for each node
def transmit(env,node):
	"""transmit
	
	Parameters
	----------
		env : simpy.core.environment
		node
	"""
	while True:
		yield env.timeout(random.expovariate(1.0/float(AVGSENDTIME)))
		node.sent = node.sent + 1
		if (node in packetsAtBS):
			print "ERROR: packet already in"
		else:
			sensitivity = SENSI[node.packet.sf - 7, [125,250,500].index(node.packet.bw) + 1]
			if node.packet.rssi < sensitivity:
				node.packet.lost = True
				print "rssi lost"
			else:
				node.packet.lost = False
				if (checkcollision(env, node.packet, packetsAtBS)==1):
					node.packet.collided = 1
				else:
					node.packet.collided = 0
				packetsAtBS.append(node)
				node.packet.addTime = env.now

		yield env.timeout(node.packet.rectime)

		if node.packet.lost:
			global nrLost
			nrLost += 1
		if node.packet.collided == 1:
			global nrCollisions
			nrCollisions = nrCollisions +1
		if not node.packet.collided and not node.packet.lost:
			global nrReceived
			nrReceived = nrReceived + 1
		if node.packet.processed == 1:
			global nrProcessed
			nrProcessed = nrProcessed + 1
		if (node in packetsAtBS):
			packetsAtBS.remove(node)
			# reset the packet
		node.packet.collided = 0
		node.packet.processed = 0
		node.packet.lost = False
			
#=============
#	MAIN
#=============
conf.RANDOM = False
if len(sys.argv) >= 3:
	getParams(sys.argv)	
else:
	print "usage: ./loraGps <experiment> <model> [collision]"
	print "experiment 0 and 1 use 1 frequency only"
	exit()


packetsAtBS = []
env = simpy.Environment()

bsId = 1
nrCollisions = 0
nrReceived = 0
nrProcessed = 0
nrLost = 0

if conf.EXP in [0,1,4]:
	minsensi = SENSI[5,2]# 5th row is SF12, 2nd column is BW125
elif conf.EXP == 2:
	minsensi = -112.0 # no experiments, so value from datasheet
elif conf.EXP in [3,5]:
	minsensi = np.amin(SENSI)#for Experiment 3 take minimum
elif conf.EXP == 7 or conf.EXP == 8:
	minsensi = SENSI[0,2]
	
Lpl = PTX - minsensi
conf.MAXDIST = D0*(math.e**((Lpl-LPLD0)/(10.0*GAMMA)))
graph = Graph()


data = loadData("data/data.csv")
for i in range(len(data)):
	node = fixedNode(
		data["NodeId"][i], 
		bsId,
		20,
		data["x"][i],
		data["y"][i],
		data["Elevation"][i],
		data["Distance"][i]
	)
	graph.add(node)
	conf.NODES.append(node)
	env.process(transmit(env,node))
		
print "[DEBUG INFO]: Nodes created"	

# start simulation
env.run(until=SIMTIME)
print "[DEBUG INFO]: Simulation ended"
# compute energy and data extraction rate
sent = sum(n.sent for n in conf.NODES)
energy = sum(node.packet.rectime * TX[int(node.packet.txpow)+2] * V * node.sent for node in conf.NODES) / 1e6
der = float(sent-nrCollisions)/float(sent)
der = float(nrReceived)/float(sent)

graph.save()
if not conf.RANDOM:
	data = {
		"Nodes":conf.NR_NODES,
		"Collisions":nrCollisions,
		"PktSent":sent,
		"PathLoss":conf.MODEL,
		"Energy":energy,
		"Der":der,
		"Exp":conf.EXP,
	}

	finalReport(data)

