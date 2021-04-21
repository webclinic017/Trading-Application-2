from datetime import datetime
date = datetime.now()
date = date.replace(hour=0, minute=0,second=0)
date = date.isoformat(' ', 'seconds')
print(date)