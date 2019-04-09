#!/usr/bin/python3
import time
from fxcmrest import FXCMRest, Config

def onMessage(data):
	print(data)

c = Config("demo",token="6062ec8fe48ce501b31951e5e0117a448c721dc7")
r = FXCMRest(c)
print(r.connect())

r.socket.on_message(onMessage)

print(r.request('POST','/subscribe',{'pairs':'EUR/USD'}).json())

input("press Enter")
