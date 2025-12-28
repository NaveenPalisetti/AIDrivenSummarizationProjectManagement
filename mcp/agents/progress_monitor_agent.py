# Simple placeholder progress monitor agent
class ProgressMonitorAgent:
	def __init__(self):
		pass

	def analyze(self, tasks):
		total = len(tasks)
		open_tasks = len([t for t in tasks if t.get('status')!='done'])
		return {'total': total, 'open': open_tasks, 'percent_complete': 0 if total==0 else round((total-open_tasks)/total*100,2)}
