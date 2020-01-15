#!/usr/bin/env python3
# coding=utf-8
# derived from https://github.com/svetlyak40wt/mobile-balance.git

import requests
import re
import json

class BadResponse(Exception):
    def __init__(self, message, response):
        super(BadResponse, self).__init__(message)
        self.response = response

def check_status_code(response, expected_code):
    result_code = response.status_code

    if result_code != expected_code:
        url = response.url
        method = response.request.method

        raise BadResponse(('{method} to {url} resulted '
                           'in {result_code} status code '
                           'instead of {expected_code}').format(
            **locals()),
            response)


def cleanup_phone_number(number):
    number_clean = re.sub(r'\D', '', number)
    if len(number_clean) == 11 and number_clean[0] != '7':
        number_clean = '7{}' + number_clean[1:]
    elif len(number_clean) == 10:
        number_clean = '7{}' + number_clean
    if not re.match(r'^7\d{10}$', number_clean):
        raise ValueError('Incorrect phone number format. Must be 7XXXXXXXXXX')
    return number_clean


def auth(number, password):
    s = requests.Session()
    # API expects phone number in strict international format
    # Only digits: <COUNTRY_CODE><ABC/DEF><PHONE_NUMBER>
    number = cleanup_phone_number(number)

    response = s.get('https://login.tele2.ru/ssotele2/wap/auth/')
    check_status_code(response, 200)

    match = re.search(r'value="(.*?)" name="_csrf"', str(response.content))
    csrf_token = match.group(1)
    if csrf_token is None:
        raise BadResponse('CSRF token not found', response)

    data = dict(pNumber=number, password=password, _csrf=csrf_token, authBy='BY_PASS', rememberMe='true')
    response = s.post(
        'https://login.tele2.ru/ssotele2/wap/auth/submitLoginAndPassword',
        data=data)
    check_status_code(response, 200)
    return s

def get_info(s, number):
    response = s.get('https://my.tele2.ru/api/subscribers/{}/balance'.format(number))
    check_status_code(response, 200)

    amount = response.json().get('data', {}).get('value', None)
    if amount is None:
        raise BadResponse('Unable to get balance amount from JSON', response)
    print("Tel: +" + str(number) + " Balance: " + str(amount))

    response = s.get('https://my.tele2.ru/api/subscribers/{}/services'.format(number))
    check_status_code(response, 200)
    json_data = json.loads(response.text)
#    print(response.text.encode("utf-8"))
    for i, result in enumerate(json_data['data']):
        e = json_data['data'][i]
        if e['status'] == 'CONNECTED':
            nam = str(json_data['data'][i]['name'])
            if e['abonentFee']['amount'] is None:
                 print(nam)
            else:
                 print(nam + " [" + str(e['abonentFee']['amount']) + "]")
    print ("")

s = auth("7xxxxxxxxxx", "password")
get_info(s, "7xxxxxxxxxx")
