#!/usr/bin/python
# -*- coding: utf-8 -*-

# /index.py

# Import Library : Part Dialogflow
from flask import Flask, request, jsonify, render_template
import dialogflow
import requests
import json
import ssl #SSL Flask
from flask_sslify import SSLify #SSL Flask
import os

# Import Library : Part Export graph
import time
import datetime
import re
import plotly.graph_objects as go
from pymongo import MongoClient
import pymongo
from bson.json_util import dumps
# Close 
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import plotly.io as pio
pio.orca.config # see the current configuration settings
pio.orca.config.executable = '/usr/local/bin/orca'
pio.orca.config.save()

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = '/home/user01/Chatbot/dialogflow_key.json' # dialogflow_key_data

# =================== Flask web server ===================

# Define flask application
app = Flask(__name__)
# SSL flask
context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
context.load_cert_chain('certinet/xxxxxxxxxxxxx.crt', 'certinet/xxxxxxxxxxxxx.key')
sslify = SSLify(app)

# Send message to onechat
def OneChatNotify(userid, oneid, message):
    try:
        url = 'https://xxxxxxxxxxxxx/message/api/v1/push_message'
        token = 'xxxxxxxxxxxxx'
        headers = {'Authorization': token}

        body = {
        "to" : userid,
        "bot_id" : "xxxxxxxxxxxxx",
        "type" : "text",
        "message" : message,
        }

        r = requests.post(url, headers=headers , data=body)
        # print(r.text)
    except:
        return "can't get token"

# Send onechat quickreply
def OneChatNotify_quickreply(userid, oneid, message_topic, label, message_click, payload):
    url = 'https://xxxxxxxxxxxxx/message/api/v1/push_quickreply'
    token = 'xxxxxxxxxxxxx'
    headers = {'Authorization': token, 'Content-Type': 'application/json'}

    # Send quick reply button to body
    def add_quick_reply_button(label_sub, message_click_sub, payload_sub):
        add = {
        "label" : label_sub,
        "type" : "text",
        "message" : message_click_sub,
        "payload" : payload_sub
      }
        return add

    # Send quick reply date to body
    def add_quick_reply_date(label_sub):
        add = {
        "label" : label_sub,
        "type" : "datepicker",
        "min" : (datetime.datetime.today() - datetime.timedelta(days=365)).strftime('%Y-%m-%d'),
        "initial" : (datetime.datetime.today() - datetime.timedelta(days=1)).strftime('%Y-%m-%d'),
        "max" : (datetime.datetime.today() - datetime.timedelta(days=1)).strftime('%Y-%m-%d'),
        "payload" : "s&edate"
      }
        return add

    body = {
    "to" : userid,
    "bot_id" : "xxxxxxxxxxxxx",
    "message" : message_topic,
    "quick_reply" : []
    }

    count_label = len(label)

    if count_label == 1:
        if label[0] == "กรุณาระบุวันเริ่มต้น":
            label_sub = label[0]
            append_sub_variable = add_quick_reply_date(label_sub)
            body["quick_reply"].append(append_sub_variable)
        elif label[0] == "กรุณาระบุวันสิ้นสุด":
            label_sub = label[0]
            append_sub_variable = add_quick_reply_date(label_sub)
            body["quick_reply"].append(append_sub_variable)       
        else:
            label_sub = label[0]
            message_click_sub = message_click[0]
            payload_sub = payload[0]
            append_sub_variable = add_quick_reply_button(label_sub, message_click_sub, payload_sub)
            body["quick_reply"].append(append_sub_variable)
    elif count_label > 1:
        for label_no in range (count_label):
            label_sub = label[label_no]
            message_click_sub = message_click[label_no]
            payload_sub = payload[label_no]
            append_sub_variable = add_quick_reply_button(label_sub, message_click_sub, payload_sub)
            body["quick_reply"].append(append_sub_variable)
    r = requests.post(url, headers=headers , data=json.dumps(body))
    print(r.text)

