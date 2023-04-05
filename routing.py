from collections import deque as queue

import numpy as np

dRow = [-1, 0, 1, 0]
dCol = [0, 1, 0, -1]


def isValid(vis, row, col, size):
    if row < 0 or col < 0 or row >= size[0] or col >= size[1]:
        return False

    if vis is not None:
        if vis[row][col]:
            return False
    return True


def findPath_ver2(expands: list, grid):
    path = []
    start = expands[0]
    goal = expands[-1]
    path.append(goal)

    while True:
        goal = expands[-1]
        x, y = goal
        for i in range(4):
            adjx = x + dRow[i]
            adjy = y + dCol[i]
            if (isValid(None, adjx, adjy, grid.shape)) and [adjx, adjy] in expands:
                if expands.index([adjx, adjy]) < expands.index(goal):
                    path.append([adjx, adjy])
                    index_new_goal = expands.index([adjx, adjy])
                    expands = expands[:index_new_goal + 1]
                    if [adjx, adjy] == start:
                        path.reverse()
                        return path
                    break


def BFS(grid, vis, row, col):
    expands = []
    q = queue()
    q.append((col, row))
    vis[row][col] = True

    stop = False
    while (len(q) > 0):
        cell = q.popleft()
        x = cell[0]
        y = cell[1]
        if not stop:
            expands.append([x, y])
        if grid[y][x] == -1:
            stop = True
            break
        for i in range(4):
            adjx = x + dRow[i]
            adjy = y + dCol[i]
            if isValid(vis, adjy, adjx, grid.shape):
                q.append((adjx, adjy))
                vis[adjy][adjx] = True
    x, y = expands[-1]
    if grid[y][x] != -1:
        return None
    if len(expands) == 1:
        return None
    pathFinal = findPath_ver2(expands, np.arange(400).reshape(20, 20))
    return pathFinal


# Driver Code
if __name__ == '__main__':
    expands = [[5, 5], [5, 4], [6, 4], [5, 3], [6, 3], [4, 3], [7, 3], [3, 3], [8, 3], [3, 4], [3, 2], [8, 4], [9, 3],
               [2, 4], [3, 5], [2, 2], [8, 5], [9, 4], [10, 3], [2, 5], [3, 6], [1, 2], [2, 1], [8, 6], [9, 5], [2, 6],
               [0, 2], [1, 3], [2, 0], [7, 6], [9, 6], [10, 5]]
    path = findPath_ver2(expands, np.arange(400).reshape(20, 20))
    print(path)
