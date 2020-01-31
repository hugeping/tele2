#!/usr/bin/env python
# coding=utf-8
# originally derived from https://github.com/svetlyak40wt/mobile-balance.git
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

    data = dict(client_id='digital-suite-web-app', grant_type='password', username=number, password=password, password_type='password')

    response = s.post(
         'https://msk.tele2.ru/auth/realms/tele2-b2c/protocol/openid-connect/token',
         data = data)
    check_status_code(response, 200)
    json_data = json.loads(response.text)
    token = str(json_data['token_type']) + ' ' + str(json_data['access_token'])
    return s, token

def get_info(s, token, number):
    response = s.get('https://my.tele2.ru/api/subscribers/{}/balance'.format(number), headers = {'Authorization': token })
    check_status_code(response, 200)

    amount = response.json().get('data', {}).get('value', None)
    if amount is None:
        raise BadResponse('Unable to get balance amount from JSON', response)
    print("Tel: +" + str(number) + " Balance: " + str(amount))

    response = s.get('https://my.tele2.ru/api/subscribers/{}/services'.format(number), headers = {'Authorization': token })
    check_status_code(response, 200)
    json_data = json.loads(response.text)

    for i, result in enumerate(json_data['data']):
        e = json_data['data'][i]
        if e['status'] == 'CONNECTED':
            nam = str(json_data['data'][i]['name'])
            if e['abonentFee']['amount'] is None:
                 print(nam)
            else:
                 print(nam + " [" + str(e['abonentFee']['amount']) + "]")
    print ("")

s, token = auth("7XXXXXXXXXX", "password")
get_info(s, token, "7XXXXXXXXXX")

s, token = auth("7XXXXXXXXXX", "password")
get_info(s, token, "7XXXXXXXXXX")
get_info(s, token, "7XXXXXXXXXX")
