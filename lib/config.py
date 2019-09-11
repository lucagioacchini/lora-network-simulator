import numpy as np

# Dynamic
EXP = 7
MODEL = 0
FULL_COLLISION = False
RANDOM = False
NODES = []
MAXDIST = 0
NR_NODES = 0
RAY = 250
# Satic
AVGSENDTIME = 1002000 #ms
SIMTIME = 3.6e+6 #ms
BSX = 0
BSY = 0
PTX = 14.0
GAMMA = 2.08
D0 = 40.0
VAR = 0 # variance ignored for now
LPLD0 = 127.41
GL = 0
HM = 1#m
HB = 200 #m
SEED = 69

SF7 = np.array([7,-126.5,-124.25,-120.75])
SF8 = np.array([8,-127.25,-126.75,-124.0])
SF9 = np.array([9,-131.25,-128.25,-127.5])
SF10 = np.array([10,-132.75,-130.25,-128.75])
SF11 = np.array([11,-134.5,-132.75,-128.75])
SF12 = np.array([12,-133.25,-132.25,-132.25])

SENSI = np.array([SF7,SF8,SF9,SF10,SF11,SF12])

# maximum number of packets the BS can receive at the same time
MAXBSREC = 8

# Transmit consumption in mA from -2 to +17 dBm
TX = [22, 22, 22, 23,                                      # RFO/PA0: -2..1
      24, 24, 24, 25, 25, 25, 25, 26, 31, 32, 34, 35, 44,  # PA_BOOST/PA1: 2..14
      82, 85, 90,                                          # PA_BOOST/PA1: 15..17
      105, 115, 125]                                       # PA_BOOST/PA1+PA2: 18..20
# mA = 90    # current draw for TX = 17 dBm
V = 3.0     # voltage