# See amonut of VM in CNO
def get_VM_in_cno_and_send_onechat(userid, oneid, cno, project_id):
    
    # Define MongoDB Variable
    Vreal_database_directory = pymongo.MongoClient('localhost', 27017, username='xxxxxxxxxxxxx', password='xxxxxxxxxxxxx')
    vreal_database = Vreal_database_directory["VrealDB"]
    Vreal_collection = vreal_database["VMware_CNO_Collection"]

    myquery = {"CNO" : str(cno)}
    print("myquery : ", myquery)
    Mongo_cnodata = Vreal_collection.find(myquery,{"_id" : 0, "VMname" : 1})
    cno_vm_list = list(Mongo_cnodata)
    count_vm = len(cno_vm_list)
    
    if count_vm >= 1 and count_vm <= 10:
        cut_vmname_key = [vmname["VMname"] for vmname in cno_vm_list]
        message_topic = "กรุณาเลือก VMname ครับ"
        label = cut_vmname_key
        message_click = cut_vmname_key
        payload = cut_vmname_key
        OneChatNotify_quickreply(userid, oneid, message_topic, label, message_click, payload)

    elif count_vm > 10:
        text_vmname = ''
        for vmname in cno_vm_list:
            text_vmname += vmname['VMname'] + '\n'
        
        vm_in_cno_text = "รายชื่อ VM ใน CNO : {0}\n{1}".format(cno,text_vmname)
        OneChatNotify(userid, oneid, vm_in_cno_text)        

    elif myquery['CNO'] == "ไม่มี CNO":
        no_vm = "ไม่มี CNO"
        fulfillment_text = detect_intent_texts(project_id, userid, no_vm, 'en')
        response_text = { "message":  fulfillment_text }
        OneChatNotify(userid, oneid, response_text["message"]) 

    elif count_vm == 0:
        no_vm = "ไม่พบ VM ครับ"
        fulfillment_text = detect_intent_texts(project_id, userid, no_vm, 'en')
        response_text = { "message":  fulfillment_text }
        OneChatNotify(userid, oneid, response_text["message"])   

    Vreal_database_directory.close()

