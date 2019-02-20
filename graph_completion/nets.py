import torch.nn as nn
import torch.nn.functional as F
from graph_completion.models import GCN
from graph_completion.layers import DoubleEmbedding
from graph_completion.CrossAdjacencyMatrix import CrossAdjacencyMatrix
from graph_completion.CrossGraphCompletion import CrossGraphCompletion
from graph_completion.functions import cosine_similarity_nbyn
from scipy.optimize import linear_sum_assignment


class AlignGraphNet(nn.Module):
    def __init__(self, dropout_rate=0.5, non_acylic=False, cuda=True):
        super(AlignGraphNet, self).__init__()
        self.is_cuda = cuda
        self.non_acylic = non_acylic
        self.dropout_rate = dropout_rate

    def predict(self, sr_data, tg_data):
        raise NotImplementedError

    def bootstrap(self, *args):
        raise NotImplementedError

class GATNet(AlignGraphNet):
    def __init__(self, *args, **kwargs):
        super(GATNet, self).__init__(*args, **kwargs)


class GCNNet(AlignGraphNet):
    def __init__(self, cgc, num_layer, dim, *args, **kwargs):
        super(GCNNet, self).__init__(*args, **kwargs)
        assert isinstance(cgc, CrossGraphCompletion)
        self.cam = CrossAdjacencyMatrix(dim, cgc, self.cuda, non_acylic=self.non_acylic)
        self.gcn = GCN(dim, num_layer, self.dropout_rate)
        self.entity_embedding = DoubleEmbedding(len(cgc.id2entity_sr), len(cgc.id2entity_tg), dim)
        self.relation_embedding = DoubleEmbedding(len(cgc.id2relation_sr), len(cgc.id2relation_tg), dim)

    def forward(self, sr_data, tg_data, sr_rel_data, tg_rel_data):
        adjacency_matrix_sr, adjacency_matrix_tg = self.cam(*self.relation_embedding.weight)
        graph_embedding_sr, graph_embedding_tg = self.entity_embedding.weight
        graph_embedding_sr = self.gcn(graph_embedding_sr, adjacency_matrix_sr)
        graph_embedding_tg = self.gcn(graph_embedding_tg, adjacency_matrix_tg)
        repre_e_sr = F.embedding(sr_data, graph_embedding_sr)
        repre_e_tg = F.embedding(tg_data, graph_embedding_tg)
        repre_r_sr, repre_r_tg = self.relation_embedding(sr_rel_data, tg_rel_data)
        return repre_e_sr, repre_e_tg, repre_r_sr, repre_r_tg

    def predict(self, sr_data, tg_data):
        adjacency_matrix_sr, adjacency_matrix_tg = self.cam(*self.relation_embedding.weight)
        graph_embedding_sr, graph_embedding_tg = self.entity_embedding.weight
        graph_embedding_sr = self.gcn(graph_embedding_sr, adjacency_matrix_sr)
        graph_embedding_tg = self.gcn(graph_embedding_tg, adjacency_matrix_tg)
        repre_e_sr = F.embedding(sr_data, graph_embedding_sr)
        repre_e_tg = F.embedding(tg_data, graph_embedding_tg)
        return repre_e_sr.cpu().detach().numpy(), repre_e_tg.cpu().detach().numpy()

    def bootstrap(self, entity_seeds, relation_seeds):
        adjacency_matrix_sr, adjacency_matrix_tg = self.cam()
        graph_embedding_sr, graph_embedding_tg = self.cam.entity_embedding_sr.weight, self.cam.entity_embedding_tg.weight
        for gcn in self.gcn_list:
            graph_embedding_sr = gcn(graph_embedding_sr, adjacency_matrix_sr)
            graph_embedding_tg = gcn(graph_embedding_tg, adjacency_matrix_tg)
        rel_embedding_sr, rel_embedding_tg = self.cam.relation_embedding_sr.weight, self.cam.relation_embedding_tg.weight
        sim_graph_embedding = cosine_similarity_nbyn(graph_embedding_sr, graph_embedding_tg).cpu().detatch().numpy()
        sim_rel_embedding = cosine_similarity_nbyn(rel_embedding_sr, rel_embedding_tg).cpu().detatch().numpy()
        e_rows, e_cols = linear_sum_assignment(sim_graph_embedding)
        r_rows, r_cols = linear_sum_assignment(sim_rel_embedding)
