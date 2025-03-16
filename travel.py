#!/usr/bin/python

import math
import random
import matplotlib.pyplot as plt
import copy

class City:
    def __init__(self, name, coord_x, coord_y):
        self.name = name
        self.x = coord_x
        self.y = coord_y
        self.x_stash = 0
        self.y_stash = 0

    def __repr__(self):
        return 'City({}, x={:.3f}, y={:.3f})'.format(self.name, self.x, self.y)

    def stash(self):
        self.x_stash = self.x
        self.y_stash = self.y

    def swap(self):
        x = self.x
        y = self.y
        self.x = self.x_stash
        self.y = self.y_stash
        self.x_stash = x
        self.y_stash = y

    def commit(self):
        self.x = self.x_stash
        self.y = self.y_stash
        self.x_stash = 0
        self.y_stash = 0

    def abort(self):
        self.x_stash = 0
        self.y_stash = 0

class Connection:
    def __init__(self, a, b, time):
        self.a = a
        self.b = b
        self.time = time

    def __hash__(self):
        return hash((self.a, self.b))

    def __eq__(self, cc):
        return (cc.a == self.a and cc.b == self.b) or \
               (cc.a == self.b and cc.b == self.a)

    def __ne__(self, cc):
        return not(self == cc)

    def __repr__(self):
        return 'Conn({}, {}, t={:.3f})'.format(self.a, self.b, self.time)

cities={}
conns=[]
org_cities={}
org_conns=[]

with open("coords.txt", "r") as f:
    for line in f.readlines():
        if (line[0] == '#'): continue
        tokens = line.split(',')
        cities[tokens[0]] = City(tokens[0], float(tokens[1]), float(tokens[2]))
        org_cities[tokens[0]] = City(tokens[0], float(tokens[1]), float(tokens[2]))

with open("conns.txt", "r") as f:
    for line in f.readlines():
        if (line[0] == '#'): continue
        tokens = line.split(',')
        (hours, mins) = tokens[2].split(':')
        conns += [Connection(cities[tokens[0]], cities[tokens[1]], int(hours) * 60 + int(mins))]
        org_conns += [Connection(cities[tokens[0]], cities[tokens[1]], int(hours) * 60 + int(mins))]

print("info: Found {} cities.".format(len(cities)))
print("info: Found {} connections.".format(len(conns)))

# Strategy: 
#  1. Calculate average distance per time (aDPT). 
#  2. Adjust the coordinate of the cities, whose edge has the worst error
#     between the coordinate distance and the actual time times aDPT.
#     Choose the city that yields less error.
#  3. Iterate this sufficiently.

def calc_dist(city_a, city_b):
    return math.sqrt((city_a.x - city_b.x) ** 2 + (city_a.y - city_b.y) ** 2)

def calc_dist_conn(conn):
    return calc_dist(conn.a, conn.b)

total_len = 0
total_time = 0
for conn in conns:
    total_len += calc_dist(conn.a, conn.b)
    total_time += conn.time

avg_dpt = float(total_len) / float(total_time)

print("info: Average distance-per-time: {:.3f} units/min".format(avg_dpt))

def calc_error(conn):
    return avg_dpt * conn.time - calc_dist_conn(conn) 

def calc_global_error():
    total_error = 0
    for conn in conns:
        total_error += abs(calc_error(conn))
    return total_error

cand_mode = "random"
def find_largest_error_conn():
    if (cand_mode == "random"):
        ret_conn = random.choice(conns)
        ret_error = calc_error(ret_conn)
        return ret_conn, ret_error
    elif (cand_mode == "top"):
        ret_conn = None 
        ret_error = 0
        for conn in conns:
            if (not ret_conn):
                ret_conn = conn
                continue
            this_error = calc_error(conn)
            #print("info: Conn     : {} [d={:.3f} us, e={:.3f} us]"\
            #        .format(conn, calc_dist_conn(conn), this_error))
            if (abs(this_error) > abs(ret_error)):
                ret_conn = conn
                ret_error = this_error
        return ret_conn, ret_error

adjust_mode = "random"
def adjust_coord(city_fixed, city_adj, amount):
    adj_rate = 0.2
    if (adjust_mode == "random"):
        adj_rate = random.random()
    base_coord = (city_adj.x - city_fixed.x, city_adj.y - city_fixed.y)
    base_len = math.sqrt(base_coord[0] ** 2 + base_coord[1] ** 2)
    city_adj.x += (amount * adj_rate * base_coord[0] / base_len)
    city_adj.y += (amount * adj_rate * base_coord[1] / base_len)

prev_global_error = calc_global_error()
print("info: Total error: {:.3f} units".format(prev_global_error))
input()

n_iters = 10000
for n in range(n_iters):
    print("info: Iteration {}.".format(n))
    cand_conn, cand_error = find_largest_error_conn()
    if (not cand_conn):
        print("info: All error gone. Exiting.")
        exit
    print("info: Candidate: {} [d={:.3f} us, e={:.3f} us, gd={:.3f} us]"\
            .format(cand_conn, calc_dist_conn(cand_conn), cand_error, prev_global_error))

    cand_conn.a.stash()
    cand_conn.b.stash()
    adjust_coord(cand_conn.a, cand_conn.b, cand_error)
    new_global_error_b = calc_global_error()
    print("info: Adjusted : {} [d={:.3f} us, e={:.3f} us, gd={:.3f} us]"\
            .format(cand_conn, calc_dist_conn(cand_conn), calc_error(cand_conn), new_global_error_b))
    cand_conn.b.swap()

    adjust_coord(cand_conn.b, cand_conn.a, cand_error)
    new_global_error_a = calc_global_error()
    print("info: Adjusted : {} [d={:.3f} us, e={:.3f} us, gd={:.3f} us]"\
            .format(cand_conn, calc_dist_conn(cand_conn), calc_error(cand_conn), new_global_error_a))
    cand_conn.a.swap()

    if (prev_global_error < new_global_error_a and 
        prev_global_error < new_global_error_b):
        cand_conn.a.abort()
        cand_conn.b.abort()
        print("info: Reject.")
    elif (new_global_error_a < new_global_error_b):
        cand_conn.a.commit()
        cand_conn.b.abort()
        prev_global_error = new_global_error_a
    elif (new_global_error_a >= new_global_error_b):
        cand_conn.a.abort()
        cand_conn.b.commit()
        prev_global_error = new_global_error_b

    print("info: Total error: {:.3f} units".format(prev_global_error))

plt_x=[]
plt_y=[]
plt_org_x=[]
plt_org_y=[]

for city in cities.values():
    plt_x += [city.x]
    plt_y += [city.y]

for city in org_cities.values():
    plt_org_x += [city.x]
    plt_org_y += [city.y]

fig, ax = plt.subplots()
ax.scatter(plt_x, plt_y, color='r')
ax.scatter(plt_org_x, plt_org_y, color='b')
for city in cities.values():
    ax.annotate(city.name, (city.x, city.y))
for city in org_cities.values():
    ax.annotate(city.name, (city.x, city.y))
ax.invert_yaxis()
plt.show()
