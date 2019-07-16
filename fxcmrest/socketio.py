import json
import threading
from ws4py.client.threadedclient import WebSocketClient
from ws4py.exc import HandshakeError
from .config import Config
from enum import Enum

class SocketIO:
	def __init__(this, config, on_connected = None, on_message = None,
		on_closed = None, on_error = None):
		if not isinstance(config, Config):
			raise ValueError("config must be an object of Config class")
		this._impl = SocketIO_Private(config, on_connected, on_message, on_closed, on_error)
	
	def on_connected(this, on_connected):
		this._impl.connected_callback = on_connected
	
	def on_message(this, on_message):
		this._impl.message_callback = on_message
	
	def on_closed(this, on_closed):
		this._impl.closed_callback = on_closed
	
	def on_error(this, on_error):
		this._impl.error_callback = on_error
	
	def connect(this):
		this._impl.connect()
	
	def sid(this):
		return this._impl.sid()

class SocketIO_Private:
	class EIO:
		OPEN = '0'
		CLOSE = '1'
		PING = '2'
		PONG = '3'
		MESSAGE = '4'
		UPGRADE = '5'
		NOOP = '6'
	
	class SIO:
		CONNECT = '0'
		DISCONNECT = '1'
		EVENT = '2'
		ACK = '3'
		ERROR = '4'
		BINARY_EVENT = '5'
		BINARY_ACK = '6'
	
	def __init__(this, config, on_connected, on_message, on_closed, on_error):
		this.config = config
		this.connecting = False
		if on_connected:
			this.connected_callback = on_connected
		if on_message:
			this.message_callback = on_message
		if on_closed:
			this.closed_callback = on_closed
		if on_error:
			this.error_callback = on_error
	
	def ws_opened(this):
		pass
	
	def ws_closed(this, code, reason=None):
		this.pinger.close()
		this.closed_callback(code, reason)
	
	def ws_message(this, m):
		m = str(m)
		if(m):
			if(m[0] == this.EIO.MESSAGE):
				if(m[1] == this.SIO.EVENT):
					try:
						message = json.loads(m[2:])
						this.message_callback(message[0],message[1])
					except json._implecoder.JSONDecodeError as e:
						this.error_callback(4001,"Error decoding socket message: {0}".format(e))
				elif(m[1] == this.SIO.CONNECT):
					this.connected_callback()
				elif(m[1] == this.SIO.ERROR):
					this.error_callback(4009,m[2:])
				elif(m[1] == this.SIO.DISCONNECT):
					this.error_callback(4010,"SocketIO got disconnect packet.")
					this.disconnect()
				else:
					this.error_callback(4008,"Got unknown SocketIO packet: {0}".format(m[1]))
			elif(m[0] == this.EIO.PONG):
				this.pinger.pong()
				pass
			elif(m[0] == this.EIO.OPEN):
				try:
					this.socketOpt = json.loads(m[1:])
					this.start_ping()
				except json._implecoder.JSONDecodeError as e:
					this.error_callback(4000,"Error decoding socket options: {0}".format(e))
			else:
				this.error_callback(4007,"Got unknown EngineIO packet: {0}".format(m[0]))
	
	def ws_unhandled_error(this, error):
		this.error_callback(4002,"Websocket library reports unhandled error: {0}".format(error))
	
	def connected_callback(this):
		pass
	
	def message_callback(this, event, message=None):
		pass
	
	def closed_callback(this, code, reason=None):
		pass
	
	def error_callback(this, code, reason=None):
		pass
	
	def connect(this):
		wsProtocol = 'ws' if this.config.protocol() == 'http' else 'wss'
		wsURL = "{0}://{1}:{2}/socket.io/?EIO=3&transport=websocket&access_token={3}&agent={4}".format(
			wsProtocol,this.config.host(),this.config.port(),this.config.token(),this.config.agent())
		this.ws = SocketIO_Private.WebSocket(wsURL,this.ws_opened,this.ws_closed,
			this.ws_message,this.ws_unhandled_error)
		try:
			this.ws.connect()
		except HandshakeError as e:
			this.error_callback(4003, "Websocket handshake error: {0}".format(e))
		except ConnectionRefusedError as e:
			this.error_callback(4004, "Websocket connection refused error")
		except Exception as e:
			this.error_callback(4005, "Websocket other exception error")
	
	def disconnect(this):
		# TODO: only if connected (state machine?)
		this.pinger.close()
		this.ws.close()
	
	def sid(this):
		return this.socketOpt.get('sid')
	
	def start_ping(this):
		this.pinger = SocketIO_Private.Pinger(this.socketOpt.get('pingInterval'),
			this.socketOpt.get('pingTimeout'), this.ping, this.pongTimeout)
		this.pinger.start()
	
	def ping(this):
		this.ws.send("2")
	
	def pongTimeout(this):
		this.error_callback(4006,"Server did not respond to ping. disconnecting")
		this._implisconnect()
	
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
	
	class OnceTimer:
		def __init__(this, timeout, callback):
			this.callback = callback
			this.timeout = timeout
			this.cancelEvent = threading.Event()
			this.cancelEvent.clear()
			this.thread = threading.Thread(target=this.wait, daemon=True)
			this.thread.start()
		
		def __enter__(this):
			return this
		
		def __exit__(this, *err):
			this.cancel()
		
		def wait(this):
			if not this.cancelEvent.wait(this.timeout):
				this.callback()
		
		def cancel(this):
			this.cancelEvent.set()
			this.thread.join()
			this.thread = None
	
	class RepeatTimer:
		def __init__(this,interval,callback):
			this.run = True
			this.startEvent = threading.Event()
			this.stopEvent = threading.Event()
			this.interval = interval
			this.callback = callback
			this.thread = None
		
		def __enter__(this):
			return this
		
		def __exit__(this, *err):
			this.close()
		
		def start(this):
			this.stopEvent.clear()
			this.startEvent.set()
			if this.thread is None:
				this.run = True
				this.thread = threading.Thread(target=this.loop, daemon=True)
				this.thread.start()
		
		def stop(this):
			this.startEvent.clear()
			this.stopEvent.set()
		
		def close(this):
			this.run = False
			this.stopEvent.set()
			this.startEvent.set()
			this.thread.join()
			this.thread = None
		
		def loop(this):
			while this.run:
				this.startEvent.wait()
				if not this.stopEvent.wait(this.interval):
					this.callback()
	
	class Pinger:
		def __init__(this,interval,timeout,pingCallback,timeoutCallback):
			this.run = True
			this.startEvent = threading.Event()
			this.pingEvent = threading.Event()
			this.pongEvent = threading.Event()
			this.interval = interval / 1000
			this.timeout = timeout / 1000
			this.pingCallback = pingCallback
			this.timeoutCallback = timeoutCallback
			this.thread = None
		
		def __enter__(this):
			return this
		
		def __exit__(this, *err):
			this.close()
		
		def start(this):
			if this.thread is None:
				this.pongEvent.clear()
				this.pingEvent.clear()
				this.startEvent.set()
				this.run = True
				this.thread = threading.Thread(target=this.loop, daemon=True, name="SocketIOPinger")
				this.thread.start()
		
		def stop(this):
			this.startEvent.clear()
		
		def close(this):
			this.run = False
			this.startEvent.set()
			this.pingEvent.set()
			this.pongEvent.set()
		
		def loop(this):
			while this.run:
				this.startEvent.wait()
				if not this.pingEvent.wait(this.interval):
					this.pingCallback()
				if not this.pongEvent.wait(this.timeout):
					this.timeoutCallback()
					this.run = False
				else:
					this.pongEvent.clear()
		
		def pong(this):
			this.pongEvent.set()