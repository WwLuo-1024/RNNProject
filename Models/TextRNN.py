import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np

#配置文件
class Config(object):
    """配置参数"""
    def __init__(self, dataset, embedding):
        self.model_name = 'TextRNN'
        self.train_path = dataset + 'data/train_txt' #训练集
        self.dev_path = dataset + '/data/dev.txt'    #验证集
        self.test_path = dataset + '/data/test.txt'  #测试集
        self.class_list = [x.strip() for x in open(
            dataset + '/data/class.txt').readlines()] #类别名单
        self.vocab_path = dataset + '/data/vocab.pkl' #词表
        self.save_path = dataset + '/saved_dict/' + self.model_name + 'ckpt' #模型训练结果
        self.log_path = dataset + '/log/' + self.model_name
        self.embedding_pretrained = torch.tensor(
            np.load(dataset + '/data/' + embedding)["embedding"].astype('float32'))\
            if embedding != 'random' else None #预训练词向量
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu') #是否启动cuda设备训练

        self.dropout = 0.5                      #随机失活
        self.require_improvement = 1000         #若超过1000batch效果还没提升，则提前结束训练】
        self.num_classes = len(self.class_list) #类别数
        self.n_vocab = 0                        #词表大小，在运行时赋值
        self.num_epochs = 10                    #训练轮次
        self.batch_size = 128                   #批次mini_batch大小
        self.pad_size = 32                      #每句话处理成的长度（短填充，长切断）
        self.learning_rate = 1e-3               #学习率
        self.embed = self.embedding_pretrained.size(1)\
            if self.embedding_pretrained is not None else 300 #字向量维度，若使用了预训练词向量，则维度统一
        self.hidden_size = 128                  #LSTM隐藏层
        self.num_layers = 2                     #LSTM层数


#搭建网络
class Model(nn.Module):
    def __init__(self, config):
        super(Model, self).__init__()
        if config.embedding_pretrained is not None:
            self.embedding = nn.Embedding.from_pretrained(config.embedding_pretrained, freeze = False)
        else:
            self.embedding = nn.Embedding(config.n_vocab, config.embed, padding_idx = config.n_vocab - 1)
        self.lstm = nn.LSTM(config.embed, config.hidden_size, config.num_layers, #词向量维度，隐藏层神经元个数，隐藏层数
                            bidirectional = True, batch_first = True, dropout = config.dropout) #bidirecctional是否采取双向LSTM
        self.fc = nn.Linear(config.hidden_size * 2, config.num_classes) #由于双向LSTM，所以全连接层的神经元个数需要乘以2

    def forward(self, x):
        x, _ = x
        out = self.embedding(x)
        out, _ = self.lstm(out) #输出结果和隐藏状态，此时只需要最终结果（也就是ht)
        out = self.fc(out[:, -1, :]) #句子最后时刻的hidden state
        return out