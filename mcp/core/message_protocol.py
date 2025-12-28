# Simplified MCP-like message protocol utilities
def make_message(method: str, params: dict, context: dict=None):
	return {"method": method, "params": params, "context": context or {}}
# Message protocol definitions (template)