# Get Vreal token from each platform
def get_token(platform):
    try:
        compress_variable_key_to_each_platform = {}
        if "Intel" in platform:
            each_platform_vm_url = "http://xxxxxxxxxxxxx:6100/get_token"
            if platform == 'Intel_dom4':
                fetch_data_from_vm_url = 'https://xxxxxxxxxxxxx/suite-api/api/auth/token/acquire'
                body = {"username": "xxxxxxxxxxxxx", "password": "xxxxxxxxxxxxx", "authSource": "xxxxxxxxxxxxx"}
                headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
        if "HPE" in platform:
            each_platform_vm_url = "http://xxxxxxxxxxxxx:6100/get_token"
            if platform == 'HPE_dom1':
                fetch_data_from_vm_url = 'https://xxxxxxxxxxxxx/suite-api/api/auth/token/acquire'
                body = {"username": "xxxxxxxxxxxxx", "password": "xxxxxxxxxxxxx", "authSource": "xxxxxxxxxxxxx"}
                headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
            elif platform == 'HPE_dom2':
                fetch_data_from_vm_url = 'https://xxxxxxxxxxxxx/suite-api/api/auth/token/acquire'
                body = {"username": "xxxxxxxxxxxxx", "password": "xxxxxxxxxxxxx", "authSource": "xxxxxxxxxxxxx"}
                headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
            elif platform == 'HPE_dom3':
                fetch_data_from_vm_url = 'https://xxxxxxxxxxxxx/suite-api/api/auth/token/acquire'
                body = {"username": "xxxxxxxxxxxxx", "password": "xxxxxxxxxxxxx", "authSource": "xxxxxxxxxxxxx"}
                headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
        if "Flexpod" in platform:    
            print("in flexpod 1")
            each_platform_vm_url = "http://xxxxxxxxxxxxx:6100/get_token"    
            if platform == 'Flexpod_dom1':
                fetch_data_from_vm_url = 'https://xxxxxxxxxxxxx/suite-api/api/auth/token/acquire'
                body = {"username": "xxxxxxxxxxxxx", "password": "xxxxxxxxxxxxx", "authSource": "xxxxxxxxxxxxx"}
                headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
            elif platform == 'Flexpod_dom2':
                fetch_data_from_vm_url = 'https://xxxxxxxxxxxxx/suite-api/api/auth/token/acquire'
                body = {"username": "xxxxxxxxxxxxx", "password": "xxxxxxxxxxxxx", "authSource": "xxxxxxxxxxxxx"}
                headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
            elif platform == 'Flexpod_dom3':
                print("in flexpod_dom3")
                fetch_data_from_vm_url = 'https://xxxxxxxxxxxxx/suite-api/api/auth/token/acquire'
                body = {"username": "xxxxxxxxxxxxx", "password": "xxxxxxxxxxxxx", "authSource": "xxxxxxxxxxxxx"}
                headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
            elif platform == 'Flexpod_Kerry':
                fetch_data_from_vm_url = 'https://xxxxxxxxxxxxx/suite-api/api/auth/token/acquire'
                body = {"username": "xxxxxxxxxxxxx", "password": "xxxxxxxxxxxxx", "authSource": "xxxxxxxxxxxxx"}
                headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
        if "Dell" in platform:
            each_platform_vm_url = "http://xxxxxxxxxxxxx:6100/get_token"
            if platform == 'Dell_dom2':
                fetch_data_from_vm_url = 'https://xxxxxxxxxxxxx/suite-api/api/auth/token/acquire'
                body = {"username": "xxxxxxxxxxxxx", "password": "xxxxxxxxxxxxx", "authSource": "xxxxxxxxxxxxx"}
                headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
            elif platform == 'Dell_dom3_PRD':
                fetch_data_from_vm_url = 'https://xxxxxxxxxxxxx/suite-api/api/auth/token/acquire'
                body = {"username": "xxxxxxxxxxxxx", "password": "xxxxxxxxxxxxx", "authSource": "xxxxxxxxxxxxx"}
                headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
            elif platform == 'Dell_dom3_POC':
                fetch_data_from_vm_url = 'https://xxxxxxxxxxxxx/suite-api/api/auth/token/acquire'
                body = {"username": "xxxxxxxxxxxxx", "password": "xxxxxxxxxxxxx", "authSource": "xxxxxxxxxxxxx"}
                headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
        compress_variable_key_to_each_platform['platform'] = platform
        compress_variable_key_to_each_platform['url'] = fetch_data_from_vm_url
        compress_variable_key_to_each_platform['body'] = body
        compress_variable_key_to_each_platform['header'] = headers

        # print(type(compress_variable_key_to_each_platform))

        x = requests.post(url=each_platform_vm_url, headers=headers, json=compress_variable_key_to_each_platform, verify=False, timeout=20)
        # print("token : ", x.text)
        return x.text
    except:
        return "can't get Token"

