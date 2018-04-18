#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""
 LoRaSim 0.2.1: simulate collisions in LoRa

 SYNOPSIS:
   ./loraDir.py <nodes> <random> <avgsend> <experiment> <simtime> <model>[collision]
 DESCRIPTION:
    nodes
        number of nodes to simulate
    random_placement
    	setting random_placement = 0 user is passing the right position of nodes with
    	a file called "Position.txt". At the end of the simulation in the "Report" 
    	file he can find some info about each node like Position, Distance or Rssi
    	1 	random placement for nodes
    	0 	placement for nodes passed as imput
    avgsend
        average sending interval in milliseconds
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
    simtime
        total running time in milliseconds
    model
        model is referred to the path loss model. The two models used are the Log-
        Distance one and the Okumura Hata one. The second dipens on the height of 
        the Base Station hb and the Mobile Station hm, so the have to be changed into
        the "main" section.
        0 	set the log-distance model
        1 	set the Okumura-Hata for small and medium-size cities model
        2 	set the Okumura-Hata for metropolitan areas
        3 	set the Okumura-Hata for suburban enviroments
        4 	set the Okumura-Hata for rural areas
        5 	set the 3GPP for suburban macro-cell
        6 	set the 3GPP for metropolitan macro-cell
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
"""

import simpy
import random
import numpy as np
import math
import sys
import matplotlib.pyplot as plt
import os
import time

start_time = time.time()
#flag = 0 -----> stress the system
#flag = 1 -----> single simulation
global flag
flag = 1
# turn on/off graphics
if flag == 1:
	graphics = 1
else:
	graphics = 0
# do the full collision check
full_collision = False

#this function creates a progress bar
def progress(count, total, status=''):
    bar_len = 50
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + ' ' * (bar_len - filled_len)

    sys.stdout.write('[%s] %s%s ...%s\r' % (bar, percents, '%', status))
    sys.stdout.flush() 
    
#################################################################################################################################################

# this is an array with measured values for sensitivity
sf7 = np.array([7,-126.5,-124.25,-120.75])
sf8 = np.array([8,-127.25,-126.75,-124.0])
sf9 = np.array([9,-131.25,-128.25,-127.5])
sf10 = np.array([10,-132.75,-130.25,-128.75])
sf11 = np.array([11,-134.5,-132.75,-128.75])
sf12 = np.array([12,-133.25,-132.25,-132.25])

# check for collisions at base station
def checkcollision(packet):
    col = 0
    processing = 0
    for i in range(0,len(packetsAtBS)):
        if packetsAtBS[i].packet.processed == 1:
            processing = processing + 1
    if (processing > maxBSReceives):
        packet.processed = 0
    else:
        packet.processed = 1
    if packetsAtBS:
        for other in packetsAtBS:
            if other.nodeid != packet.nodeid:
               # simple collision
               if frequencyCollision(packet, other.packet) \
                   and sfCollision(packet, other.packet):
                   if full_collision:
                       if timingCollision(packet, other.packet):
                           c = powerCollision(packet, other.packet)
                           # mark all the collided packets
                           for p in c:
                               p.collided = 1
                               if p == packet:
                                   col = 1
                       else:
                           pass # no timing collision
                   else:
                       packet.collided = 1
                       other.packet.collided = 1
                       col = 1
        return col
    return 0

# frequencyCollision, conditions
#        |f1-f2| <= 120 kHz if f1 or f2 has bw 500
#        |f1-f2| <= 60 kHz if f1 or f2 has bw 250
#        |f1-f2| <= 30 kHz if f1 or f2 has bw 125
def frequencyCollision(p1,p2):
    if (abs(p1.freq-p2.freq)<=120 and (p1.bw==500 or p2.freq==500)):
        return True
    elif (abs(p1.freq-p2.freq)<=60 and (p1.bw==250 or p2.freq==250)):
        return True
    else:
        if (abs(p1.freq-p2.freq)<=30):
            return True
    return False

def sfCollision(p1, p2):
    if p1.sf == p2.sf:
        return True
    return False

def powerCollision(p1, p2):
    powerThreshold = 6 #dB
    #return px as casualty
    if abs(p1.rssi - p2.rssi) < powerThreshold:
        return (p1, p2)
    elif p1.rssi - p2.rssi < powerThreshold:
        return (p1,)
    return (p2,)

def timingCollision(p1, p2):
    # assuming p1 is the freshly arrived packet and this is the last check
    # we've already determined that p1 is a weak packet, so the only
    # way we can win is by being late enough (only the first n - 5 preamble symbols overlap)
    Npream = 8 #assuming 8 preamble symbols
    Tpreamb = 2**p1.sf/(1.0*p1.bw) * (Npream - 5)
    p2_end = p2.addTime + p2.rectime
    p1_cs = env.now + Tpreamb
    if p1_cs < p2_end: # p1 collided with p2 and lost
        return True
    return False

def airtime(sf,cr,pl,bw):
    H = 0        # implicit header disabled (H=0) or not (H=1)
    DE = 0       # low data rate optimization enabled (=1) or not (=0)
    Npream = 8   # number of preamble symbol (12.25  from Utz paper)

    if bw == 125 and sf in [11, 12]: # low data rate optimization 
        DE = 1
    if sf == 6: # can only have implicit header with SF6
        H = 1

    Tsym = (2.0**sf)/bw
    Tpream = (Npream + 4.25)*Tsym
    payloadSymbNB = 8 + max(math.ceil((8.0*pl-4.0*sf+28+16-20*H)/(4.0*(sf-2*DE)))*(cr+4),0)
    Tpayload = payloadSymbNB * Tsym
    return Tpream + Tpayload

#################################################################################################################################################

class myNode_fixed(): #random_placement = False
	def __init__(self, nodeid, bs, period, packetlen, posx, posy):
		self.nodeid = nodeid
		self.period = period
		self.bs = bs
		self.x = posx
		self.y = posy
		global counter
		progress(counter, tot, status='processing')
		counter +=1
		dist_old = np.sqrt((self.x-bsx)**2+(self.y-bsy)**2)
		self.dist = np.sqrt((dist_old)**2+(hb-hm)**2)
		self.packet = myPacket(self.nodeid, packetlen, self.dist)
		self.sent = 0
		
		if flag==1 and random_placement == 0:
			if not os.path.isdir('Report'):
				os.mkdir('Report')
			os.chdir('Report')
			if full_collision == False:
				title = ' Simple'
			else:
				title = ''
			fname = "Report"
			res = "\nNodeid: "+str(self.nodeid)+"\nPosition: {x = "+str(self.x)+"; y = "+str(self.y)+";z = "+str(hm)+"}"+"\nDistance: "+str(self.dist)+"m\nRssi: "+str(self.packet.rssi)+"dBm\nPath Loss Model: "+str(model)+str(title)+"\n\n"
			with open(fname, "a") as myfile:
				myfile.write(res)
			myfile.close()
			os.chdir(main_dir)
               
        # graphics for node
		global graphics
		if (graphics == 1):
			global ax
			ax.add_artist(plt.Circle((self.x, self.y), 1, fill=True, color='grey'))


class myNode_random(): # random_placement = True
	def __init__(self, nodeid, bs, period, packetlen):
		self.nodeid = nodeid
		self.period = period
		self.bs = bs
		self.x = 0
		self.y = 0
	     
		global counter
		progress(counter, tot, status='processing')
		counter += 1
		found = 0
		global nodes
		while (found == 0):
			a = random.random()
			b = random.random()
			if b<a:
				a,b = b,a
			posx = b*maxDist*math.cos(2*math.pi*a/b)+bsx
			posy = b*maxDist*math.sin(2*math.pi*a/b)+bsy
			if len(nodes) > 0:
				for index, n in enumerate(nodes):
					dist = np.sqrt(((abs(n.x-posx))**2)+((abs(n.y-posy))**2))
					if dist >= 10:
						found = 1
						self.x = posx
						self.y = posy
			else:
				self.x = posx
				self.y = posy
				found = 1
		dist_old = np.sqrt((self.x-bsx)*(self.x-bsx)+(self.y-bsy)*(self.y-bsy))
		self.dist = np.sqrt((dist_old)**2+(hb-hm)**2)
		self.packet = myPacket(self.nodeid, packetlen, self.dist)
		self.sent = 0

        # graphics for node
		global graphics
		if (graphics == 1):
			global ax
			ax.add_artist(plt.Circle((self.x, self.y), 1, fill=True, color='grey'))

class myPacket():
    def __init__(self, nodeid, plen, distance):
        global experiment
        global Ptx
        global gamma
        global d0
        global var
        global Lpld0
        global GL
        global hm  #Mobile Station height
        global hb  #Base Station height
        self.nodeid = nodeid
        self.txpow = Ptx
        # randomize configuration values
        self.sf = random.randint(6,12)
        self.cr = random.randint(1,4)
        self.bw = random.choice([125, 250, 500])
        # for certain experiments override these
        if experiment==1 or experiment == 0:
            self.sf = 12
            self.cr = 4
            self.bw = 125
        # for certain experiments override these
        if experiment==2:
            self.sf = 6
            self.cr = 1
            self.bw = 500
        # lorawan
        if experiment == 4:
            self.sf = 12
            self.cr = 1
            self.bw = 125
		# frequencies: lower bound + number of 61 Hz steps
        self.freq = 860000000 + random.randint(0,2622950)
        # for certain experiments override these and
        # choose some random frequences
        if experiment == 1:
            self.freq = random.choice([860000000, 864000000, 868000000])
        else:
            self.freq = 860000000
        
        Prx = self.txpow  ## zero path loss by default
        # Log-Distance Model
        if model == 0: 
            Lpl = Lpld0 + 10*gamma*math.log10(distance/d0)
                
        # Okumura-Hata Model
        elif model>=1 and model<=4:
            #small and medium-size cities
            if model == 1:
                ahm = (1.1*(math.log10(self.freq)-math.log10(1000000))-0.7)*hm - (1.56*(math.log10(self.freq)-math.log10(1000000))-0.8)
                C = 0 
            #metropolitan areas
            elif model == 2:
                if (self.freq <= 200000000):
                    ahm = 8.29*((math.log10(1.54*hm))**2) - 1.1
                elif (self.freq >= 400000000):
                    ahm = 3.2*((math.log10(11.75*hm))**2) - 4.97
                C = 0
            #suburban enviroments
            elif model == 3:
                ahm = (1.1*(math.log10(self.freq)-math.log10(1000000))-0.7)*hm - (1.56*(math.log10(self.freq)-math.log10(1000000))-0.8)
                C = -2*((math.log10(self.freq)-math.log10(28000000))**2) - 5.4
            #rural area
            elif model == 4:
                ahm = (1.1*(math.log10(self.freq)-math.log10(1000000))-0.7)*hm - (1.56*(math.log10(self.freq)-math.log10(1000000))-0.8)
                C = -4.78*((math.log10(self.freq)-math.log10(1000000))**2) + 18.33*(math.log10(self.freq)-math.log10(1000000)) - 40.98
                
            A = 69.55 + 26.16*(math.log10(self.freq)-math.log10(1000000)) - 13.82*math.log(hb) - ahm
            B = 44.9-6.55*math.log10(hb)

            Lpl = A + B*(math.log10(distance)-math.log10(1000)) + C

        # 3GPP Model
        elif model >= 5:
        	# Suburban Macro
        	if model == 5:
        		C = 0  # dB
        	# Urban Macro
        	elif model == 6:
        		C = 3 #dB
        		
        	Lpl = (44.9-6.55*math.log10(hb))*math.log10(distance/1000)+45.5+(35.46-1.1*hm)*(math.log10(self.freq)-math.log10(1000000))-13.82*math.log10(hm)+0.7*hm+C
        	        
        Prx = self.txpow - GL - Lpl	
        if (experiment == 3) or (experiment == 5):
            minairtime = 9999
            minsf = 0
            minbw = 0
            for i in range(0,6):
                for j in range(1,4):
                    if (sensi[i,j] < Prx):
                        self.sf = int(sensi[i,0])
                        if j==1:
                            self.bw = 125
                        elif j==2:
                            self.bw = 250
                        else:
                            self.bw=500
                        at = airtime(self.sf, 1, plen, self.bw)
                        if at < minairtime:
                            minairtime = at
                            minsf = self.sf
                            minbw = self.bw
                            minsensi = sensi[i, j]
            if (minairtime == 9999):
                exit(-1)
            self.rectime = minairtime
            self.sf = minsf
            self.bw = minbw
            self.cr = 1
            if experiment == 5:
                # reduce the txpower if there's room left
                self.txpow = max(2, self.txpow - math.floor(Prx - minsensi))
                Prx = self.txpow - GL - Lpl
                
        # transmission range
        self.transRange = 150
        self.pl = plen
        self.symTime = (2.0**self.sf)/self.bw
        self.arriveTime = 0
        self.rssi = Prx
        self.rectime = airtime(self.sf,self.cr,self.pl,self.bw)
        self.collided = 0
        self.processed = 0

# main discrete event loop, runs for each node
def transmit(env,node):
    while True:
        yield env.timeout(random.expovariate(1.0/float(node.period)))
        node.sent = node.sent + 1
        if (node in packetsAtBS):
                    print "ERROR: packet already in"
        else:
            sensitivity = sensi[node.packet.sf - 7, [125,250,500].index(node.packet.bw) + 1]
            if node.packet.rssi < sensitivity:
                node.packet.lost = True
            else:
                node.packet.lost = False
                if (checkcollision(node.packet)==1):
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
        if node.packet.collided == 0 and not node.packet.lost:
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

#################################################################################################################################################

# MAIN program

counter=1
Ptx = 14
gamma = 2.08
d0 = 40.0
var = 0 # variance ignored for now
Lpld0 = 127.41
GL = 0
hm = 1 #m
hb = 30 #m
 

main_dir = os.getcwd()
# get arguments

# +++for stress the system+++
if flag == 0:    
	if len(sys.argv) >= 7:
		from_val = int(sys.argv[1])
		to_val = int(sys.argv[2])
		step_val = int(sys.argv[3])
		avgSendTime = int(sys.argv[4])
		experiment = int(sys.argv[5])
		simtime = int(sys.argv[6])
		if len(sys.argv) > 7:
			full_collision = bool(int(sys.argv[7]))
		random_placement = True
		print "\n\n\nSimulation Started"
		print "\n\n\n\nFrom ", from_val, "to ", to_val, "with step of ", step_val
		print "AvgSendTime (exp. distributed):",avgSendTime
		print "Experiment: ", experiment
		print "Simtime: ", simtime
		print "\n\n"
	else:
		print "for stress the system"
		print "usage: ./loraDir <min node> <max node> <step> <avgsend> <experiment> <simtime>"
		print "experiment 0 and 1 use 1 frequency only"
		exit(-1)
    
#+++for only one simulation
else:    
	if len(sys.argv) >= 7:
		nrNodes = int(sys.argv[1])
		random_placement = bool(int(sys.argv[2]))
		avgSendTime = int(sys.argv[3])
		experiment = int(sys.argv[4])
		simtime = int(sys.argv[5])
		model = int(sys.argv[6])
		if len(sys.argv) > 7:
			full_collision = bool(int(sys.argv[7])) 
		#the following 3 line are used to set the loop cycles for 1 simulation
		from_val = nrNodes
		to_val = nrNodes + 1
		step_val = 1
		print "Nodes:", nrNodes
		print "Random: ", random
		print "AvgSendTime (exp. distributed):",avgSendTime
		print "Experiment: ", experiment
		print "Simtime: ", simtime
		print "Model: ", model
		print "Full Collision: ", full_collision
		print "\n\n\n"
	else:
		print "usage: ./loraDir <nodes> <random> <avgsend> <experiment> <simtime> <model> [collision]"
		print "experiment 0 and 1 use 1 frequency only"
		exit(-1)

#for the counter
global tot
tot=0
for i in range(from_val, to_val + 1, step_val):
	tot = (tot + i)
if flag ==0:
	tot = tot*14
else:
	tot = nrNodes
dimension = int(((to_val - from_val)/step_val)+1) #for graphics array

for k in range (0,2): # Full Collision
	if flag == 0:
		full_collision = bool(k)
	for x in range(0,7,1): # Model
		w=0
		valgraph = [0]*dimension
		nodegraph = [0]*dimension
		if flag == 0:
			model = x 
		y = from_val
		while(y <= to_val): #Nr Nodes
			nrNodes = y
			nodes = []
			packetsAtBS = []
			env = simpy.Environment()
   	    	# maximum number of packets the BS can receive at the same time
			maxBSReceives = 8
	    
	    	# max distance: 300m in city, 3000 m outside (5 km Utz experiment)
			bsId = 1
			nrCollisions = 0
			nrReceived = 0
			nrProcessed = 0
			nrLost = 0
			sensi = np.array([sf7,sf8,sf9,sf10,sf11,sf12])
			if experiment in [0,1,4]:
				minsensi = sensi[5,2]# 5th row is SF12, 2nd column is BW125
			elif experiment == 2:
				minsensi = -112.0 # no experiments, so value from datasheet
			elif experiment in [3,5]:
				minsensi = np.amin(sensi)#for Experiment 3 take minimum
			Lpl = Ptx - minsensi
			maxDist = d0*(math.e**((Lpl-Lpld0)/(10.0*gamma)))
	    
  	    	# base station placement
			#bsx = maxDist+10
			#bsy = maxDist+10
			bsx = 0
			bsy = 0
			xmax = bsx + maxDist
			ymax = bsy + maxDist
			
			
	    	# prepare graphics and add sink
			if (graphics == 1):
				plt.ion()
				ax = plt.gcf().gca()
				# base station position
				ax.add_artist(plt.Circle((bsx, bsy), 2.5, fill=True, color='black')) # bs
				ax.add_artist(plt.Circle((bsx, bsy), maxDist, fill=False, color='black')) # circle


			if random_placement == False:
				global fp
				with open("Position.txt", "r") as fp:
					for line in fp:
						nodeid, posx, posy = line.split(' ',3)
						nodeid = int(nodeid)
						posx = int(posx)
						posy = int(posy)
						node = myNode_fixed(nodeid, bsId, avgSendTime,20, posx, posy)
						nodes.append(node)
						env.process(transmit(env,node))
			else:
				for i in range(0,nrNodes):
				    node = myNode_random(i,bsId, avgSendTime,20)
				    nodes.append(node)
				    env.process(transmit(env,node))
	        
	        
			# prepare show
			if (graphics == 1):
				plt.xlim([-xmax, xmax])
				plt.ylim([-ymax, ymax])
				plt.suptitle('Placement of '+str(nrNodes)+' nodes\nin a range of '+str(int(maxDist))+' m')
				plt.draw()
	        
   	    	# start simulation
			env.run(until=simtime)
	    
	    	# compute energy and data extraction rate
	    	# Transmit consumption in mA from -2 to +17 dBm
			TX = [22, 22, 22, 23,                                      # RFO/PA0: -2..1
	    	      24, 24, 24, 25, 25, 25, 25, 26, 31, 32, 34, 35, 44,  # PA_BOOST/PA1: 2..14
	    	      82, 85, 90,                                          # PA_BOOST/PA1: 15..17
	    	      105, 115, 125]                                       # PA_BOOST/PA1+PA2: 18..20
	    	# mA = 90    # current draw for TX = 17 dBm
			V = 3.0     # voltage
			sent = sum(n.sent for n in nodes)
			energy = sum(node.packet.rectime * TX[int(node.packet.txpow)+2] * V * node.sent for node in nodes) / 1e6
			der = (sent-nrCollisions)/float(sent)
			der = (nrReceived)/float(sent)
			valgraph[w] = der
			nodegraph[w] = nrNodes
			w += 1
			if flag==1:
				break
			if y==to_val:
				break
			y=y+step_val
		
		# it creates a Report
		if flag==1:
			if not os.path.isdir('Report'):
				os.mkdir('Report')
			os.chdir('Report')
			if full_collision == False:
				title = ' Simple'
			else:
				title = ''
			fname = "Report"
			res = "\n\n*********************************\n\nnrNodes: "+str(nrNodes)+"\nnrCollisions: "+str(nrCollisions)+"\nSent packets: "+str(sent)+"\nPath Loss Model: "+str(model)+str(title)+"\nOverall Energy: "+str(energy)+" J\nDer: "+str(der)+"\n\n*********************************\n"
			with open(fname, "a") as myfile:
				myfile.write(res)
			myfile.close()
			os.chdir(main_dir)
			
		#it creates a Placemente Graphic
		if flag == 1:	
			if not os.path.isdir('Graphics'):
					os.mkdir('Graphics')
			os.chdir('Graphics')
			plt.grid(True)	
			plt.savefig('Placement_'+str(nrNodes))
			plt.close
			os.chdir(main_dir)
		
		# it creates a Graphic
		else:
			if not os.path.isdir('Graphics'):
				os.mkdir('Graphics')
			os.chdir('Graphics')
			plt.plot(nodegraph,valgraph,'k')
			plt.axis([from_val,to_val,0.00,1.01])
			plt.xlabel('Nodes')
			plt.ylabel('Data Extraction Rate')
			plt.grid(True)
			if full_collision == False:
				title = '_Simple'
			else:
				title = ''
			plt.savefig('exp'+str(experiment)+'_mod'+str(model)+title+'.png')
			plt.close()
			os.chdir(main_dir)
		
			if flag == 1:
				break
		if flag == 1:
			break
	if flag == 1:
		break
	
seconds = int(time.time() - start_time)
minutes = int(seconds/60)
hour = int(minutes/60)
seconds = int(seconds - minutes*60)
minutes = int(minutes - hour*60)
print("\n\nSimulation Time: " + str(hour) + ":" + str(minutes) + ":" + str(seconds) + " \n\n\n")		
