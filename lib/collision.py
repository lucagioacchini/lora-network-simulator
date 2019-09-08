from config import *
import config as conf


def checkcollision(env, packet, at_bs):
	"""Check for collisions at base station
	
	Parameters
	----------
		env : simpy.core.environment
		packet : 
		at_bs : 
	
	Returns
	-------
		col : int
			1 if collision happened
			0 otherwise
	"""
	col = 0
	processing = 0
	for i in range(0,len(at_bs)):
	    if at_bs[i].packet.processed == 1:
	        processing = processing + 1
	if (processing > MAXBSREC):
	    packet.processed = 0
	else:
	    packet.processed = 1
	if at_bs:
	    for other in at_bs:
	        if other.nodeid != packet.nodeid:
	           # simple collision
	           if frequencyCollision(packet, other.packet) \
	               and sfCollision(packet, other.packet):
	               if conf.FULL_COLLISION:
	                   if timingCollision(env, packet, other.packet):
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

def frequencyCollision(p1,p2):
	""" Conditions for frequency collisions:
	|f1-f2| <= 120 kHz if f1 or f2 has bw 500
	|f1-f2| <= 60 kHz if f1 or f2 has bw 250
	|f1-f2| <= 30 kHz if f1 or f2 has bw 125
	
	Parameters
	----------
		p1 :
		p2 :
	
	Returns
	-------
		bool
			True if collisions happened
			False otherwise
	
	"""
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

def timingCollision(env, p1, p2):
	""" assuming p1 is the freshly arrived packet and this is the last check
		we've already determined that p1 is a weak packet, so the only
		way we can win is by being late enough (only the first n - 5 preamble symbols overlap)
	"""
	Npream = 8 #assuming 8 preamble symbols
	Tpreamb = 2**p1.sf/(1.0*p1.bw) * (Npream - 5)
	p2_end = p2.addTime + p2.rectime
	p1_cs = env.now + Tpreamb
	if p1_cs < p2_end: # p1 collided with p2 and lost
	    return True
	return False
