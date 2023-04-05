import json
import random
import paho.mqtt.client as mqtt
import pygame
import os
import csv
import button
import pandas as pd

pos_array = list()
pygame.init()
clock = pygame.time.Clock()
SCREEN_WIDTH = 1000 #1000
SCREEN_HEIGHT = 750 #900
TILE_SIZE = 10 # 12
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("demo")


def matrix(x):
    return x * TILE_SIZE + TILE_SIZE / 2

# doc map
def read_csv(filename):
    map_data = []
    with open(os.path.join(filename)) as data:
        data = csv.reader(data, delimiter=",")
        for row in data:
            map_data.append(list(row))
    return map_data


arrMap = read_csv("csv_file/map350danhdauvitri.csv")

def draw(arrVarMap):
    j = 2
    x = 0
    for point in arrVarMap:
        if x == 0:
            x += 1
            continue
        for i in range(len(point)):
            if point[i] == "":
                pygame.draw.rect(
                    screen,
                    (211, 211, 211),
                    pygame.Rect(
                        (i + 1) * TILE_SIZE, j * TILE_SIZE, TILE_SIZE, TILE_SIZE
                    ),
                    1,
                )
                # blit_text(screen, '+', ((i + 1) * TILE_SIZE + 4, j * TILE_SIZE), font2)
            if point[i] == "2": #diem nhan hang
                pygame.draw.rect(
                    screen,
                    (58, 232, 34),
                    pygame.Rect(
                        (i + 1) * TILE_SIZE, j * TILE_SIZE, TILE_SIZE, TILE_SIZE
                    ),
                )
                pygame.draw.rect(
                    screen,
                    (211, 211, 211),
                    pygame.Rect(
                        (i + 1) * TILE_SIZE, j * TILE_SIZE, TILE_SIZE, TILE_SIZE
                    ),
                    1,
                )
            if point[i] == "4":
                pygame.draw.rect(
                    screen,
                    (246, 181, 121),
                    pygame.Rect(
                        (i + 1) * TILE_SIZE, j * TILE_SIZE, TILE_SIZE, TILE_SIZE
                    ),
                )
                pygame.draw.rect(
                    screen,
                    (211, 211, 211),
                    pygame.Rect(
                        (i + 1) * TILE_SIZE, j * TILE_SIZE, TILE_SIZE, TILE_SIZE
                    ),
                    1,
                )
            if point[i] == "1": #diem tra hang
                pygame.draw.rect(
                    screen,
                    (58, 116, 34),
                    pygame.Rect(
                        (i + 1) * TILE_SIZE, j * TILE_SIZE, TILE_SIZE, TILE_SIZE
                    ),
                )
        j += 1


def on_connect(client, obj, flags, rc):
    print("rc: " + str(rc))

device = dict()

def on_message_location(client, obj, msg):
    data = msg.payload.decode()
    device[msg.topic.split("/")[0]] = data


def on_publish(client, obj, mid):
    pass


def on_subscribe(client, obj, mid, granted_qos):
    pass


def on_log(client, obj, level, string):
    print(string)


# If you want to use a specific client id, use
# client = mqtt.Client("client-id")
# but note that the client id must be unique on the broker. Leaving the client
# id parameter empty will generate a random id for you.

client_id = f"map-view-{random.randint(0, 1000)}"

#  + trong topic dai dien cho chuoi bat ky ,lister topic cac thiet bi gui vi tri device/{device_id}/location
topic_location = f"+/location"

broker = "127.0.0.1"
port = 1883
username = "python-user"
password = "123"
# client_id khong được trùng
client = mqtt.Client(client_id)
client.username_pw_set(username, password)

# set callback function

client.message_callback_add("+/location", on_message_location)

client.on_connect = on_connect
client.on_publish = on_publish
client.on_subscribe = on_subscribe
# client.on_log = on_log
client.connect(broker, port, 25)
client.subscribe("+/location", 0)

client.loop_start()

run = True

df = pd.DataFrame(arrMap)
df.to_csv("myfile.csv")
# load giao dien
start_img = pygame.image.load("graph/sta.png").convert_alpha()
exit_img = pygame.image.load("graph/st.png").convert_alpha()

start_button = button.Button(750, 90, start_img, 0.4)#940, 50
exit_button = button.Button(820, 90, exit_img, 0.4)#1000,50

on_img = pygame.image.load("graph/on.png").convert_alpha()
off_img = pygame.image.load("graph/off.png").convert_alpha()

on_button = button.Button(750, 550, on_img, 0.25)#940, 750
off_button = button.Button(820, 550, off_img, 0.25)#1000,750

# vẽ text
def blit_text(surface, text, pos, font, color=pygame.Color("black")):
    words = [
        word.split(" ") for word in text.splitlines()
    ]  # 2D array where each row is a list of words.
    space = font.size(" ")[0]  # The width of a space.
    max_width, max_height = surface.get_size()
    x, y = pos
    for line in words:
        for word in line:
            word_surface = font.render(word, 0, color)
            word_width, word_height = word_surface.get_size()
            if x + word_width >= max_width:
                x = pos[0]  # Reset the x.
                y += word_height  # Start on new row.
            surface.blit(word_surface, (x, y))
            x += word_width + space
        x = pos[0]  # Reset the x.
        y += word_height  # Start on new row.

#|  So AGV online:   225          | 
text = f"""
---------------------------------------------
|  So cua nhan hang:   38         |
|  So cong tra hang:   360         |
---------------------------------------------
"""
label1 = """Bat dau chuong trinh"""
label2 = """Bat tat AGV"""
font = pygame.font.SysFont("Arial", 20)
font2 = pygame.font.SysFont("Arial", 8)
# def draw_text_GUI:
#

start_time = pygame.time.get_ticks()
i = 0
while run:
    screen.fill((220, 221, 220))
    draw(arrMap)
    if start_button.draw(screen):
        client.publish("server", payload="start".encode(), qos=0, retain=False)
        print("start")
    # if exit_button.draw(screen):
    #     client.publish("server", payload="stop".encode(), qos=0, retain=False)
    #     print("stop")
    # if on_button.draw(screen):
    #     print("on")
    # if off_button.draw(screen):
    #     print("off")
    for item in device.copy():
        data = device[item].split("/")
        x = float(data[0])
        y = float(data[1])
        clock_agv = data[-2]
        device_str = data[-1]
        blit_text(screen, device_str, (matrix(x), matrix(y)), font2)
        if data[2] == "False":
            pygame.draw.circle(screen, (0, 0, 255), [matrix(x), matrix(y)], 4)
        else:
            pygame.draw.circle(screen, (255, 0, 0), [matrix(x), matrix(y)], 4)
    # blit_text(screen, label1, (720, 50), font)#920, 20
    blit_text(screen, text, (720, 240), font)#900, 300
    # blit_text(screen, label2, (720, 510), font)#950, 720

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
    pygame.display.update()
    clock.tick(30)

pygame.quit()
