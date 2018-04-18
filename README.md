# LoRaSim

This is a modification of an existing LoRaSim found here:
http://www.lancaster.ac.uk/scc/sites/lora/lorasim.html
LoRaSim is a discrete-event simulator based on SimPy for simulating collisions in LoRa networks and to analyse scalability.

In addition to the original simulator, this version has two new features: Model and Random.

-----------------------------
Model
-----------------------------
This feature is referred to the path loss model. The two models used are the Log-
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
        
-----------------------------
Random
-----------------------------
random_placement
    	setting random_placement = 0 user is passing the right position of nodes with
    	a file called "Position.txt". At the end of the simulation in the "Report" 
    	file he can find some info about each node like Position, Distance or Rssi
    	1 	random placement for nodes
    	0 	placement for nodes passed as imput

-----------------------------
Synopsis
-----------------------------
   ./loraDir.py <nodes> <random> <avgsend> <experiment> <simtime> <model>[collision]

-----------------------------
2017 Luca Gioacchini
