from .config import Config
from .socketio import SocketIO
import threading
import requests
import json
import logging

class FXCMRest():
	def __init__(self, config):
		if not isinstance(config, Config):
			raise ValueError("config must be an object of Config class")
		else:
			self.config = config
			self.socket = None
			self.thread = None
			self.state = "disconnected"
			self.bearer = ""
			self.socketReadyEvent = threading.Event()
			self.headers = {
				'User-Agent': 'request',
				'Accept': 'application/json',
				'Content-Type': 'application/x-www-form-urlencoded',
				'Accept-Encoding' : 'identity'
			}
	
	def url(self):
		return "{0}://{1}:{2}".format(
			self.config.protocol(),
			self.config.host(),
			self.config.port()
		)
	
	def getSocket(self):
		return self.socket
	
	def getSocketId(self):
		return self.socket.sid()
	
	def onConnected(self):
		logging.info("connected")
		self.headers['Authorization'] = "Bearer {0}{1}".format(
			self.getSocketId(),self.config.token())
		self.state = "connected"
		self.socketReadyEvent.set()
	
	def onError(self, code, reason=''):
		logging.info("error: {0} {1}".format(code, reason))
		self.state = "error: {0} {1}".format(code, reason)
		self.socketReadyEvent.set()
	
	def onDisconnect(self, code, reason=''):
		logging.info("disconnected: {0} {1}".format(code, reason))
		self.state = "disconnected: {0} {1}".format(code, reason)
	
	def onMessage(self, event, message=''):
		logging.info("message: {0}:{1}".format(event,message))
	
	def connect(self):
		logging.info("connect()")
		self.socketReadyEvent.clear()
		self.socket = SocketIO(self.config,
			on_connected = self.onConnected,
			on_message = self.onMessage,
			on_closed = self.onDisconnect,
			on_error = self.onError)
		self.socket.connect()
		self.socketReadyEvent.wait(30)
		return self.status()
	
	def request(self, method, resource, params = {}):
		req = requests.Request(method, "{0}{1}".format(
			self.url(),resource), headers=self.headers)
		if method is 'GET':
			req.params = params
		else:
			req.data = params
		prep = requests.Session().prepare_request(req)
		resp = requests.Session().send(prep)
		logging.info("request({0},{1},{2}) response({3}:{4})".format(
			method,resource,params,resp.status_code,resp.text))
		return resp
	
	def disconnect(self):
		pass # TODO: implement
	
	def status(self):
		return self.state
	
	def isConnected(self):
		return self.state == "connected"
