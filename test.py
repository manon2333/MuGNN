import torch
import torch.nn.functional as F
import numpy as np
from scipy import spatial
from tools.print_time_info import print_time_info
from torch import nn
import random

a = set(list(range(10))).remove(3)
print(a)
exit()
print(random.sample(a, k=2))
exit()
a = set(list(range(10)))
a = set(str(i) for i in a)
a.remove('1')
a.remove('2')
print(a)
exit()
print(loss(b, a, torch.tensor([-1], dtype=torch.double)))

# print(b * a)
exit()

def get_hits(sr_embedding, tg_embedding, top_k=(1, 10, 50, 100)):
    test_num = len(sr_embedding)
    Lvec = sr_embedding
    Rvec = tg_embedding
    sim = spatial.distance.cdist(Lvec, Rvec, metric='cityblock')
    print(sim)
    top_lr = [0] * len(top_k)
    for i in range(Lvec.shape[0]):
        rank = sim[i, :].argsort()
        print(rank)
        print(np.where(rank == i))
        # exit()
        rank_index = np.where(rank == i)[0][0]
        print(rank_index)
        # exit()
        for j in range(len(top_k)):
            if rank_index < top_k[j]:
                top_lr[j] += 1
    top_rl = [0] * len(top_k)
    for i in range(Rvec.shape[0]):
        rank = sim[:, i].argsort()
        rank_index = np.where(rank == i)[0][0]
        for j in range(len(top_k)):
            if rank_index < top_k[j]:
                top_rl[j] += 1
    print_time_info('For each source:')
    for i in range(len(top_lr)):
        print_time_info('Hits@%d: %.2f%%' % (top_k[i], top_lr[i] / test_num * 100))
    print('')
    print_time_info('For each target:')
    for i in range(len(top_rl)):
        print_time_info('Hits@%d: %.2f%%' % (top_k[i], top_rl[i] / test_num * 100))
    # return Hits@10
    return (top_lr[1] / test_num * 100, top_rl[1] / test_num * 100)

a = np.asarray([[1,2,3], [2, 3, 4], [1, 1, 3]])
b = np.asarray([[1,2,3], [2, 3, 4], [1, 1, 3]])

r = get_hits(a, b)