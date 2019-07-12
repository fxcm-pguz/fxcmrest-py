import threading
from .config import Config
from .socketio import SocketIO_Private

class SocketIO_Compat:
	def __init__(this, url, port = None, params = None, wait_for_connection = False, proxies = None):
		if params is None:
			params = {}
		if proxies is None:
			proxies = {}
		config = Config.fromUrl(url=url,port=port,params=params)
		this._impl = SocketIO_Compat_Private(config)
		this._engineIO_session = SocketIO_Compat_Private.EngineIOSession(this._impl)
	
	def wait(this):
		return this._impl.wait()
	
	def connect(this):
		return this._impl.connect()
	
	def on(this, event, callback):
		return this._impl.on(event, callback)
	
	def off(this, event, callback):
		return this._impl.off(event, callback)
	
	def disconnect(this):
		return this._impl.disconnect()
	
	def connected(this):
		return this._impl.connected

class SocketIO_Compat_Private:
	def __init__(this,config):
		this.config = config
		this.events = {}
		this.eventsOnce = {}
		this.disconnectEvent = threading.Event() # TODO: create a state machine for this and move to socketio proper
		this.connected = False # TODO: state machine
		this._sio = SocketIO_Private(config, this.on_connected, this.on_message, this.on_closed, this.on_error)
	
	def on_connected(this):
		this.connected = True
		this.emit('connect')
	
	def on_message(this, event, message):
		this.emit(event, message)
	
	def on_closed(this, code, reason):
		this.connected = False
		this.emit('disconnect',"{0}:{1}".format(str(code),reason))
		this.disconnectEvent.set()
	
	def on_error(this, code, error):
		this.emit('error',"{0}:{1}".format(str(code),error))
	
	def connect(this):
		this.disconnectEvent.clear()
		this._sio.connect()
	
	def wait(this):
		this.connect()
		this.disconnectEvent.wait()
	
	def on(this, event, callback):
		if not event in this.events:
			this.events[event] = []
		this.events[event].append(callback)
	
	def once(this, event, callback):
		if not event in this.eventsOnce:
			this.eventsOnce[event] = []
		this.eventsOnce[event].append(callback)
	
	def off(this, event, callback):
		if event in this.eventsOnce:
			this.eventsOnce[event].remove(callback)
		if event in this.events:
			this.events[event].remove(callback)
	
	def emit(this, event, *args):
		if event in this.eventsOnce:
			for callback in this.eventsOnce.pop(event):
				callback(*args)
		if event in this.events:
			for callback in this.events[event]:
				callback(*args)
	
	def disconnect(this):
		this._sio.disconnect()
		pass
	
	def getId(this):
		return this._sio.sid()
	
	class EngineIOSession:
		def __init__(this, p):
			this._impl = p
		@property
		def id(this):
			return this._impl.getId()
