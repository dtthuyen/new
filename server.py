import csv
import json
import random
import time
from threading import Thread

import paho.mqtt.client as mqtt
import pygame
import redis

from utils import calculatePointBack, loadPointPort, deliveryPoint, calculateCost
import numpy as np

pygame.init()

TIMER = 0
publish_time_sync = False
start_signal = False

dict_input = list()
with open("csv_file/arrInput.csv", "r") as f:
    reader = csv.reader(f, delimiter="\t")
    for i, line in enumerate(reader):
        item = {
            "x": int(line[0].split(",")[0]),
            "y": int(line[0].split(",")[1]),
            "package": False,
        }
        dict_input.append(item)

arrBack = loadPointPort("csv_file/arrBack.csv")
arrDelivery = loadPointPort("csv_file/arrDelivery.csv")
arrCrossPoint = loadPointPort("csv_file/arrPoint.csv")

r = redis.Redis(host="localhost", port=6379, db=3, password="")
r2 = redis.Redis(host="localhost", port=6379, db=5, password="")  # Db đường về
r3 = redis.Redis(host="localhost", port=6379, db=14, password="")

RoamMap1 = {
    1: [[3, 2], [3, 6], [32, 6], [32, 2]],
    2: [[64, 2], [64, 5], [35, 5], [35, 2]],
    3: [[2, 68], [2, 65], [34, 65], [34, 68]],
    4: [[67, 68], [67, 64], [37, 64], [37, 68]],
}


def check_pos_new1(x, y):
    if y == 2:
        if x < 33:
            return 1
        elif x > 33:
            return 2
    elif y == 68:
        if x < 35:
            return 3
        elif x > 35:
            return 4


def check_pos5(x, y):
    """
    Hàm để tính toán điểm quay về đường default sau khi hoàn thành giao hàng đến outport
    """
    for point in arrBack:
        if x == point[0]:
            return f",{point[0]},{point[1]}"


def send_way(client, way, device_id):
    client.publish(f"{device_id}/way", payload=way, qos=0, retain=False)


def on_connect(client, obj, flags, rc):
    print("rc: " + str(rc))


def on_message_timer(client, userdata, message):
    # print("time: ", str(message.payload.decode("utf-8")))
    global TIMER
    TIMER = int(str(message.payload.decode("utf-8")))
    pass


def on_message_get_way(mosq, obj, msg):
    """
    Callback func để cấp đường cho agv
    """
    global time_sync
    type_message = msg.payload.decode().split("/")[0]
    message_info = msg.payload.decode().split("/")[1]
    device = msg.topic.split("/")[0]
    if type_message == "get-order":
        inport = r.get(message_info)
        if inport is None:
            search = message_info
        else:
            search = message_info + ',' + inport.decode()
    
        # search = message_info + ',' + inport.decode()
        Thread(target=send_way, args=(client, r2.get(search), device)).start()

    # if type_message == "way_deliver":
    #     x_in, y_in, x_out, y_out = message_info.split(",")
    #     # Biến chứa tất cả những điểm có thể đổ hàng tại outport x_out, y_out của AGV
    #     allDeliveryPoint = deliveryPoint(x_out, y_out, arrDelivery)
    #     ways = []  # Lưu trữ tất cả các đường đi của AGV
    #     for point in allDeliveryPoint:
    #         if int(point[1]) not in [61, 8]:
    #             message_info = ",".join([x_in, y_in, str(point[0]), str(point[1])])
    #             # print(message_info)
    #             ways.append(json.loads(r3.get(message_info)))
    #     costs = []  # list cost của tất cả các trường hợp đường của AGV
    #     """
    #     Khi đã có đủ số lượng đường có thể có của AGV thì tiến hành lập lịch dựa trên thời gian và va trạm
    #     """
    #     for way in ways:
    #         costs.append(calculateCost(way, arrCrossPoint))
    #     costs = np.array(costs)
    #     index_sort = np.argsort(costs)
    #     best_way = json.dumps(ways[index_sort[0]]).encode()  # Đường đi với cost nhỏ nhất.
    #     Thread(target=send_way, args=(client, best_way, device)).start()
    # elif type_message == "way_back":
    #     x_check = int(float(message_info.split(",")[0]))
    #     y_check = int(float(message_info.split(",")[1]))
    #     if check_pos5(x_check, y_check) is not None:
    #         redis_search = message_info + check_pos5(x_check, y_check)
    #         way = r2.get(redis_search)
    #         if way is None:
    #             print(redis_search)
    #         way = json.loads(way.decode())
    #         end_point = way[-1]
    #         pos = check_pos_new1(end_point['x'], end_point['y'])
    #         roamMapNew = RoamMap1[pos]
    #         for point in roamMapNew:
    #             way.append({"x": point[0], "y": point[1]})
    #         way = json.dumps(way)
    #         message = "back/" + way
    #         message.encode()
    #         Thread(target=send_way, args=(client, message, device)).start()


def on_publish(client, obj, mid):
    pass


device = dict()


def on_message_location(client, obj, msg):
    data = msg.payload.decode()
    device[msg.topic.split("/")[0]] = data


def on_message_call(client, obj, msg):
    data = msg.payload
    data = data.decode()
    global start_signal
    if data == "start" and not start_signal:
        # global publish_time_sync
        # publish_time_sync = True
        # for item in device.copy():
        #     data = device[item].split("/")
        #     x = float(data[0])
        #     y = float(data[1])
        #     redis_search = str(int(x)) + "," + str(int(y)) + check_pos5(x, y)
        #     way = r2.get(redis_search)
        #     way = json.loads(way)
        #     end_point = way[-1]
        #     pos = check_pos_new1(end_point['x'], end_point['y'])
        #     roamMapNew = RoamMap1[pos]
        #     for point in roamMapNew:
        #         way.append({"x": point[0], "y": point[1]})
        #     way = json.dumps(way)
        #     message = "init/" + way
        #     message.encode()
        #     Thread(target=send_way, args=(client, message, item)).start()
        client.publish("call", payload="start".encode(), qos=1, retain=False)
    elif data == "stop":
        client.publish("call", payload="stop".encode(), qos=0, retain=False)


def on_subscribe(client, obj, mid, granted_qos):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))


def on_log(client, obj, level, string):
    print(string)


client_id = f"server-{random.randint(0, 1000)}"

broker = "127.0.0.1"
port = 1883
username = "python-user"
password = "123"
# client_id khong được trùng
client = mqtt.Client(client_id)
client.username_pw_set(username, password)
# set callback function

client.message_callback_add("+/location", on_message_location)
client.message_callback_add("+/get-way", on_message_get_way)
client.message_callback_add("server", on_message_call)
client.message_callback_add("timer", on_message_timer)

client.on_connect = on_connect
client.on_publish = on_publish
client.on_subscribe = on_subscribe
# client.on_log = on_log

client.connect(broker, port, 25)

client.subscribe("+/#", 0)

client.subscribe("server", 0)
client.subscribe("timer", qos=0)
client.loop_start()
clock = pygame.time.Clock()
time_sync = 0
while True:
    if publish_time_sync:
        client.publish("clock", payload=str(time_sync).encode(), qos=0, retain=False)
        time_sync += 1
    clock.tick(5)
