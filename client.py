import json
import logging
import random as rd
import sys
import time
from typing import List
import ast
import numpy as np
import paho.mqtt.client as mqtt
import pygame

from routing import BFS
from utils import loadPointPort, manhattanDistance, outport

ID_CHECK = None
num_robot = 2
TILE_SIZE = 12

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.CRITICAL)
arrOutPort_check_pos = loadPointPort("csv_file/arrOutput.csv")
arrQueue = loadPointPort("csv_file/arrQueue.csv")
arrInPort = loadPointPort("csv_file/arrInput.csv")
arrInit = loadPointPort("csv_file/arrInit.csv")
rd.seed(123)
index_x = [7, 10, 13, 16, 19, 22, 25, 28, 31, 34, 37, 40, 43, 46, 49, 52, 55, 58, 61]
index_y = [[5, 6], [64, 65]]


def json2arr(jsondata) -> list:
    path = []
    for ele in jsondata:
        path.append([ele["x"], ele["y"]])
    return path


def toQueue(id, graph, robot_list: list, checkpoint: np.ndarray = np.array([])):
    change_path = None
    robot: Robot = robot_list[id - 1]
    cur_pos_x = robot.x
    cur_pos_y = robot.y
    r = 8
    rangeX = [cur_pos_x - r, cur_pos_x + r]
    rangeY = [cur_pos_y - r, cur_pos_y + r]

    if rangeX[0] <= 0:
        rangeX[0] = 0

    if rangeY[0] <= 0:
        rangeY[0] = 0

    if rangeX[1] >= 68:
        rangeX[1] = 68

    if rangeY[1] >= 68:
        rangeY[1] = 68

    list_vertices = checkpoint[int(rangeY[0]):int(rangeY[1]) + 1, int(rangeX[0]):int(rangeX[1]) + 1]
    list_vertices = np.array(list_vertices)

    [tmp_pos_y, tmp_pos_x] = np.where(list_vertices == id)

    queue_index = np.where(list_vertices == -1)
    path_index = np.where(list_vertices == 0)
    arrQueuePoint = []
    arrPathPoint = []
    vis = [[True for i in range(list_vertices.shape[1])] for i in range(list_vertices.shape[0])]
    for queue_posion in zip(queue_index[1], queue_index[0]):
        arrQueuePoint.append(queue_posion)
        vis[queue_posion[1]][queue_posion[0]] = False
    for path_position in zip(path_index[1], path_index[0]):
        arrPathPoint.append(path_position)
        vis[path_position[1]][path_position[0]] = False

    distance = []
    try:
        start_point = [int(tmp_pos_x), int(tmp_pos_y)]
    except:
        """
        Test lỗi trong local map có 2 vị trí của agv đang đánh dấu.
        """
        print("error temp pos in local map: ", tmp_pos_x, tmp_pos_y)
        print(f"Vùng lân cận của device {id}: \n", list_vertices)

        if len(tmp_pos_x):
            start_point = [int(tmp_pos_x[0]), int(tmp_pos_y[0])]
        sys.exit("Lỗi Local map!")

    vis[start_point[1]][start_point[0]] = False

    """
    Tính distance từ điểm đứng hiện tại đến các điểm queue trong local map

    """
    for queue_point in arrQueuePoint:
        dis = manhattanDistance(start_point, queue_point)
        distance.append(dis)
    distance = np.array(distance)
    index_sort = np.argsort(distance)

    vis_temp = vis.copy()
    change_path = BFS(list_vertices, vis_temp, start_point[1], start_point[0])
    if change_path is None:
        return
    x_plus = cur_pos_x - start_point[0]
    y_plus = cur_pos_y - start_point[1]
    finalPath = []
    if change_path is not None:
        for point in change_path:
            finalPath.append([point[0] + x_plus, point[1] + y_plus])
    return finalPath


def checkAvailblePath(path: List, check_pos: np.ndarray):
    for point in path:
        x, y = point
        if check_pos[int(y)][int(x)] != 0:
            return False
    return True