# Query metric datas form selected metrics
def query_metrics_resources(token, resourceId, startdate, enddate, platform):
    # Verify parameter
    sdate = datetime.datetime.strptime(startdate, "%Y-%m-%d ").timestamp()*1000 - 43200001
    edate = datetime.datetime.strptime(enddate, "%Y-%m-%d ").timestamp()*1000 - 43200001
    
    dict_sdate_to_edate = []
    sim_sdate = sdate + 43200000
    sim_edate = edate + 43200000
    dict_sdate_to_edate.append(int(sim_sdate))
    while (sim_sdate < sim_edate):
        sim_sdate += 86400000
        dict_sdate_to_edate.append(int(sim_sdate))

    compress_variable_key_to_each_platform = {}
    if "Intel" in platform:
        each_platform_vm_url = "http://xxxxxxxxxxxxx:6100/fetch_data"
        if platform == 'Intel_dom4':
            print("token : ", token)
            fetch_data_from_vm_url = 'https://xxxxxxxxxxxxx/suite-api/api/resources/stats/query'
            headers = {
                "Authorization": token,
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
    elif "HPE" in platform:
        each_platform_vm_url = "http://xxxxxxxxxxxxx:6100/fetch_data"
        if platform == 'HPE_dom1':
            fetch_data_from_vm_url = 'https://xxxxxxxxxxxxx/suite-api/api/resources/stats/query'
            headers = {
                "Authorization": token,
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
        elif platform == 'HPE_dom2':
            fetch_data_from_vm_url = 'https://xxxxxxxxxxxxx/suite-api/api/resources/stats/query'
            headers = {
                "Authorization": token,
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
        elif platform == 'HPE_dom3':
            fetch_data_from_vm_url = 'https://xxxxxxxxxxxxx/suite-api/api/resources/stats/query'
            headers = {
                "Authorization": token,
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
    elif "Flexpod" in platform:
        each_platform_vm_url = "http://xxxxxxxxxxxxx:6100/fetch_data" 
        if platform == 'Flexpod_dom1':
            fetch_data_from_vm_url = 'https://xxxxxxxxxxxxx/suite-api/api/resources/stats/query'
            headers = {
                "Authorization": token,
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
        elif platform == 'Flexpod_dom2':
            fetch_data_from_vm_url = 'https://xxxxxxxxxxxxx/suite-api/api/resources/stats/query'
            headers = {
                "Authorization": token,
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
        elif platform == 'Flexpod_dom3':
            fetch_data_from_vm_url = 'https://xxxxxxxxxxxxx/suite-api/api/resources/stats/query'
            headers = {
                "Authorization": token,
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
        elif platform == 'Flexpod_Kerry':
            fetch_data_from_vm_url = 'https://xxxxxxxxxxxxx/suite-api/api/resources/stats/query'
            headers = {
                "Authorization": token,
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
    elif "Dell" in platform:
        each_platform_vm_url = "http://xxxxxxxxxxxxx:6100/fetch_data"
        if platform == 'Dell_dom2':
            fetch_data_from_vm_url = 'https://xxxxxxxxxxxxx/suite-api/api/resources/stats/query'
            headers = {
                "Authorization": token,
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
        elif platform == 'Dell_dom3_PRD':
            fetch_data_from_vm_url = 'https://xxxxxxxxxxxxx/suite-api/api/resources/stats/query'
            headers = {
                "Authorization": token,
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
        elif platform == 'Dell_dom3_POC':
            fetch_data_from_vm_url = 'https://xxxxxxxxxxxxx/suite-api/api/resources/stats/query'
            headers = {
                "Authorization": token,
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
    body = {
        "begin": sdate,
        "end": edate,
        "intervalType": "DAYS",
        "intervalQuantifier": 1,
        "rollUpType": "AVG",
        "resourceId": resourceId,
        "statKey": [
            # "disk|usage_average"
            # # "net|usage_average"
            # "guestfilesystem|utilization"
            # "cpu|workload",
            # "mem|workload",
            "cpu|usage_average",
            "mem|usage_average",
            "guestfilesystem|percentage",
            # "net|usage_average"
            ]
    }

    compress_variable_key_to_each_platform['platform'] = platform
    compress_variable_key_to_each_platform['url'] = fetch_data_from_vm_url
    compress_variable_key_to_each_platform['body'] = body
    compress_variable_key_to_each_platform['header'] = headers

    # print("compress_variable_key_to_each_platform : ", compress_variable_key_to_each_platform)
    x = requests.post(url=each_platform_vm_url, headers=compress_variable_key_to_each_platform['header'], json=compress_variable_key_to_each_platform, verify=False)
    payload = json.loads(x.text)
    # print(payload)

    # Path for search data
    vreal_graph_data = {}
    vreal_graph_no_data = {}
    # print("payload : ",payload)

    try:
        for i in range (len(payload['values'][0]['stat-list']['stat'])):
            path_statKey =  payload['values'][0]['stat-list']['stat'][i]['statKey']['key']
            if re.search("cpu", path_statKey):
                vreal_graph_data["cpu"] = [{
                'path_statKey' : path_statKey,
                'data' : payload['values'][0]['stat-list']['stat'][i]['data'],
                'timestamp' : [datetime.datetime.fromtimestamp(i/1000) for i in (payload['values'][0]['stat-list']['stat'][0]['timestamps'])]
                }]

                vreal_graph_no_data["nodata_cpu"] = [{
                'path_statKey' : path_statKey,
                'data' : [],
                'timestamp' : []
                }]

                # change data digit to .2f
                vreal_graph_data["cpu"][0]['data'] = [ round(elem, 2) for elem in vreal_graph_data["cpu"][0]['data']]

                for j in dict_sdate_to_edate:
                    if j not in payload['values'][0]['stat-list']['stat'][i]['timestamps']:                    
                        vreal_graph_no_data["nodata_cpu"][0]["data"].append(None)
                        vreal_graph_no_data["nodata_cpu"][0]["timestamp"].append(j)
                
                for no_timestamp in vreal_graph_no_data["nodata_cpu"][0]['timestamp']:
                    vreal_graph_data["cpu"][0]['timestamp'].append(datetime.datetime.fromtimestamp(no_timestamp/1000))
                    index_timestamp = vreal_graph_data["cpu"][0]['timestamp'].index(datetime.datetime.fromtimestamp(no_timestamp/1000))

                vreal_graph_data["cpu"][0]['timestamp'] = sorted(vreal_graph_data["cpu"][0]['timestamp'])  
                
                for data_no_timestamp in vreal_graph_no_data["nodata_cpu"][0]['timestamp']:
                    index_data_no_timestamp = vreal_graph_data["cpu"][0]['timestamp'].index(datetime.datetime.fromtimestamp(data_no_timestamp/1000))
                    # vreal_graph_data["cpu"][0]['data'][index_data_no_timestamp].append(None)
                    vreal_graph_data["cpu"][0]['data'][index_data_no_timestamp:index_data_no_timestamp] = [None]

            if re.search("mem", path_statKey):
                vreal_graph_data["mem"] = [{
                'path_statKey' : path_statKey,
                'data' : payload['values'][0]['stat-list']['stat'][i]['data'],
                'timestamp' : [datetime.datetime.fromtimestamp(i/1000) for i in (payload['values'][0]['stat-list']['stat'][0]['timestamps'])]
                }]

                vreal_graph_no_data["nodata_mem"] = [{
                'path_statKey' : path_statKey,
                'data' : [],
                'timestamp' : []
                }]

                # change data digit to .2f
                vreal_graph_data["mem"][0]['data'] = [ round(elem, 2) for elem in vreal_graph_data["mem"][0]['data']]

                for j in dict_sdate_to_edate:
                    if j not in payload['values'][0]['stat-list']['stat'][i]['timestamps']:                    
                        vreal_graph_no_data["nodata_mem"][0]["data"].append(None)
                        vreal_graph_no_data["nodata_mem"][0]["timestamp"].append(j)
                
                for no_timestamp in vreal_graph_no_data["nodata_mem"][0]['timestamp']:
                    vreal_graph_data["mem"][0]['timestamp'].append(datetime.datetime.fromtimestamp(no_timestamp/1000))
                    index_timestamp = vreal_graph_data["mem"][0]['timestamp'].index(datetime.datetime.fromtimestamp(no_timestamp/1000))

                vreal_graph_data["mem"][0]['timestamp'] = sorted(vreal_graph_data["mem"][0]['timestamp'])  
                
                for data_no_timestamp in vreal_graph_no_data["nodata_mem"][0]['timestamp']:
                    index_data_no_timestamp = vreal_graph_data["mem"][0]['timestamp'].index(datetime.datetime.fromtimestamp(data_no_timestamp/1000))
                    vreal_graph_data["mem"][0]['data'][index_data_no_timestamp:index_data_no_timestamp] = [None]

            if re.search("guestfilesystem", path_statKey):
                # Many disk
                if "disk" in vreal_graph_data:
                    vreal_graph_data["disk"].append({
                    'path_statKey' : path_statKey,
                    'data' : payload['values'][0]['stat-list']['stat'][i]['data'],
                    'timestamp' : [datetime.datetime.fromtimestamp(i/1000) for i in (payload['values'][0]['stat-list']['stat'][0]['timestamps'])]
                    })

                    vreal_graph_no_data["nodata_disk"].append({
                    'path_statKey' : path_statKey,
                    'data' : [],
                    'timestamp' : []
                    })

                    count_disk = len(vreal_graph_no_data["nodata_disk"]) - 1 

                    # change data digit to .2f
                    vreal_graph_data["disk"][count_disk]['data'] = [ round(elem, 2) for elem in vreal_graph_data["disk"][count_disk]['data']]

                    
                    for j in dict_sdate_to_edate:
                        if j not in payload['values'][0]['stat-list']['stat'][i]['timestamps']:                    
                            vreal_graph_no_data["nodata_disk"][count_disk]["data"].append(None)
                            vreal_graph_no_data["nodata_disk"][count_disk]["timestamp"].append(j)
                    
                    for no_timestamp in vreal_graph_no_data["nodata_disk"][count_disk]['timestamp']:
                        vreal_graph_data["disk"][count_disk]['timestamp'].append(datetime.datetime.fromtimestamp(no_timestamp/1000))
                        index_timestamp = vreal_graph_data["disk"][count_disk]['timestamp'].index(datetime.datetime.fromtimestamp(no_timestamp/1000))

                    vreal_graph_data["disk"][count_disk]['timestamp'] = sorted(vreal_graph_data["disk"][count_disk]['timestamp'])  
                    
                    for data_no_timestamp in vreal_graph_no_data["nodata_disk"][count_disk]['timestamp']:
                        index_data_no_timestamp = vreal_graph_data["disk"][count_disk]['timestamp'].index(datetime.datetime.fromtimestamp(data_no_timestamp/1000))
                        vreal_graph_data["disk"][count_disk]['data'][index_data_no_timestamp:index_data_no_timestamp] = [None]

                # Only one disk
                else:
                    vreal_graph_data["disk"] = [{
                    'path_statKey' : path_statKey,
                    'data' : payload['values'][0]['stat-list']['stat'][i]['data'],
                    'timestamp' : [datetime.datetime.fromtimestamp(i/1000) for i in (payload['values'][0]['stat-list']['stat'][0]['timestamps'])]
                    }]

                    vreal_graph_no_data["nodata_disk"] = [{
                    'path_statKey' : path_statKey,
                    'data' : [],
                    'timestamp' : []
                    }]

                    # change data digit to .2f
                    vreal_graph_data["disk"][0]['data'] = [ round(elem, 2) for elem in vreal_graph_data["disk"][0]['data']]

                    for j in dict_sdate_to_edate:
                        if j not in payload['values'][0]['stat-list']['stat'][i]['timestamps']:                    
                            vreal_graph_no_data["nodata_disk"][0]["data"].append(None)
                            vreal_graph_no_data["nodata_disk"][0]["timestamp"].append(j)
                    
                    for no_timestamp in vreal_graph_no_data["nodata_disk"][0]['timestamp']:
                        vreal_graph_data["disk"][0]['timestamp'].append(datetime.datetime.fromtimestamp(no_timestamp/1000))
                        index_timestamp = vreal_graph_data["disk"][0]['timestamp'].index(datetime.datetime.fromtimestamp(no_timestamp/1000))

                    vreal_graph_data["disk"][0]['timestamp'] = sorted(vreal_graph_data["disk"][0]['timestamp'])  
                    
                    for data_no_timestamp in vreal_graph_no_data["nodata_disk"][0]['timestamp']:
                        index_data_no_timestamp = vreal_graph_data["disk"][0]['timestamp'].index(datetime.datetime.fromtimestamp(data_no_timestamp/1000))
                        vreal_graph_data["disk"][0]['data'][index_data_no_timestamp:index_data_no_timestamp] = [None]
                    
        # print(vreal_graph_data['disk'])
        return vreal_graph_data
    except:
        return "vreal_graph_no data"

# Export data to stream picture
def export_pic(vreal_graph_data):
    try:
        keep_byte_image = []
        count_disk = len(vreal_graph_data['disk'])
        count_sensor = len(vreal_graph_data) + count_disk
        for key in (vreal_graph_data).keys():
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=vreal_graph_data[key][0]['timestamp'], y=vreal_graph_data[key][0]['data'],
                            mode='lines+markers',
                            name='line name'))
            fig.update_layout(
                title = {
                'text' : "{}".format(vreal_graph_data[key][0]['path_statKey']),
                'y':0.9,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top'
                },
                xaxis_title="Date",
                yaxis_title="Data (%)"
            )
            # fig.show()
            # Change picture data to bit data
            img_bytes = fig.to_image(format="png")
            keep_byte_image.append(img_bytes)
            
            # print(key)
            # fig.write_image("C:/Users/Khanoon/travel_assistance/picture/{}.png".format(key))
            print(key, " image is exported")
        for i in range(1,count_disk):
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=vreal_graph_data['disk'][i]['timestamp'], y=vreal_graph_data['disk'][i]['data'],
                            mode='lines+markers',
                            name='lines+markers'))
            # print(i)
            disk_split_title = vreal_graph_data['disk'][i]['path_statKey'].split('.')[0]
            # print("disk_split_title : ", disk_split_title)
            fig.update_layout(
                title = {
                'text' : "{}".format(disk_split_title),
                'y':0.9,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top'
                },
                xaxis_title="Date",
                yaxis_title="Data (%)"
            )
            
            # fig.show()
            # Change picture data to bit data
            img_bytes = fig.to_image(format="png")
            keep_byte_image.append(img_bytes)

            # fig.write_image("C:/Users/xxxxxxxxxxxxx/xxxxxxxxxxxxx/picture/disk{}.png".format(i+1))
            
            print("disk {} image is exported".format(i+1))
        return count_sensor,count_disk, keep_byte_image

    except:
        count_sensor = ""
        count_disk = ""
        keep_byte_image = ""
        return count_sensor,count_disk, keep_byte_image

# Send picture to Onechat
def send_picture_to_onechat(user_id, oneid, keep_byte_image):
    
    url = "https://xxxxxxxxxxxxx/message/api/v1/push_message"
    bot_id = "xxxxxxxxxxxxx"
    Authorization = "xxxxxxxxxxxxx"
    headers = {'Authorization':Authorization}
    msg = {"to" : oneid,"bot_id" : bot_id,"type" : "file"}
    
    # Want to show  CPU graph first
    files = [('file',('fig1.png',keep_byte_image[2],'image/png'))]
    r = requests.request("POST",url, headers=headers, files=files, data = msg)

    # Show mem and disk graph
    for count_byte_image in [x for x in range(len(keep_byte_image)) if x != 2]:
        # print(count_byte_image)
        files = [('file',('fig1.png',keep_byte_image[count_byte_image],'image/png'))]
        r = requests.request("POST",url, headers=headers, files=files, data = msg)
        # print(r.text)
    
# Change VMname to UUID
def change_vmname_to_UUID(vm_name):
    Vreal_database_directory = pymongo.MongoClient('localhost', 27017, username='user01', password='mis@Pass01')
    Vreal_database = Vreal_database_directory["VrealDB"]
    Vreal_collection = Vreal_database["All_platform__VMdata_Collection"]

    # print("vmname : ", vm_name)
    myquery = {'resourceKey.name' : vm_name}
    Mongo_Vmdata = Vreal_collection.find_one(myquery, {"resourceKey.name" : 1, 'platform' : 1, "identifier" : 1})
    # print("Mongo_Vmdata : ",Mongo_Vmdata)

    resourceId = Mongo_Vmdata['identifier']
    platform = Mongo_Vmdata['platform']
    
    Vreal_database_directory.close()

    return [resourceId], platform
    
# End Point reply to dialog flow
@app.route('/onechat', methods=['POST'])
def send_message():
    data = request.get_json(silent=True)
    
    # Filter data
    message = data['message']['text']
    userid = data['source']['user_id']
    oneid = data['source']['one_id']
    
    project_id = "line-bot-vrealize-woom"
    fulfillment_text = detect_intent_texts(project_id, userid, message, 'en')
    # print("fulfillment_text /send_message : ", fulfillment_text)         
    response_text = { "message":  fulfillment_text }
    # print("response_text : ", response_text)

    if "CNO :" in fulfillment_text:
        cno = fulfillment_text.split('CNO : ')[1]
        vm_in_cno_text = get_VM_in_cno_and_send_onechat(userid, oneid, cno, project_id)
    
    elif fulfillment_text == "ต้องการสอบถามข้อมูลด้านใดครับ":
        message_topic = "ต้องการสอบถามข้อมูลด้านใดครับ"
        label = ["Performance"]
        message_click = ["ฉันต้องการสอบถาม performance"]
        payload = ["vreal"]
        OneChatNotify_quickreply(userid, oneid, message_topic, label, message_click, payload)
    elif fulfillment_text == "กรุณากรอก Customer Number (CNO) ครับ":
        message_topic = "กรุณากรอก Customer Number (CNO) ครับ"
        label = ["ไม่มี CNO"]
        message_click = ["ไม่มี CNO"]
        payload = ["no cno"]
        OneChatNotify_quickreply(userid, oneid, message_topic, label, message_click, payload)
    elif "กรุณาระบุวันเริ่มต้นของ Performance VM" in fulfillment_text :
        message_topic = "กรุณาระบุวันเริ่มต้นครับ"
        label = ["กรุณาระบุวันเริ่มต้น"]
        message_click = [""]
        payload = ["sdate"]
        OneChatNotify_quickreply(userid, oneid, message_topic, label, message_click, payload )
    elif fulfillment_text == "กรุณาระบุวันสิ้นสุดครับ":
        message_topic = "กรุณาระบุวันสิ้นสุดครับ"
        label = ["กรุณาระบุวันสิ้นสุด"]
        message_click = [""]
        payload = ["edate"]
        OneChatNotify_quickreply(userid, oneid, message_topic, label, message_click, payload )
    elif "sdate" and "edate" and "vmname" in fulfillment_text:
        print("fulfillment_text : ", fulfillment_text)
        para_sdate = fulfillment_text.split('\n')[1].split(' : ')[1]
        para_edate = fulfillment_text.split('\n')[2].split(' : ')[1]
        para_vm_name = fulfillment_text.split('\n')[3].split(' : ')[1]
        try:
            OneChatNotify(userid, oneid, response_text["message"])
            resourceId, platform = change_vmname_to_UUID(para_vm_name)
            # print("resourceId :", resourceId)
            token = get_token(platform)
            vreal_graph_data = query_metrics_resources(token, resourceId, para_sdate, para_edate, platform)
            # print("vreal_graph_data : ", vreal_graph_data)
            count_sensor, count_disk, keep_byte_image = export_pic(vreal_graph_data)

            if count_sensor and count_disk != "":
                send_picture_to_onechat(userid, oneid, keep_byte_image)
            else:
                message = "ไม่พบข้อมูลของ VM \nกรุณาเปลี่ยน VMname / ช่วงวันที่ในการดึงข้อมูลครับ"
                OneChatNotify(userid, oneid, message)
            # print("##########################################################################")
        except:
            message = "ไม่พบข้อมูลของ VM \nกรุณาเปลี่ยน VMname / ช่วงวันที่ในการดึงข้อมูลครับ"
            OneChatNotify(userid, oneid, message)
    else:
        OneChatNotify(userid, oneid, response_text["message"])
    return jsonify(response_text)

# Endpoint dialogflow conversation flow
@app.route('/dialogflow', methods=['POST'])
def webhook():
    data = request.get_json(silent=True)
    return jsonify(data)

# Reply dialogflow converation
def detect_intent_texts(project_id, session_id, text, language_code):
    
    # Open session to dialogflow with project_id and session_id
    session_client = dialogflow.SessionsClient()
    session = session_client.session_path(project_id, session_id)

    # If want to send to dialogflow is text
    if text:
        print("text /def : ",text)

        # Input text to form of dialogflow 
        text_input = dialogflow.types.TextInput(
            text=text, language_code=language_code)
        # print("text_input / def : ", text_input)

        # Input text to dialogflow flow
        query_input = dialogflow.types.QueryInput(text=text_input)
        # print("query_input /def : ", query_input)

        # Get response from dialogflow
        response = session_client.detect_intent(
            session=session, query_input=query_input)

        # ==============================================    
        # Show all data
        # print("response :[{}] ".format(response))
        # ==============================================

        # Return response['query_result']['fulfillment_text'] to be value of fultillment text
        return response.query_result.fulfillment_text

# run Flask app
if __name__ == "__main__":
    app.run(debug=True, threaded=True, host='0.0.0.0', port='6100', ssl_context = context)
