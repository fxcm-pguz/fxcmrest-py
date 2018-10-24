import json

class Config():
	config = {}
	
	def __init__(self, file="", protocol=None, host=None, port=None, token=None, agent=None):
		if(file):
			with open(file, 'r') as f:
				self.config = json.load(f)
		if(protocol):
			self.config['protocol'] = protocol
		if(host):
			self.config['host'] = host
		if(port):
			self.config['port'] = port
		if(token):
			self.config['token'] = token
		if(agent):
			self.config['agent'] = agent
		if not 'protocol' in self.config or self.config['protocol'] not in ["http", "https"]:
			raise Exception("Config Error: Protocol must be either http or https.")
		if not 'host' in self.config or not len(self.config['host']) > 0:
			raise Exception("Config Error: Host not provided")
		if not 'port' in self.config or not 1 <= self.config['port'] <= 65535:
			raise Exception("Config Error: Port must be between 1 and 65535")
		if not 'token' in self.config or len(self.config['token']) != 40:
			raise Exception("Config Error: Token must have a length of 40 characters.")
		if not 'agent' in self.config:
			self.config['agent'] = "fxcmrest"
	
	def protocol(self):
		return self.config['protocol']
	
	def host(self):
		return self.config['host']
	
	def port(self):
		return self.config['port']
	
	def token(self):
		return self.config['token']
	
	def agent(self):
		return self.config['agent']