def checkTraffic(robot, check_pos: np.ndarray, new_point_early: list):
    """
    check trong vùng hiện tại của robot có những robot khác nào đang di chuyển hay không
    """
    startX, startY = robot.x, robot.y
    cur_pos_x = startX
    cur_pos_y = startY
    r = 3
    rangeX = [cur_pos_x - r, cur_pos_x + r]
    rangeY = [cur_pos_y - r, cur_pos_y + r]

    if rangeX[0] <= 0:
        rangeX[0] = 0

    if rangeY[0] <= 0:
        rangeY[0] = 0

    if rangeX[1] >= 68:
        rangeX[1] = 68

    if rangeY[1] >= 68:
        rangeY[1] = 68

    list_vertices = check_pos[int(rangeY[0]):int(rangeY[1]) + 1, int(rangeX[0]):int(rangeX[1]) + 1]
    list_vertices = np.array(list_vertices)
    """
    Tạo range để check ùn tắc từ điểm robot đang đứng
    """
    rangeX = np.arange(rangeX[0], rangeX[1])
    rangeY = np.arange(rangeY[0], rangeY[1])
    """ Check điểm cuối cùng của list ùn xem có nằm trong range check vừa tạo hay không """
    check_in_range = False
    if new_point_early is not None:
        if new_point_early[0] in rangeX and new_point_early[1] in rangeY:
            check_in_range = True
    else:
        check_in_range = False
    if check_in_range:
        robot.time_coutdown_queue = pygame.time.get_ticks()
    else:
        """
        Nếu điểm mới nhất vào trong list ùn mà không nằm trong vùng check thì thực hiện check xem đã đủ thời gian chưa
        Nếu đã đủ thời gian thì thực hiện điều hướng ra khỏi queue
        """
        if pygame.time.get_ticks() - robot.time_coutdown_queue > 5000:
            return True


total_package = 0
start_time = 0


