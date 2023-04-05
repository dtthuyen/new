from collections import deque
import ast
from utils import Euclidean


class Graph:
    def __init__(self, adjacency_list):
        self.adjacency_list = adjacency_list

    def get_neighbors(self, v):
        return self.adjacency_list[v]

    def h(self, v, start_node):
        v = ast.literal_eval(v)
        start_node = ast.literal_eval(start_node)
        return Euclidean(start_node[0], start_node[1], v[0], v[1])

    def a_star_algorithm(self, start_node, stop_node):
        t_start_node = ast.literal_eval(start_node)
        t_stop_node = ast.literal_eval(stop_node)
        open_list = set([start_node])
        closed_list = set([])

        g = {}

        g[start_node] = 0

        parents = {}
        parents[start_node] = start_node

        while len(open_list) > 0:
            n = None
            for v in open_list:
                if n == None or g[v] + self.h(v, start_node) < g[n] + self.h(n, start_node):
                    n = v

            if n == None:
                # print('Path does not exist!')
                return None

            if n == stop_node:
                reconst_path = []

                while parents[n] != n:
                    n_ = ast.literal_eval(n)
                    reconst_path.append(n_)
                    n = parents[n]

                reconst_path.append(ast.literal_eval(start_node))

                reconst_path.reverse()
                return reconst_path

            # for all neighbors of the current node do
            for [x, y, weight] in self.get_neighbors(n):
                m = str([x, y])
                if m not in open_list and m not in closed_list:
                    open_list.add(m)
                    parents[m] = n
                    g[m] = g[n] + weight

                else:
                    if g[m] > g[n] + weight:
                        g[m] = g[n] + weight
                        parents[m] = n

                        if m in closed_list:
                            closed_list.remove(m)
                            open_list.add(m)

            open_list.remove(n)
            closed_list.add(n)

        # print('Path does not exist!')
        return None
