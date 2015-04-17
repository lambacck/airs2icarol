# this is adapted from the example at the bottom of https://docs.python.org/2/library/csv.html
import csv


class UTF8Reader(object):
	"""
	A CSV reader which will iterate over lines in the CSV file "f",
	which is encoded in the given encoding.
	"""

	def __init__(self, f, dialect=csv.excel, **kwds):
		self.reader = csv.reader(f, dialect=dialect, **kwds)

	def next(self):
		row = self.reader.next()
		return [unicode(s, "utf-8-sig") for s in row]

	def __iter__(self):
		return self


class UTF8CSVWriter(object):
	"""
	A CSV writer which will write rows to CSV file "f",
	which is encoded in the given encoding.
	"""
	def __init__(self, f, dialect=csv.excel, **kwds):
		# Redirect output to a queue
		self.writer = csv.writer(f, dialect=dialect, **kwds)

	def writerow(self, row):
		self.writer.writerow([s.encode("utf-8") for s in row])
		# Fetch UTF-8 output from the queue ...

	def writerows(self, rows):
		for row in rows:
			self.writerow(row)
