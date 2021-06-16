# -*- coding: utf-8 -*-
"""
Created on Wed Jun 16 15:21:32 2021

@author: JamesAnderson
"""

from bs4 import BeautifulSoup
import requests
import csv
import time
import pandas as pd
import datetime

gtmetrix_url = 'https://gtmetrix.com/reports/www.garmin.com/0L8pVUyM/'
agent = {"User-Agent":'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36'}
source = requests.get(gtmetrix_url, headers=agent).text

time.sleep(2)

soup = BeautifulSoup(source,'lxml')


# Report Details

url = soup.find('div',class_='report-details')
url = url.find('h2').text

report_details = soup.find('div',class_='report-details-content')
report_details = report_details.find(("div",{"class":"report-details-info"}))

report_generated = report_details.find('div',class_='report-details-value').text.replace(u'\xa0', u' ').replace(u'\n',u'').rstrip().lstrip()

# converting datetime string to datetime

date = report_generated.split(', ')[1][-2:]
month = report_generated.split(', ')[1][:3]
year = report_generated.split(', ')[2][:4]
time = report_generated.split(' ')[4] + ':00' + report_generated.split(' ')[5]

if int(time.split(':')[0]) < 10:
    time = '0'+time 

def convert24(str1):
    # Checking if last two elements of time
    # is AM and first two elements are 12
    if str1[-2:] == "AM" and str1[:2] == "12":
        return "00" + str1[2:-2]
    # remove the AM    
    elif str1[-2:] == "AM":
        return str1[:-2]
    # Checking if last two elements of time
    # is PM and first two elements are 12   
    elif str1[-2:] == "PM" and str1[:2] == "12":
        return str1[:-2]
    else:
        # add 12 to hours and remove PM
        return str(int(str1[:2]) + 12) + str1[2:8]
       
time = convert24(time)

from datetime import datetime

datetime_object = datetime.strptime(month, "%b")
month = datetime_object.month

if month < 10:
    month = '0'+str(month)
    
if int(date) < 10:
    date = '0'+str(date)
    
date_time_str = date+'/'+month+'/'+year + ' ' + time

report_generated = datetime.strptime(date_time_str, '%d/%m/%Y %H:%M:%S')

server_location = report_details.find('div',class_='report-details-item clear').text.replace(u'\xa0', u' ').replace(u'\n',u'').strip().split(': ')[1]

using = report_details.find('div',class_='report-details-item report-details-browser clear').text.replace(u'\xa0', u' ').replace(u'\n',u'').strip().split(': ')[1]


# Key Metrics

gtmetrix_grade = soup.find('div',class_='report-scores')

grade = gtmetrix_grade.find('div',class_="report-score report-score-grade-gtmetrix")

grade = grade.find('i')
grade = grade.attrs
grade = list(grade.values())
grade = grade[0][0][-1]

performance = gtmetrix_grade.find_all("div",{"report-score"})[1]
performance = performance.find('span',class_='report-score-percent').text

structure = gtmetrix_grade.find_all("div",{"report-score"})[2]
structure = structure.find('span',class_='report-score-percent').text


# Web Vitals

web_vitals = soup.find('div',class_='report-page-details')

lcp = web_vitals.find_all('div',class_='report-web-vital')[0].text.replace(u'\n',u'').replace(u'\xa0', u' ').split('LCP ')[1]

tbt = web_vitals.find_all('div',class_='report-web-vital')[1].text.replace(u'\n',u'').replace(u'\xa0', u' ').split('TBT ')[1]

cls_score = float(web_vitals.find_all('div',class_='report-web-vital')[2].text.replace(u'\n',u'').replace(u'\xa0', u' ').split('CLS ')[1])


# Other Performance Metrics

performance_tab = soup.find('div',{"id":"performance"})

first_contentful_paint = performance_tab.find_all('div',{'class':'report-perf-box report-perf-box-performance'})[0]
first_contentful_paint = first_contentful_paint.find('div',class_='report-perf-box-result-numeric').text

time_to_interactive = performance_tab.find_all('div',{'class':'report-perf-box report-perf-box-performance'})[1]
time_to_interactive = time_to_interactive.find('div',class_='report-perf-box-result-numeric').text

speed_index = performance_tab.find_all('div',{'class':'report-perf-box report-perf-box-performance'})[2]
speed_index = speed_index.find('div',class_='report-perf-box-result-numeric').text



row = [url,report_generated,server_location,using,grade,performance,
       structure,lcp,tbt,cls_score,first_contentful_paint,
       time_to_interactive,speed_index]

data = []
data.append(row)
df1 = pd.DataFrame(data, columns = ['URL','Report Generated','Server Location',
                                   'Using','Grade','Performance','Structure','LCP',
                                   'TBT','CLS','First Contentful Paint',
                                   'Time to Interactive','Speed Index'])

# Structure Table

structure_tab = soup.find('div',{"id":"structure"})

i=0
for tag in structure_tab.find_all('tr',{"class":"rules-row audit-row"}):
    i=i+1

structure_data = []

for i in range(i):
    
    structure_tab = soup.find('div',{"id":"structure"})
    
    table_row = structure_tab.find_all('tr',{'class':'rules-row audit-row'})[i].text
    table_row = table_row.split('\n')
    
    impact = table_row[1]
    audit = table_row[2]
    description = table_row[3]
    
    row_details = structure_tab.find_all('tr',{'class':'rules-row rules-details'})[i].text.split('\n')
    row_details = list(filter(None,row_details))
    row_details = list(filter(lambda str: str.strip(), row_details))
    
    details = row_details[0]
    
    additional_info = ' '.join(row_details[2:])
    
    row_2 = [impact,audit,description,details,additional_info]
    
    structure_data.append(row_2)
    
df2 = pd.DataFrame(structure_data, columns = ['Impact','Audit','Description','Details','Additional Info'])

url_name = url.replace('https://','').replace('www.','').replace('.com','').replace('http://','').split('.')[0].replace('/','')

df1.to_csv(f'GTMetrix_{url_name}_Metrics.csv',index=False)
df2.to_csv(f'GTMetrix_{url_name}_Structure.csv',index=False)