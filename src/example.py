import random

from matplotlib import pyplot as plt

from picea import PICEA

random.seed(10)

def f2(sol):
    [x1,x2] = sol
    return x1**4 + x2**4 + x1*x2 - (x1*x2)**2

def f1(sol):
    [x1,_] = sol
    return f2(sol) - 10*x1**2

def f3(sol):
    [x1,x2] = sol
    return x1 + x2 + x1*x2 - x2**2

def constructor():
    x1 = (random.random()-0.5)*4
    x2 = (random.random()-0.5)*4
    return [x1,x2]

def geneticOperator(sol1,sol2):
    offspring = []
    for i in range(len(sol1)):
        min_v = min(sol1[i], sol2[i])
        max_v = max(sol1[i], sol2[i])
        d = (max_v-min_v) + (random.random() - 0.5) * 0.1
        v = random.random() * d + min_v + (random.random() - 0.5) * d
        offspring.append(v)
    return offspring

pc = PICEA(constructor, geneticOperator, [f1,f2, f3], N=150, Ng=300, cArch=300)

pc.run(200)

#pc.interact()

points = pc.get_archive_front()

xs = [i[0] for i in points]
ys = [i[1] for i in points]
zs = [i[2] for i in points]

ax = plt.axes(projection='3d')
ax.scatter3D(xs,ys,zs, points[::][2])
plt.show()
