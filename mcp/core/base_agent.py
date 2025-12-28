class BaseAgent:
	def __init__(self, name: str):
		self.name = name

	async def handle(self, *args, **kwargs):
		raise NotImplementedError
