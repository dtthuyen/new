import numpy as np
import pandas as pd

map = pd.read_excel("../map.xlsx")
# nodes = []
arrInput = [] #nhan hang
arrOutput = [] #tra hang
arrDelivery = [] #diem do hang
arrBack = []
arrPoint = [] #diem > 2
arrQueue = [] #diem queue

d = dict()
for i in range(len(map.index)):
    for j in range(len(map.columns)):
        temp = map.iloc[i][j].split(",")
        if "i" in temp:
            arrInput.append([j, i])
        if temp[0] == 'q':
            arrQueue.append([j, i])
        if temp[0] == 'x':
            arrOutput.append([j, i])
            if map.iloc[i - 1][j].split(",")[0] != "q":
                # nodes.append([i - 1, j, map.iloc[i - 1][j].split(",")])
                arrDelivery.append([j, i - 1])
            if map.iloc[i + 1][j].split(",")[0] != "q":
                # nodes.append([i + 1, j, map.iloc[i + 1][j].split(",")])
                arrDelivery.append([j, i + 1])
            if map.iloc[i][j - 1].split(",")[0] != "q":
                # nodes.append([i, j - 1, map.iloc[i][j - 1].split(",")])
                arrDelivery.append([j - 1, i])
            if map.iloc[i][j + 1].split(",")[0] != "q":
                # nodes.append([i, j + 1, map.iloc[i][j + 1].split(",")])
                arrDelivery.append([j + 1, i])
        if len(temp) >= 2 and "i" not in temp:
            # nodes.append([i, j, temp])
            arrPoint.append([j, i])


np.savetxt("arrInput.csv", arrInput, fmt="%s", delimiter=",")
np.savetxt("arrOutput.csv", arrOutput, fmt="%s", delimiter=",")
np.savetxt("arrDelivery.csv", arrDelivery, fmt="%s", delimiter=",")
np.savetxt("arrPoint.csv", arrPoint, fmt="%s", delimiter=",")
np.savetxt("arrQueue.csv", arrQueue, fmt="%s", delimiter=",")
np.savetxt("arrBack.csv", arrInput, fmt="%s", delimiter=",")

