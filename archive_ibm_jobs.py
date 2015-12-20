import os
import sqlite3
import requests
from bs4 import BeautifulSoup
import json

AUTH = 'https://krb-sjobs.brassring.com/TGWebHost/home.aspx?partnerid=26059&siteid=5016'
COUNT = 'https://krb-sjobs.brassring.com/TGWebHost/searchresults.aspx'
SEARCH = 'https://krb-sjobs.brassring.com/TGWebHost/searchresults.aspx'

def get_original_cookies():
	return requests.get(AUTH).cookies

def get_total_count(cookies):
	response = requests.get(COUNT,cookies=cookies)
	soup = BeautifulSoup(response.text)
	inputs = soup.select('input')
	for putin in inputs:
		if putin.has_attr('name'):
			if putin['name'] == 'totalrecords':
				return int(putin['value'].strip())
	
def main():
	database_file = 'careers.db'

	if os.path.isfile(database_file) == False:
		conn = sqlite3.connect(database_file)
		curs = conn.cursor()
		curs.execute('CREATE table ibm (job_id PRIMARY KEY,link,title,country,state,city,date)')
		conn.commit()

	conn = sqlite3.connect(database_file)
	curs = conn.cursor()

	cookies = get_original_cookies()
	total_count = get_total_count(cookies)

	record_start = 1

	while record_start <= total_count:

		print(record_start)
		
		data = {'JobInfo':'%%',
		'recordstart':'%i' % record_start,
		'totalrecords':'%i' % total_count,
		'sortOrder':'DESC',
		'sortField':'LastUpdated',
		'sorting':'',
		'JobSiteInfo':''}

		response = requests.post(SEARCH, cookies=cookies, data=data)
		soup = BeautifulSoup(response.text)
		job_view = json.loads(soup.select('.json_tabledata')[0]['value'])

		for job in job_view:
			try:
				job_id = BeautifulSoup(job['AutoReq']).select('input')[0]['value'].strip()
				link = BeautifulSoup(job['AutoReq']).select('a')[0]['href'].strip()
				title = job['JobTitle'].strip()
				country = job['FORMTEXT2'].strip()
				state = job['FORMTEXT13'].strip()
				city = job['FORMTEXT27'].strip()
				date = BeautifulSoup(job['LastUpdated']).get_text().strip()

				curs.execute('INSERT INTO ibm VALUES (?,?,?,?,?,?,?)', (job_id,link,title,country,state,city,date))
			except sqlite3.IntegrityError as e:
				print('duplicate: %s' % job_id)

		conn.commit()
		record_start += 50

if __name__ == '__main__':
	main()
