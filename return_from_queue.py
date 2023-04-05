import paho.mqtt.client as mqtt

client_id = f"routing"

broker = "127.0.0.1"
port = 1883
username = "python-user"
password = "123"
# client_id khong được trùng
client = mqtt.Client(client_id)
client.username_pw_set(username, password)


def on_connect(client, obj, flags, rc):
    print("rc: " + str(rc))


def on_publish(client, obj, mid):
    print("Điều hướng AGV: ")
    pass


def on_subscribe(client, obj, mid, granted_qos):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))


client.connect(broker, port, 25)
client.on_connect = on_connect
client.on_publish = on_publish
client.on_subscribe = on_subscribe
client.loop_start()
while True:
    id = input()
    client.publish("idcheck", payload=str(id).encode(), qos=0, retain=False)
