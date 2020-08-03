# LoRaSim
Discrete-event simulator based on SimPy for simulating collisions in LoRa networks and to analyse scalability.  
In addition to the [original simulator](http://www.lancaster.ac.uk/scc/sites/lora/lorasim.html), this version has two new features: Model and Random.

## Synopsis
```./loraSim.py <nodes> <experiment> <model> [random] [collision]```

### Model
This feature is referred to the path loss model. The two models used are the Log-Distance one and the Okumura Hata one. The second dipends on the height of the Base Station ```hb``` and the Mobile Station ```hm``` which are customizable through the ```main``` section.  
The implemented pathloss models are:
* ```0``` set the log-distance model  
* ```1``` set the Okumura-Hata for small and medium-size cities model  
* ```2``` set the Okumura-Hata for metropolitan areas  
* ```3``` set the Okumura-Hata for suburban enviroments  
* ```4``` set the Okumura-Hata for rural areas  
* ```5``` set the 3GPP for suburban macro-cell  
* ```6``` set the 3GPP for metropolitan macro-cell  

### Random
By setting ```random_placement = 0```, the user is passing the right position of nodes with a file called ```Position.txt```. At the end of the simulation in the ```Report``` file he can find some info about each node like Position, Distance or RSSI  
*```1``` random placement for nodes  
*```0``` placement for nodes passed as imput  


##
(c) 2018 Luca Gioacchini
