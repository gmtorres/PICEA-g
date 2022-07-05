import math
import numpy as np
from functools import cmp_to_key


class KD_Node:
    def __init__(self, depth, median = None, left = None, right = None, point = None):
        self.depth = depth
        self.left = left
        self.right = right
        self.point = point
        self.median = median
        self.leaf = True if left == None and right == None else False

        self.parent = None
        
        if self.leaf:
            point.kd_node = self
        if left: left.parent = self
        if right: right.parent = self

class KD_Element:
    def __init__(self,element):
        self.element = element
        self.left = None
        self.kd_node = None
    def get_value(self):
        return self.element.get_value()
    def get_element(self):
        return self.element


def compare(x, y):
    for i in range(len(x)):
        if x[i] < y[i]:
            return -1
        elif y[i] < x[i]:
            return 1
    return 0

class KD_Tree():

    def __init__(self, points):
        self.root = None
        if len(points) == 0:
            return
        self.elements = []
        #points = sorted(points,key = cmp_to_key(compare))
        #i = 0
        #self.elements.append(KD_Element(points[0]))
        for p in points:
            self.elements.append(KD_Element(p))
        
        self.dim = len(self.elements[0].get_value())
        
        aux_lists = []
        for i in range(self.dim):
            aux_list = sorted(self.elements, key = lambda e : e.get_value()[i])
            aux_lists.append(aux_list)
        
        self.root = self.__build_kd(aux_lists)

    def __get_median(self, points, aux_lists,  d):
        m = None
        median = None
        if len(points) % 2 == 1:
            m = int((len(points) - 1) / 2)
            median = points[m].get_value()[d]
        else:
            m = int(len(points) / 2) - 1
            median = (points[m].get_value()[d] + points[m+1].get_value()[d])/2
        
        for i in range(m + 1):
            points[i].left = True

        left_auxs = []
        right_auxs = []
        for i in range(self.dim):
            left = []
            right = []
            for elem in aux_lists[i]:
                if elem.left:
                    left.append(elem)
                else:
                    right.append(elem)
            left_auxs.append(left)
            right_auxs.append(right)
        for i in range(m + 1):
            points[i].left = False
        return left_auxs, right_auxs, median
        

    def __build_kd(self, aux_lists, depth = 0):

        d = depth % self.dim
        points = aux_lists[d]
        if len(points) == 1:
            return KD_Node(d, point = points[0])
        elif len(points) == 0:
            return None

        left_auxs, right_auxs, median = self.__get_median(points, aux_lists, d) 
        l = self.__build_kd(left_auxs,d+1)
        r = self.__build_kd(right_auxs,d+1)
        if l == None:
            return r
        elif r == None:
            return l
        else:
            return KD_Node(d, median=median, left= l, right= r)

    def search(self, query):
        self.query_output = []
        if self.root == None:
            return []
        window = np.full((self.dim,2), [-math.inf,math.inf]).tolist()
        self.__search(query, self.root, window)
        return [p.get_element() for p in self.query_output]
    
    def __contained(self, window, query, safe = 0):
        #for i in range(len(window)-1,-1,-1):
        for i in range(safe, len(window)):
            if window[i][0] < query[i][0] or window[i][1] > query[i][1]:
                return False, safe
            else:
                safe += 1
        return True, safe
    def __contained_point(self, point, query, safe = 0):
        value = point.get_value()
        if(len(value) == 2):
            print("tenso")
        for i in range(safe, len(query)):
            if value[i] < query[i][0] or value[i] > query[i][1]:
                return False
        return True
    
    def __overlap(self,window, query, safe = 0):
        for i in range(safe, len(window)):
            if window[i][0] > query[i][1] or query[i][0] > window[i][1]:
                return False
        
        return True
    
    def report_sub_tree(self, node):
        if node.leaf:
            self.query_output.append(node.point)
        else:
            self.report_sub_tree(node.left)
            self.report_sub_tree(node.right)

    def __search(self, query, node, window, safe = 0):
        if node.leaf:
            point = node.point
            if self.__contained_point(point, query, safe):
                self.query_output.append(node.point)
        else:           
            window_l = np.array(window)
            window_r = np.array(window)

            window_l[node.depth][1] = node.median
            window_r[node.depth][0] = node.median
            contained_l, safe_l = self.__contained(window_l, query, safe)
            if contained_l: # windows fully inside query
                self.report_sub_tree(node.left)
            else:
                if self.__overlap(window_l,query, safe_l):
                    self.__search(query,node.left, window_l, safe_l)
            
            contained_r, safe_r = self.__contained(window_r, query, safe)
            if contained_r:
                self.report_sub_tree(node.right)
            else:
                if self.__overlap(window_r,query, safe_r):
                    self.__search(query,node.right, window_r, safe_r)

            

    
