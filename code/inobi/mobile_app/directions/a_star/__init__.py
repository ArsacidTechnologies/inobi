from time import time as now
from math import inf as Infinity

from geopy.distance import distance

from .queue import PriorityQueue
from .utils import _recover_bidirectional, _recover_path


# HEURISTICS
def euclidean(node_a, node_b):
    return distance(node_a[-3:-1], node_b[-3:-1]).kilometers


tag = '@a-star:'


# A-STAR ITSELF
def bidirectional_a_star_search(graph, start, goal,
        heuristic=euclidean, notify=None,
        aspire=False, leaf_checks=3,
        heuristic_amplifier=1, verbose=False):

    frontier = PriorityQueue()
    backtier = PriorityQueue()

    frontier.put(start, 0)
    backtier.put(goal, 0)

    if notify:
        notify(start)
        notify(goal)

    prev = {
        start: None
    }
    costs = {
        start: 0
    }
    bprev = {
        goal: None
    }
    bcosts = {
        goal: 0
    }

    path = {}

    found_leafs = {}

    def add_and_check(leaf):
        c = costs[leaf] + bcosts[leaf]
        found_leafs[c] = leaf
        if aspire or len(found_leafs) == leaf_checks:
            m = min(found_leafs.items(), key=lambda x: x[0])[1]
            nonlocal path
            path = _recover_bidirectional(start, goal, m, prev, bprev)
            return True
        else:
            return False

    ts = now()

    for i, (fcur, bcur) in enumerate(zip(frontier, backtier)):
        if verbose:
            print(i)

        if fcur in bprev:
            if add_and_check(fcur):
                break

        for node, cost in graph.neighbors(fcur):
            new_dist = costs[fcur] + cost
            if new_dist < costs.get(node, Infinity):
                if notify:
                    notify(node)
                costs[node] = new_dist
                h = heuristic(goal, node) * heuristic_amplifier
                priority = new_dist + h
                frontier.put(node, priority)
                prev[node] = fcur

        if bcur in prev:
            if add_and_check(bcur):
                break

        for node, cost in graph.neighbors(bcur, backward=True):
            new_dist = bcosts[bcur] + cost
            if new_dist < bcosts.get(node, Infinity):
                if notify:
                    notify(node, color='#ff0055')
                bcosts[node] = new_dist
                h = heuristic(start, node) * heuristic_amplifier
                priority = new_dist + h
                backtier.put(node, priority)
                bprev[node] = bcur

    if notify:
        notify('finished in %d iterations' % (i+1,))

    print(tag, 'finished in %d iterations' % (i+1, ))
    print(tag, 'finished in {:.3f} seconds'.format(now()-ts))

    return path


def a_star_search(graph, start, goal, heuristic=euclidean, notify=None):

    if notify:
        notify(start)
        notify(goal)

    frontier = PriorityQueue()
    frontier.put(start, 0)

    prev = {
        start: None
    }
    costs = {
        start: 0
    }
    path = {}

    for i, current in enumerate(frontier):
        print(i)

        if current == goal:
            path = _recover_path(start, goal, prev)
            print(*path, sep='\n')
            break

        for node, cost in graph.neighbors(current, with_cost=True):
            new_dist = costs[current] + cost
            if new_dist < costs.get(node, Infinity):
                if notify:
                    notify(node)
                costs[node] = new_dist
                h = heuristic(goal, node)
                priority = new_dist + h
                frontier.put(node, priority)
                prev[node] = current

    if notify:
        notify('finished in %d iterations' % (i,))

    return path
