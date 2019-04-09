import requests
import json
import threading
from enum import Enum
from ws4py.client.threadedclient import WebSocketClient
from .config import Config

class SocketIO:
	def __init__(this, config, on_connected = None, on_message = None,
		on_closed = None, on_error = None):
		if not isinstance(config, Config):
			raise ValueError("config must be an object of Config class")
		this._d = this.SocketIO_Private(config, on_connected, on_message, on_closed, on_error)
	
	def on_connected(this, on_connected):
		this._d.connected = on_connected
	
	def on_message(this, on_message):
		this._d.message = on_message
	
	def on_closed(this, on_closed):
		this._d.closed = on_closed
	
	def on_error(this, on_error):
		this._d.error = on_error
	
	def connect(this):
		this._d.connect()
	
	def sid(this):
		return this._d.sid()
	
	def state(this):
		return this._d.state
	
	class SocketIO_Private:
		EIO_OPEN = '0'
		EIO_CLOSE = '1'
		EIO_PING = '2'
		EIO_PONG = '3'
		EIO_MESSAGE = '4'
		EIO_UPGRADE = '5'
		EIO_NOOP = '6'
		SIO_CONNECT = '0'
		SIO_DISCONNECT = '1'
		SIO_EVENT = '2'
		SIO_ACK = '3'
		SIO_ERROR = '4'
		SIO_BINARY_EVENT = '5'
		SIO_BINARY_ACK = '6'
		
		def __init__(this, config, on_connected, on_message, on_closed, on_error):
			this.state = SocketIO.State.DISCONNECTED
			this.config = config
			if on_connected:
				this.connected = on_connected
			if on_message:
				this.message = on_message
			if on_closed:
				this.closed_callback = on_closed
			if on_error:
				this.error = on_error
		
		def ws_opened(this):
			this.ws.send("2probe")
		
		def ws_closed(this, code, reason=None):
			print("WS closed. code={0}, reason={1}"
				.format(code,reason))
		
		def ws_message(this, m):
			m = str(m)
			print("ws_message: {0}".format(m))
			if(m):
				if(m[0] == this.EIO_MESSAGE):
					if(m[1] == "2"):
						this.message(m[2:])
					elif(m[1] == "0"):
						this.state = SocketIO.State.CONNECTED
						this.connected()
					elif(m[1] == "4"):
						this.error(-1,m[2:])
				if(m[0] == this.EIO_PONG):
					if this.state is SocketIO.State.CONNECTING:
						print("got first pong")
						this.ws.send("5")
						this.start_ping()
		
		def ws_unhandled_error(this, error):
			print("WS unhandled error. error={1}"
				.format(error))
		
		def connected(this):
			pass
		
		def message(this, message):
			pass
		
		def closed(this, code, reason=None):
			this.pinger.stop()
			this.closed_callback(code,reason)
		
		def error(this, code, reason=None):
			pass
		
		def connect(this):
			this.state = SocketIO.State.CONNECTING
			resp = requests.request('GET',
				"{0}://{1}:{2}/socket.io/?EIO=3&transport=polling&access_token={3}&agent={4}"
				.format(this.config.protocol(),this.config.host(),
				this.config.port(),this.config.token(),this.config.agent())).text
			loc1 = resp.find("{")
			loc2 = resp.rfind("}")
			this.socketOpt = json.loads(resp[loc1:loc2+1])
			wsProtocol = 'ws' if this.config.protocol() == 'http' else 'wss'
			wsURL = "{0}://{1}:{2}/socket.io/?EUO=3&transport=websocket&\
				sid={3}&access_token={4}&agent={5}".format(
				wsProtocol,this.config.host(),this.config.port(),
				this.socketOpt.get('sid'),this.config.token(),this.config.agent())
			this.ws = SocketIO.WebSocket(wsURL,this.ws_opened,this.ws_closed,
				this.ws_message,this.ws_unhandled_error)
			this.ws.connect()
		
		def sid(this):
			return this.socketOpt.get('sid')
		
		def start_ping(this):
			print("start_ping")
			this.pinger = SocketIO.RepeatTimer(this.socketOpt.get('pingInterval')/1000, this.ping)
			this.pinger.start()
		
		def ping(this):
			this.ws.send("2")
		
		def stop_ping(this):
			this.pinger.stop()
	
	class WebSocket(WebSocketClient):
		def __init__(this, url, opened = None, closed = None,
			received_message = None, unhandled_error = None):
			super().__init__(url)
			if opened:
				this.opened = opened
			if closed:
				this.closed = closed
			if received_message:
				this.received_message = received_message
			if unhandled_error:
				this.unhandled_error = unhandled_error
		
		@property
		def handshake_headers(this):
			headers = WebSocketClient.handshake_headers.fget(this)
			headers = [
				(header, this.host) if header == 'Host' else (header, value)
				for (header, value) in headers
			]
			return headers
	
	class State(Enum):
		DISCONNECTED = 1
		CONNECTING = 2
		CONNECTED = 3
		DISCONNECTING = 4
	
	class RepeatTimer:
		def __init__(this,t,function):
			this.t = t
			this.function = function
			this.isRunning = False
		
		def start(this):
			print("start: {0}".format(this.t))
			if not this.isRunning:
				this.isRunning = True
				this._startTimer()
		
		def stop(this):
			this.thread.cancel()
			this.isRunning = False
		
		def _startTimer(this):
			this.thread = threading.Timer(this.t,this._timeout)
			this.thread.start()
		
		def _timeout(this):
				this.function()
				this._startTimer()
		
		def stop(this):
			this.thread.cancel()
	

