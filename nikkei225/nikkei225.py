import csv
import sqlite3
import datetime
import fractions
import urllib.request
import yfinance as yf

filename = 'nikkei225.csv'

def download():
	url = 'https://indexes.nikkei.co.jp/nkave/archives/file/nikkei_stock_average_par_value_jp.csv'
	urllib.request.urlretrieve(url, filename)

def preprocess():
	f = open(filename, 'r', encoding='shift-jis')
	header = next(csv.reader(f, delimiter=','))
	reader = csv.DictReader(f, header)
	return reader

def calc(reader):
	total = 0
	div = 27.769 # 2020-12-01

	# ready for sqlite3
	connection = sqlite3.connect('nikkei225.db')
	cursor = connection.cursor()

	today = datetime.date.today()
	cursor.execute('CREATE TABLE IF NOT EXISTS "{}" (code INTEGER PRIMARY KEY, name TEXT, industry TEXT, sector TEXT, value REAL, diff REAL, adjvalue REAL, adjdiff REAL)'.format(today))

	for i, stock in enumerate(reader):
		# remove the last line
		if i == 225:
			break

		# get the face value
		face = fractions.Fraction(stock['みなし額面'][:-1])

		# get the latest close value
		ticker = yf.Ticker("{}.T".format(stock['コード']))
		hist = ticker.history(period='2d')['Close']
		value = hist[1]
		diff = hist[1] - hist[0]
		adjvalue = value * 50.0 / face
		adjdiff = diff * 50.0 / face

		# add the adjusted value
		total += adjvalue

		# save data
		data = {
			'code': stock['コード'],
			'name': stock['銘柄名'], 
			'industry': stock['業種'], 
			'sector': stock['セクター'], 
			'value': value, 
			'diff': diff, 
			'adjvalue': adjvalue, 
			'adjdiff': adjdiff
		}
		print(data)

		cursor.execute('INSERT INTO "{}" VALUES (:code, :name, :industry, :sector, :value, :diff, :adjvalue, :adjdiff)'.format(today), data)

	cursor.execute('CREATE TABLE IF NOT EXISTS summary (date TEXT PRIMARY KEY, total REAL, div REAL, nikkei225 REAL)')
	cursor.execute(
		'INSERT INTO summary VALUES (:date, :total, :div, :nikkei225)',
		{
			'date': str(datetime.date.today()),
			'total': total,
			'div': div,
			'nikkei225': total / div
		}
	)

	# finish sqlite3
	connection.commit()
	connection.close()


if __name__ == '__main__':
	download()
	reader = preprocess()
	calc(reader)
