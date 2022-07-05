import math
import random
from matplotlib import pyplot as plt

import numpy as np
from kd_tree import KD_Tree

import gc

class NDS:
    def __init__(self, value):
        self.value = value
        self.restart()
    def restart(self):
        self.dominated = 0 # times it was dominated
        self.domination = [] # the one it dominates
    def increase_domination(self):
        self.dominated += 1
    def dominate(self, goal):
        self.domination.append(goal)
    def get_value(self):
        return self.value

class Goal_Vector(NDS):
    def __init__(self, value):
        super().__init__(value)

class Solution_Vector(NDS):
    def __init__(self, sol, objectives):
        super().__init__([obj(sol) for obj in objectives])
        self.solution = sol
        self.interval = None

    def get_solution(self):
        return self.solution

    def get_interval(self):
        if self.interval != None:
            return self.interval
        self.interval = []
        for v in self.value:
            self.interval.append([v,math.inf])
        return self.interval

class PICEA:
    def __init__(self, constructor, genetic_operator, objectives, N = 10, Ng = 10, cArch = 10):
        self.N = N # number of solutions
        self.Ng = Ng # number of goals
        self.cArch = cArch
        self.S : list[Solution_Vector] = []
        self.G : list[Goal_Vector] = []
        self.archive : list[Solution_Vector] = []
        self.genetic_operator = genetic_operator
        self.objectives = objectives
        self.M = len(self.objectives)

        self.init_sol(constructor)
    
    def init_sol(self, constructor):
        S = []
        for _ in range(self.N):
            S.append(constructor())
        self.S = [Solution_Vector(s, self.objectives) for s in S]
        self.updateArchive(self.S)
        self.gBounds = self.goalBound(self.S)
        self.G = self.goalGenerator(self.gBounds)

    def updateArchive(self, FSnd):
        FS = self.getNonDominantedSolutions(FSnd)
        #FS = FSnd
        kd_FS = KD_Tree(FS)
        for s in self.archive:
            s.restart()
            dominated = kd_FS.search(s.get_interval())
            for fs_i in dominated:
                fs_i.increase_domination()

        add_to_archive = []
        for fs_i in FS:
            if fs_i.dominated == 0:
                add_to_archive.append(fs_i)
            fs_i.restart()
        kd_archive = KD_Tree(self.archive)

        for new_s in add_to_archive:
            dominated = kd_archive.search(new_s.get_interval())
            for fs_i in dominated:
                fs_i.increase_domination()

        updated_archive = []
        for fs_a in self.archive:
            if fs_a.dominated == 0:
                updated_archive.append(fs_a)
        updated_archive.extend(add_to_archive)
        
        # não é preciso calcular a matrix de todas as vezes
        if len(updated_archive) > self.cArch:

            matrix_dist = []
            valid_dist = []
            # da para calcular isto metade das vezes
            for a in updated_archive:
                line_dist = []
                line_valid = []
                for b in updated_archive:
                    if a == b:
                        line_dist.append(math.inf)
                    else:
                        line_dist.append(np.linalg.norm(np.array(a.get_value())-np.array(b.get_value())))
                    line_valid.append(True)
                matrix_dist.append(line_dist)
                valid_dist.append(line_valid)
            to_remove = None
            while len(updated_archive) > self.cArch:

                possible = []
                for i in range(len(updated_archive)):
                    possible.append(i)
                while len(possible) != 1:
                    used = []
                    next_possible = []
                    min_dist = math.inf
                    for a in possible:
                        min_v = math.inf
                        min_b = None
                        for b in range(len(updated_archive)):
                            if matrix_dist[a][b] < min_v and valid_dist[a][b]:
                                min_v = matrix_dist[a][b]
                                min_b = b
                        if min_v < min_dist:
                            next_possible = [a]
                            used = [(a,min_b)]
                            min_dist = min_v
                        elif min_v == min_dist:
                            next_possible.append(a)
                            used.append((a,min_b))
                    possible = next_possible
                    for (a,b) in used:
                        valid_dist[a][b] = False
                
                to_remove = possible[0]
                updated_archive.pop(to_remove)
            
            matrix_dist.pop(to_remove)
            valid_dist.pop(to_remove)
            for i in range(len(matrix_dist)):
                matrix_dist[i].pop(to_remove)
                valid_dist[i].pop(to_remove)

        self.archive = updated_archive
    
    def goalBound(self, FS, alpha = 1.2):
        M = self.M
        gmin = [math.inf] * M
        gmax = [-math.inf] * M
        for s in FS:
            for i in range(M):
                if s.get_value()[i] < gmin[i]:
                    gmin[i] = s.get_value()[i]
                if s.get_value()[i] > gmax[i]:
                    gmax[i] = s.get_value()[i]
        for i in range(M):
            gmax[i] = gmin[i] + alpha * (gmax[i] - gmin[i])
        return gmin, gmax
    
    def goalGenerator(self, gBounds):
        goals = []
        gmin, gmax = gBounds
        for _ in range(self.Ng):
            goals_value = []
            for i in range(len(gmin)):
                goals_value.append(random.random() * (gmax[i] - gmin[i]) + gmin[i])
            goals.append(Goal_Vector(goals_value))
        return goals
        
    def fitnessAssignment(self, S, G):
        kd = KD_Tree(G)
        for sg in S + G:
            sg.restart()

        for s in S:
            dominated = kd.search(s.get_interval())
            for g in dominated:
                g.increase_domination()
                s.dominate(g)

        for s in S:
            fitness = 0
            for g in s.domination:
                fitness += 1.0/g.dominated
            s.fitness = fitness

        for g in G:
            y = 1 if g.dominated == 0 else (g.dominated - 1)/(2*self.N - 1)
            fitness = 1.0 / (1 + y)
            g.fitness = fitness
    
    def getNonDominantedSolutions(self, S):
        kd = KD_Tree(S)
        for s in S:
            s.restart()
        for s in S:
            dominated = kd.search(s.get_interval())
            for sd in dominated:
                if sd == s:
                    continue
                sd.increase_domination()
                s.dominate(sd)
        non_dominated = []
        for s in S:
            if s.dominated == 0:
                non_dominated.append(s)
        return non_dominated
    
    def getNextSolutions(self, Snd, JointS): 
        Sn = None
        if len(Snd) < self.N: #non-dominated solutions less than N
            max_fitness = max(JointS, key= lambda s : s.fitness).fitness
            for s in Snd:
                s.fitness = max_fitness
            JointS = sorted(JointS, key = lambda s : s.fitness, reverse=True)
            Sn = JointS[:self.N]
        else:
            Snd = sorted(Snd, key = lambda s : s.fitness, reverse=True)
            Sn = Snd[:self.N]
        return Sn

    def getNextGoals(self, JointG):
        Gn = None
        Gn = sorted(JointG, key = lambda g : g.fitness, reverse=True)
        Gn = Gn[:self.Ng]
        return Gn

    def geneticOperator(self, mating = False, scaling = None): # gerar offsprings, a modificar
        Sc = []
        for s1 in self.S:
            s2 = None
            if not mating:
                s2 = random.choice(self.S)
            else:
                prob = []
                for s in self.S:
                    if s == s1:
                        prob.append(0)
                    else:
                        prob.append(s1.solution.get_distance(s.solution))
                sum_prob = sum(prob)
                if scaling:
                    avg = sum_prob/len(prob)
                    a = (scaling * avg - avg)/(max(prob) - avg)
                    b = a * avg -avg
                    prob = [a * p - b for p in prob]
                min_p = min(prob)
                prob = [p - min_p for p in prob]
                sum_prob = sum(prob)
                prob = [p/sum_prob for p in prob]
                s2 = np.random.choice(self.S, p=prob)
            offspring = self.genetic_operator(s1.solution,s2.solution)
            Sc.append(Solution_Vector(offspring, self.objectives))
        return Sc

    def run(self, max_iter = 100, mr = True):
        for _ in range(max_iter):
            print(_)
            Sc = self.geneticOperator(mr, 2)
            JointS = self.S + Sc
            Gc = self.goalGenerator(self.gBounds)
            JointG = self.G + Gc
            self.fitnessAssignment(JointS, JointG)
            Snd = self.getNonDominantedSolutions(JointS)

            self.S = self.getNextSolutions(Snd, JointS)
            self.G = self.getNextGoals(JointG)
            self.updateArchive(self.S)
            self.gBounds = self.goalBound(self.S)

            gc.collect()

        for p in self.S:
            print(p.get_solution(), " -> ", p.get_value())
        
    def get_archive_front(self):
        return [s.get_value() for s in self.archive]
    
    def get_archive(self):
        return self.archive

    def interact(self):
        print("Press 2 objectives to visualize (q to quit):")

        while True:
            for i in range(len(self.objectives)):
                print("f" + str(i))
            i1 = input("Objective 1: ")
            if i1 == "q":
                break
            else:
                i1 = int(i1)
                if i1 < 0 or i1 >= len(self.objectives):
                    break
            i2 = input("Objective 2: ")
            if i2 == "q":
                break
            else:
                i2 = int(i2)
                if i2 < 0 or i2 >= len(self.objectives):
                    break

            for p in self.get_archive_front():
                plt.plot(p[i1],p[i2],'o', color='red',alpha=0.2,markersize=2)
            plt.show()

    def dump(self):
        to_dump = []
        values = []
        for s in self.archive:
            sol = s.get_solution()
            to_dump.append(sol.dump())
        for s in self.archive:
            values.append(s.get_value())
        return {'sols': to_dump, 'vals': values}