from mcp.core.context_handler import ContextHandler
class ContextManagerAgent:
	def __init__(self):
		self.ctx = ContextHandler()
    
	def get_summary(self, meeting_id):
		return self.ctx.get_summary(meeting_id)
