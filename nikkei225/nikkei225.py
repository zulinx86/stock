import sys
import csv
import json
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
	data = {}
	for i, stock in enumerate(reader):
		# remove the last line
		if i == 225:
			break

		# get the face value
		faceval = fractions.Fraction(stock['みなし額面'][:-1])

		# get the latest close value
		ticker = yf.Ticker("{}.T".format(stock['コード']))
		val = ticker.history(period='1d')['Close'][-1]
		adj = val * 50.0 / faceval

		# add the adjusted value
		total += adj

		# save data
		data[stock['コード']] = {
			'name': stock['銘柄名'],
			'industry': stock['業種'],
			'sector': stock['セクター'],
			'value': val,
			'adjust': adj
		}

	for code in data:
		data[code]['percent'] = data[code]['adjust'] / total * 100.0

	nikkei225 = total / div	
	data['total'] = total
	data['div'] = div
	data['nikkei225'] = nikkei225

	return data

def save(data):
	text = json.dumps(data, ensure_ascii=False, indent=2)
	with open('{}.json'.format(datetime.date.today()), 'w') as f:
		f.write(text)
	print(text)

if __name__ == '__main__':
	download()
	reader = preprocess()
	data = calc(reader)
	save(data)
