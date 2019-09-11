import os

for model in range(7):
	os.system("python loraGps.py 7 {} 1".format(
		model
	))
