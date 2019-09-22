import config as conf
from config import *
import random
import math
import pandas as pd
from scipy.interpolate import UnivariateSpline

random.seed(SEED)

class Packet():
	def __init__(self, nodeid, plen, distance):
		self.nodeid = nodeid
		self.txpow = PTX
		self.dist = distance

		# randomize configuration values
		self.sf = random.randint(6,12)
		self.cr = random.randint(1,4)
		self.bw = random.choice([125, 250, 500])
		# for certain conf.conf.EXPeriments override these
		if conf.EXP == 1 or conf.EXP == 0:
			self.sf = 12
			self.cr = 4
			self.bw = 125
		# for certain conf.conf.EXPeriments override these
		if conf.EXP == 2:
			self.sf = 6
			self.cr = 1
			self.bw = 500
		# lorawan
		if conf.EXP == 4:
			self.sf = 12
			self.cr = 1
			self.bw = 125
		# frequencies: lower bound + number of 61 Hz steps
		self.freq = 860000000 + random.randint(0,2622950)
		# for certain conf.conf.EXPeriments override these and
		# choose some random frequences

		if conf.EXP == 1:
			self.freq = random.choice([860000000, 864000000, 868000000])
		else:
			self.freq = 860000000
		
		# On-field experiment
		if conf.EXP == 7 or conf.EXP == 8 or conf.EXP == 9:
			self.sf = 7
			self.cr = 1
			self.bw = 125
			self.freq = 868000000
			
		Prx = self.txpow  ## zero path loss by default
		Lpl = self.estimatePathLoss()
		Prx = self.txpow - GL - Lpl	
		
		if conf.EXP == 3 or conf.EXP == 5:
			minairtime = 9999
			minsf = 0
			minbw = 0
			for i in range(0,6):
				for j in range(1,4):
					if (SENSI[i,j] < Prx):
						self.sf = int(SENSI[i,0])
						if j==1:
							self.bw = 125
						elif j==2:
							self.bw = 250
						else:
							self.bw=500
						at = self.airtime(self.sf, 1, plen, self.bw)
						if at < minairtime:
							minairtime = at
							minsf = self.sf
							minbw = self.bw
							minsensi = SENSI[i, j]
			if (minairtime == 9999):
				exit()
			self.rectime = minairtime
			self.sf = minsf
			self.bw = minbw
			self.cr = 1
			if conf.EXP == 5:
				# reduce the txpower if there's room left
				self.txpow = max(2, self.txpow - math.floor(Prx - minsensi))
				Prx = self.txpow - GL - Lpl
				
		# transmission range
		self.transRange = 150
		self.pl = plen
		self.symTime = (2.0**self.sf)/self.bw
		self.arriveTime = 0
		self.rssi = Prx
		self.rectime = self.airtime(self.sf,self.cr,self.pl,self.bw)
		self.collided = 0
		self.processed = 0  
	
	def estimatePathLoss(self):	
		# Log-Distance model
		if conf.MODEL == 0: 
			Lpl = LPLD0 + 10*GAMMA*math.log10(self.dist/D0)
				
		# Okumura-Hata model
		elif conf.MODEL >= 1 and conf.MODEL <= 4:
			#small and medium-size cities
			if conf.MODEL == 1:
				ahm = (1.1*(math.log10(self.freq)-math.log10(1000000))-0.7)*HM \
				- (1.56*(math.log10(self.freq)-math.log10(1000000))-0.8)
				
				C = 0 
			#metropolitan areas
			elif conf.MODEL == 2:
				if (self.freq <= 200000000):
					ahm = 8.29*((math.log10(1.54*HM))**2) - 1.1
				elif (self.freq >= 400000000):
					ahm = 3.2*((math.log10(11.75*HM))**2) - 4.97
				C = 0
			#suburban enviroments
			elif conf.MODEL == 3:
				ahm = (1.1*(math.log10(self.freq)-math.log10(1000000))-0.7)*HM \
				- (1.56*(math.log10(self.freq)-math.log10(1000000))-0.8)
				
				C = -2*((math.log10(self.freq)-math.log10(28000000))**2) - 5.4
			#rural area
			elif conf.MODEL == 4:
				ahm = (1.1*(math.log10(self.freq)-math.log10(1000000))-0.7)*HM \
				- (1.56*(math.log10(self.freq)-math.log10(1000000))-0.8)
				
				C = -4.78*((math.log10(self.freq)-math.log10(1000000))**2) \
				+18.33*(math.log10(self.freq)-math.log10(1000000)) - 40.98
				
			A = 69.55 + 26.16*(math.log10(self.freq)-math.log10(1000000)) \
			- 13.82*math.log(HB) - ahm
			
			B = 44.9-6.55*math.log10(HB)

			Lpl = A + B*(math.log10(self.dist)-math.log10(1000)) + C		
			
		# 3GPP model
		elif conf.MODEL >= 5 and conf.MODEL < 7:
			# Suburban Macro
			if conf.MODEL == 5:
				C = 0  # dB
			# Urban Macro
			elif conf.MODEL == 6:
				C = 3 #dB
				
			Lpl = (44.9-6.55*math.log10(HB))*(math.log10(self.dist) - math.log10(1000)) \
			+ 45.5 + (35.46-1.1*HM)*(math.log10(self.freq)-math.log10(1000000)) \
			- 13.82*math.log10(HM)+0.7*HM+C
		
		# Polynomial 3rd degree
		elif conf.MODEL == 7:
			p1 = -5.491e-06
			p2 = 0.002936
			p3 = -0.5004
			p4 = -70.57
			
			Lpl = p1*math.pow(self.dist, 3) + p2*math.pow(self.dist, 2) \
			+ p3*self.dist + p4
		
		# Polynomial 6th degree
		elif conf.MODEL == 8:
			p1 = 3.69e-12
			p2 = 5.997e-11 
			p3 = -1.381e-06 
			p4 = 0.0005134 
			p5 = -0.07318 
			p6 = 4.254 
			p7 = -171  
		
			Lpl = p1*math.pow(self.dist, 6) + p2*math.pow(self.dist, 5) \
			+ p3*math.pow(self.dist, 4) + p4*math.pow(self.dist, 3) \
			+ p5*math.pow(self.dist, 2) + p6*self.dist + p7
			
		return Lpl
		
	def airtime(self, sf,cr,pl,bw):
		H = 0        # implicit header disabled (H=0) or not (H=1)
		DE = 0       # low data rate optimization enabled (=1) or not (=0)
		Npream = 8   # number of preamble symbol (12.25  from Utz paper)

		if bw == 125 and sf in [11, 12]: # low data rate optimization 
			DE = 1
		if sf == 6: # can only have implicit header with SF6
			H = 1

		Tsym = (2.0**sf)/bw
		Tpream = (Npream + 4.25)*Tsym
		payloadSymbNB = 8 + max(math.ceil((8.0*pl-4.0*sf+28+16-20*H)
		/(4.0*(sf-2*DE)))*(cr+4),0)
		
		Tpayload = payloadSymbNB * Tsym
		
		return Tpream + Tpayload	
