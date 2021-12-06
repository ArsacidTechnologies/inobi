from collections import deque
import heapq


class Queue:
    def __init__(self):
        self.elements = deque()

    def empty(self):
        return len(self.elements) == 0

    def put(self, element):
        self.elements.append(element)

    def get(self):
        return self.elements.popleft()


class PriorityQueue:
    def __init__(self):
        self.elements = []

    def empty(self):
        return len(self.elements) == 0

    def put(self, item, priority):
        heapq.heappush(self.elements, (priority, item))

    def get(self):
        return heapq.heappop(self.elements)[1]

    def __iter__(self):
        while not self.empty():
            yield self.get()