class Robot:
    check_pos = np.zeros((100, 100), dtype=int)
    local_check_pos = np.zeros((100, 100), dtype=int)

    """
    Định nghĩa đánh dấu:
    +) -1: điểm queue.
    +) -2: điểm đổ hàng.
    +) 0: điểm trống
    +) Số khác: id của AGV.
    """
    for queue_point in arrQueue:
        local_check_pos[queue_point[1]][queue_point[0]] = -1
    for out_point in arrOutPort_check_pos:
        local_check_pos[out_point[1]][out_point[0]] = -2

    stop_queue = []
    early_stop_queue = []

    def __init__(
            self,
            device_id,
            x,
            y,
            broker="127.0.0.1",
            port=1883,
            username="python-user",
            password="123",
    ):
        # SETTING TIME SYNC
        self.time_stop = pygame.time.get_ticks()
        self.time_early_stop = pygame.time.get_ticks()
        self.time_coutdown_queue = None
        self.id = device_id
        self.agv_time = 0
        self.time_tick = False
        # SETTING ROBOT
        self.time_to_get = 12
        self.state = "idle"
        self.spin_time = 12
        self.drop_time = 24
        self.vector = (0, 0)
        # Biến về đường, vị trí và trạng thái của AGV
        self.speed = 3
        self.dict_input = list()
        self.have_package = False
        self.run = False
        self.position = [x * TILE_SIZE, y * TILE_SIZE]
        self.x = x
        self.y = y
        self.arrMap = list()
        self.way = list()
        self.wayBackFromQueue = list()
        self.wayReturn = list()
        self.spin = 0
        self.out_x = None
        self.out_y = None
        self.old_pos = [int(self.x), int(self.y)]
        self.nex_pos = [-1, -1]
        self.stop_pos = list()  # Biến lưu điểm dừng của robot
        # SETTING MQTT
        self.device_id = f"device-{device_id}"
        self.topic_sub = f"{self.device_id}/#"
        self.client = mqtt.Client(self.device_id)
        self.client.username_pw_set(username, password)
        self.client.message_callback_add("call", self.on_message_start)
        self.client.message_callback_add(f"{self.device_id}/way", self.on_message_way)
        self.client.message_callback_add("clock", self.on_message_timer)
        self.client.message_callback_add("idcheck", self.on_message_check)
        self.client.on_connect = self.on_connect
        self.client.connect(broker, port, 25)
        self.client.subscribe(topic="clock", qos=0)
        self.client.subscribe(topic="idcheck", qos=0)

        self.client.subscribe([(self.topic_sub, 1), ("call", 0)])
        self.client.loop_start()
        # Check variable
        self.hasInit = False
        self.checkPath = False
        self.check_stop = False
        self.check_early_stop = False
        self.in_queue = False
        self.route_queue = False
        self.check_routing = False
        self.hasPathToQueue = False
        self.pathToQueue = list()

    def send_location(self, client):
        message = (
                str(self.x)
                + "/"
                + str(self.y)
                + "/"
                + str(self.have_package)
                + "/"
                + str(self.spin)
                + "/"
                + str(self.agv_time)
                + "/"
                + str(self.id)
        )
        if self.x > 70 or self.x < -2 or self.y < -2 or self.y > 70:
            self.vector = (0, 0)
            print(f"device {self.device_id} out of map")
            sys.exit("terminate")
        location = message.encode()
        client.publish(
            f"{self.device_id}/location", payload=location, qos=0, retain=False
        )

    def on_message_timer(self, client, obj, msg):
        server_time_sync = int(msg.payload.decode())
        self.time_tick = True
        self.agv_time = server_time_sync

    def on_message_check(self, client, obj, msg):
        ID_CHECK = int(msg.payload.decode())
        if ID_CHECK == self.id:
            self.check_routing = True
            print("routing device ", ID_CHECK)

    def add_way(self, way):
        self.arrMap.clear()
        for node in way:
            self.arrMap.append([int(node.get("x")), int(node.get("y"))])

    def on_publish(self, client, obj, mid):
        pass

    def on_connect(self, client, obj, flags, rc):
        client.publish(f"{self.device_id}/status", payload=1, qos=1, retain=True)
        print("connected mqtt", self.device_id)

    def on_message_package(self, client, obj, msg):
        message = msg.payload.decode()
        self.dict_input.clear()
        self.dict_input = json.loads(message)

    def on_message_start(self, client, obj, msg):
        if msg.payload.decode() == "start":
            if not self.run:
                self.run = True
                self.state = "move"

    def on_message_way(self, client, obj, msg):
        message = msg.payload.decode()
        # if message.split("/")[0] == "init":
        #     """
        #     Nhận đường init từ server.
        #     """
        #     global start_time
        #     start_time = int(time.time())
        #     way = json.loads(message.split("/")[1])

        #     for node in way:
        #         self.arrMap.append([int(node.get("x")), int(node.get("y"))])
        #     self.roamMap = list(self.arrMap[-4:])
        #     self.arrMap = self.arrMap[:-4]
        #     self.way = self.arrMap.copy()
        #     self.arrMap.clear()

        # elif message.split("/")[0] == "back":
        #     """
        #     Khi nhận đường về tương tự như các thao tác trong quá trình nhận đường init
        #     """
        #     way = json.loads(message.split("/")[1])
        #     self.arrMap = []
        #     for node in way:
        #         self.arrMap.append([int(node.get("x")), int(node.get("y"))])
        #     self.roamMap = list(self.arrMap[-4:])
        #     self.arrMap = self.arrMap[:-4]
        #     self.way = self.arrMap.copy()
        #     self.arrMap.clear()
        # else:
        #     """
        #     Quá trình nhận đường đi giao hàng.
        #     """
        #     if not self.route_queue:
        #         way = json.loads(msg.payload.decode())
        #         self.way.clear()
        #         for node in way:
        #             self.way.append([int(node.get("x")), int(node.get("y"))])

    def update(self):
        self.send_location(self.client)
        if self.run:
            self.check_get_order()
            # self.check_get_package()
            self.check_drop()
            self.move(self.arrMap)
            Robot.check_pos[int(self.y)][int(self.x)] = self.id

    def check_drop(self):
        global total_package
        if self.out_y is not None and self.out_x is not None:
            a = self.position[0] / TILE_SIZE
            b = self.position[1] / TILE_SIZE
            if a + 1 == float(self.out_x) and b == float(self.out_y) and not self.route_queue:
                self.speed = 0
                self.out_x = None
                self.out_y = None
                self.have_package = False
                self.state = "drop_package"
                message = "way_back/"
                x_in = str(int(a))
                y_in = str(int(b))
                message = message + x_in + "," + y_in
                self.client.publish(
                    f"{self.device_id}/get-way", payload=message, qos=1, retain=False
                )
                total_package += 1
            elif a - 1 == float(self.out_x) and b == float(self.out_y) and not self.route_queue:
                self.speed = 0
                self.out_x = None
                self.out_y = None

                self.have_package = False
                self.state = "drop_package"
                message = "way_back/"
                x_in = str(int(a))
                y_in = str(int(b))
                message = message + x_in + "," + y_in
                self.client.publish(
                    f"{self.device_id}/get-way", payload=message, qos=1, retain=False
                )
                total_package += 1
        if self.state == "drop_package":
            if self.drop_time > 0:
                self.drop_time -= 1
            else:
                self.drop_time = 24
                self.speed = 3
                self.state = "move"

    def check_get_order(self):
        if self.have_package is False and len(self.arrMap) == 0:
            a = self.position[0] / TILE_SIZE
            b = self.position[1] / TILE_SIZE
            x_in = str(int(a))
            y_in = str(int(b))
            message = "get-order/" + x_in + "," + y_in
            self.client.publish(
                f"{self.device_id}/get-way", payload=message, qos=1, retain=False
            )

    # def check_get_package(self):
    #     if self.have_package is not True and not self.route_queue:
    #         for item in arrInPort:
    #             if self.x == item[0] and self.y == item[1] and bool(rd.getrandbits(1)):
    #                 self.have_package = True
    #                 self.speed = 0
    #                 random_outport = arrOutPort[rd.randrange(240)]
    #                 self.out_x = random_outport[0]
    #                 self.out_y = random_outport[1]
    #                 # Block code for two part delivery
    #
    #                 if item[0] < 34:
    #                     random_outport = arrOutPort[rd.randrange(240)]
    #                     self.state = "get_package"
    #                     self.out_x = random_outport[0]
    #                     self.out_y = random_outport[1]
    #                     while self.out_x >= 34:
    #                         random_outport = arrOutPort[rd.randrange(240)]
    #                         self.state = "get_package"
    #                         self.out_x = random_outport[0]
    #                         self.out_y = random_outport[1]
    #                 elif item[0] > 34:
    #                     random_outport = arrOutPort[rd.randrange(240)]
    #                     self.state = "get_package"
    #                     self.out_x = random_outport[0]
    #                     self.out_y = random_outport[1]
    #                     while self.out_x < 34:
    #                         random_outport = arrOutPort[rd.randrange(240)]
    #                         self.state = "get_package"
    #                         self.out_x = random_outport[0]
    #                         self.out_y = random_outport[1]
    #                 message = (
    #                         "way_deliver/"
    #                         + str(item[0])
    #                         + ","
    #                         + str(item[1])
    #                         + ","
    #                         + str(self.out_x)
    #                         + ","
    #                         + str(self.out_y)
    #                 )
    #                 self.client.publish(
    #                     f"{self.device_id}/get-way",
    #                     payload=message,
    #                     qos=1,
    #                     retain=False,
    #                 )
    #                 break
    #     if self.state == "get_package":
    #         self.time_to_get -= 1
    #     if self.time_to_get == 0:
    #         self.time_to_get = 24
    #         self.speed = 3
    #         self.state = "move"

    def move(self, path):
        if len(path) != 0:
            a = path[0][0] - self.x
            b = path[0][1] - self.y
            temp = (0, 0)
            if self.vector != (0, 0):
                temp = self.vector
            if a > 0 and b == 0:
                self.vector = (1, 0)
            elif a < 0 and b == 0:
                self.vector = (-1, 0)
            elif a == 0 and b > 0:
                self.vector = (0, 1)
            elif a == 0 and b < 0:
                self.vector = (0, -1)
            self.check_spin(temp)

            if self.spin != 0:
                if self.spin_time == 0:
                    self.spin = 0
                    self.spin_time = 12
                else:
                    self.spin_time -= 1
            else:
                if self.x % 1 == 0 and self.y % 1 == 0:
                    self.next_pos, next_pos2 = self.save_locate()
                    if Robot.check_pos[self.next_pos[1]][self.next_pos[0]] == 0:
                        Robot.check_pos[self.next_pos[1]][self.next_pos[0]] = self.id

                if Robot.check_pos[self.next_pos[1]][self.next_pos[0]] == self.id or Robot.check_pos[self.next_pos[1]][
                    self.next_pos[0]] == -1:
                    self.position[0] += self.vector[0] * self.speed
                    self.position[1] += self.vector[1] * self.speed
                    self.x = self.position[0] / TILE_SIZE
                    self.y = self.position[1] / TILE_SIZE

            if self.x == path[0][0] and self.y == path[0][1]:
                path.remove(path[0])
            if self.x == self.next_pos[0] and self.y == self.next_pos[1]:
                Robot.check_pos[self.old_pos[1]][self.old_pos[0]] = 0
                self.old_pos[0] = int(self.x)
                self.old_pos[1] = int(self.y)
            self.check_stop_status()
            self.check_early_stoping_status()

    def check_spin(self, temp):
        if temp[0] * self.vector[1] + temp[1] * self.vector[0] == -1 and temp[0] != 0:
            self.spin = 1
        elif temp[0] * self.vector[1] + temp[1] * self.vector[0] == 1 and temp[0] != 0:
            self.spin = 2
        elif temp[0] * self.vector[1] + temp[1] * self.vector[0] == -1 and temp[0] == 0:
            self.spin = 2
        elif temp[0] * self.vector[1] + temp[1] * self.vector[0] == 1 and temp[0] == 0:
            self.spin = 1

    def save_locate(self):
        if self.vector == (1, 0):
            return [int(self.x + 1), int(self.y)], [int(self.x + 2), int(self.y)]
        if self.vector == (-1, 0):
            return [int(self.x - 1), int(self.y)], [int(self.x - 2), int(self.y)]
        if self.vector == (0, 1):
            return [int(self.x), int(self.y + 1)], [int(self.x), int(self.y + 2)]
        if self.vector == (0, -1):
            return [int(self.x), int(self.y - 1)], [int(self.x), int(self.y - 2)]

    def check_stop_status(self):
        """
        - Hàm check trạng thái tắc của agv
        """
        if float(self.old_pos[0]) == self.x and float(self.old_pos[1]) == self.y and self.y not in [2, 68]:
            if not self.check_stop:
                self.check_stop = True
                self.time_stop = pygame.time.get_ticks()
            if pygame.time.get_ticks() - self.time_stop > 3000 and self.check_stop and not self.route_queue and self.state != "drop_package":
                if self.id not in Robot.stop_queue:
                    Robot.stop_queue.append(self.id)
                    self.stop_pos = [int(self.x), int(self.y)]
                    Robot.local_check_pos[self.stop_pos[1]][self.stop_pos[0]] = self.id

        else:
            self.check_stop = False
            if self.id in Robot.stop_queue:
                Robot.stop_queue.remove(self.id)
                Robot.local_check_pos[self.stop_pos[1]][self.stop_pos[0]] = 0

    def check_early_stoping_status(self):
        """
        - Hàm check robot đang ùn
        """
        if float(self.old_pos[0]) == self.x and float(self.old_pos[1]) == self.y:
            if not self.check_early_stop:
                self.check_early_stop = True
                self.time_early_stop = pygame.time.get_ticks()
            if pygame.time.get_ticks() - self.time_early_stop > 2000 and self.check_early_stop and not self.route_queue:
                if self.id not in Robot.early_stop_queue:
                    Robot.early_stop_queue.append(self.id)

        else:
            self.check_early_stop = False
            if self.id in Robot.early_stop_queue:
                Robot.early_stop_queue.remove(self.id)

    def clear_check_pos(self):
        if not self.route_queue:
            cur_x, cur_y = int(self.x), int(self.y)
            all_index_y, all_index_x = np.where(Robot.check_pos == self.id)
            for x, y in zip(all_index_x, all_index_y):
                dis = manhattanDistance([cur_x, cur_y], [x, y])
                if dis > 2:
                    Robot.check_pos[y][x] = 0
            if len(all_index_y) != 1:
                Robot.check_pos[cur_y][cur_x] = self.id

    def clear_check_pos_ver2(self):
        if not self.route_queue:
            all_index_y, all_index_x = np.where(Robot.check_pos == self.id)
            if len(all_index_y) > 2:
                pass
            else:
                cur_x, cur_y = int(self.x), int(self.y)
                for x, y in zip(all_index_x, all_index_y):
                    dis = manhattanDistance([cur_x, cur_y], [x, y])
                    if dis > 1:
                        Robot.check_pos[y][x] = 0


