from .config import Config
from socketIO_client import SocketIO
import threading
import requests
import json
import logging

class FXCMRest():
	config = None
	socket = None
	thread = None
	state = "disconnected"
	bearer = ""
	socketReadyEvent = threading.Event()
	
	headers = {
		'User-Agent': 'request',
		'Accept': 'application/json',
		'Content-Type': 'application/x-www-form-urlencoded',
		'Accept-Encoding' : 'identity'
	}
	
	def __init__(self, config):
		if not isinstance(config, Config):
			raise ValueError("config must be an object of Config class")
		else:
			self.config = config
	
	def url(self):
		return "{0}://{1}:{2}".format(
			self.config.protocol(),
			self.config.host(),
			self.config.port()
		)
	
	def getSocket(self):
		return self.socket
	
	def getSocketId(self):
		return self.socket._engineIO_session.id
	
	def onConnect(self, data=''):
		logging.info("connected: {0}".format(data))
		self.headers['Authorization'] = "Bearer {0}{1}".format(self.getSocketId(),self.config.token())
		self.state = "connected"
		self.socketReadyEvent.set()
	
	def onError(self, data=''):
		logging.info("error: {0}".format(data))
		self.state = "error: {0}".format(data)
		self.socketReadyEvent.set()
	
	def onConnectError(self, data=''):
		logging.info("connect_error: {0}".format(data))
		self.state = "connect_error: {0}".format(data)
		self.socketReadyEvent.set()
	
	def onDisconnect(self, data=''):
		logging.info("disconnected: {0}".format(data))
		self.state = "disconnected"
	
	def socketThread(self):
		self.socketReadyEvent.clear()
		self.socket = SocketIO(self.url(), params={'access_token':self.config.token(),'agent':self.config.agent()})
		self.socket.on('connect',self.onConnect)
		self.socket.on('disconnect',self.onDisconnect)
		self.socket.on('connect_error',self.onConnectError)
		self.socket.on('error',self.onError)
		self.socket.wait()
	
	def request(self, method, resource, params = {}):
		req = requests.Request(method, "{0}{1}".format(self.url(),resource), headers=self.headers)
		if method is 'GET':
			req.params = params
		else:
			req.data = params
		prep = requests.Session().prepare_request(req)
		resp = requests.Session().send(prep)
		logging.info("request({0},{1},{2}) response({3}:{4})".format(method,resource,params,resp.status_code,resp.text))
		return resp
	
	def connect(self):
		logging.info("connect()")
		self.thread = threading.Thread(target=self.socketThread)
		self.thread.setDaemon(True)
		self.thread.start()
		self.socketReadyEvent.wait(30)
		return self.status()
	
	def disconnect(self):
		if self.thread:
			self.socket.disconnect()
			self.thread.join(15)
	
	def status(self):
		return self.state
	
	def isConnected(self):
		return self.state == "connected"