robot_list = list()

for i in range(1, num_robot+1):
    index = rd.randint(1, len(arrInit) - 1)
    coor = arrInit[index]
    arrInit.remove(coor)
    # coor = outport[i]
    # print('outport',coor)
    robot_list.append(Robot(i, coor[0], coor[1]))
    Robot.check_pos[coor[1]][coor[0]] = i

clock = pygame.time.Clock()
last_time = 0
start = True
InQueue = []
while True:
    total = 0
    if not start:
        for robot in robot_list:
            if robot.hasInit:
                total += 1
        if total == num_robot - 1:
            start = True
    else:
        for robot in robot_list:
            robot.update()
            robot.clear_check_pos()
    if len(Robot.stop_queue):
        for id_check in Robot.stop_queue:
            if id_check in Robot.stop_queue:
                robot_x = robot_list[id_check - 1]
                if not robot_x.route_queue:
                    allIndex = np.where(Robot.local_check_pos == robot_x.id)
                    for x_, y_ in zip(allIndex[1], allIndex[0]):
                        Robot.local_check_pos[y_][x_] = 0
                    Robot.local_check_pos[int(robot_x.y)][int(robot_x.x)] = robot_x.id
                    finalPath = toQueue(robot_x.id, None, robot_list, Robot.local_check_pos)
                    if finalPath is None:
                        continue
                    else:
                        Robot.local_check_pos[int(finalPath[-1][1])][int(finalPath[-1][0])] = robot_x.id
                        robot_x.wayReturn = robot_x.arrMap.copy()
                        robot_x.pathToQueue = finalPath[1:]
                        robot_x.wayBackFromQueue = list(reversed(finalPath))[1:]
                        check = False
                        check = True
                        for point in robot_x.pathToQueue:
                            if Robot.check_pos[int(point[1])][int(point[0])] in [-1, 0]:
                                continue
                            else:
                                check = False

                        if check:
                            for point in robot_x.pathToQueue:
                                Robot.check_pos[int(point[1])][int(point[0])] = id_check
                            robot_x.arrMap = robot_x.pathToQueue
                            robot_x.route_queue = True
                            InQueue.append(robot_x.id)
                            robot_x.time_coutdown_queue = pygame.time.get_ticks()
                            Robot.stop_queue.remove(id_check)
                            Robot.local_check_pos[int(robot_x.y)][int(robot_x.x)] = 0

                        else:
                            Robot.local_check_pos[int(finalPath[-1][1])][int(finalPath[-1][0])] = -1

    InQueueHasPack = []
    InQueueNoPack = []
    for ID_CHECK in InQueue:
        robot_x: Robot = robot_list[ID_CHECK - 1]
        if robot_x.have_package:
            InQueueHasPack.append(ID_CHECK)
        else:
            InQueueNoPack.append(ID_CHECK)
    rd.shuffle(InQueueHasPack)
    rd.shuffle(InQueueNoPack)
    num_robot_per_cycle = 7

    for ID_CHECK in InQueueHasPack:
        robot_x: Robot = robot_list[ID_CHECK - 1]
        if len(Robot.stop_queue) and num_robot_per_cycle > 0:
            last_robot_early_stop = robot_list[Robot.early_stop_queue[-1] - 1]
            robot_x.check_routing = checkTraffic(robot_x, Robot.check_pos,
                                                 [int(last_robot_early_stop.x), int(last_robot_early_stop.y)])
            if robot_x.check_routing:
                num_robot_per_cycle -= 1
        else:
            robot_x.check_routing = checkTraffic(robot_x, Robot.check_pos, None)
            if robot_x.check_routing:
                num_robot_per_cycle -= 1
        if robot_x.check_routing:
            robot_x.check_routing = False
            if robot_x.have_package:
                cur_location = [robot_x.x, robot_x.y]
                output_location = robot_x.wayReturn[-1]

                if cur_location[1] > output_location[1]:
                    path = [[cur_location[0] - 1, cur_location[1]], [cur_location[0] - 1, output_location[1] + 1],
                            [output_location[0], output_location[1] + 1], output_location]
                    robot_x.arrMap.clear()
                    robot_x.arrMap = path
                    robot_x.check_stop = False
                    robot_x.route_queue = False
                    InQueue.remove(robot_x.id)
                    Robot.local_check_pos[int(robot_x.y)][int(robot_x.x)] = -1
                    pass
                elif cur_location[1] < output_location[1]:
                    path = [[cur_location[0] + 1, cur_location[1]], [cur_location[0] + 1, output_location[1] - 1],
                            [output_location[0], output_location[1] - 1], output_location]
                    robot_x.arrMap.clear()
                    robot_x.arrMap = path
                    robot_x.check_stop = False
                    robot_x.route_queue = False
                    InQueue.remove(robot_x.id)
                    Robot.local_check_pos[int(robot_x.y)][int(robot_x.x)] = -1
    if num_robot_per_cycle > 0:
        for ID_CHECK in InQueueNoPack:
            robot_x: Robot = robot_list[ID_CHECK - 1]
            if len(Robot.stop_queue) and num_robot_per_cycle > 0:
                last_robot_early_stop = robot_list[Robot.early_stop_queue[-1] - 1]
                robot_x.check_routing = checkTraffic(robot_x, Robot.check_pos,
                                                     [int(last_robot_early_stop.x), int(last_robot_early_stop.y)])
                if robot_x.check_routing:
                    num_robot_per_cycle -= 1
            else:
                robot_x.check_routing = checkTraffic(robot_x, Robot.check_pos, None)
                if robot_x.check_routing:
                    num_robot_per_cycle -= 1
            if robot_x.check_routing:
                robot_x.check_routing = False
                if checkAvailblePath(robot_x.wayBackFromQueue, Robot.check_pos) and len(robot_x.arrMap) == 0:
                    robot_x.arrMap.extend(robot_x.wayBackFromQueue)
                    robot_x.arrMap.extend(robot_x.wayReturn)
                    robot_x.check_stop = False
                    robot_x.route_queue = False
                    InQueue.remove(robot_x.id)
                    Robot.local_check_pos[int(robot_x.y)][int(robot_x.x)] = -1
    clock.tick(24)
