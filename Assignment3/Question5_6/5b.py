# -*- coding: utf-8 -*-
"""5b.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1s4IVJAP2pOQCzFSMok2vVM6xNJzEOLFE

Question 5:

Run the below cell to mount the google drive you might have stored the dataset
"""

from google.colab import drive
drive.mount('/content/drive')

!pip install wandb

"""Run the below cell to import packages and also define attention class"""

import numpy as np
import tensorflow as tf
import random
from tensorflow import keras
from tensorflow.keras.utils import plot_model
import tensorflow as tf
import os
import wandb
from tensorflow.python.keras.layers import Layer
from tensorflow.python.keras import backend as K

class AttentionLayer(Layer):
    """
    This class implements Bahdanau attention (https://arxiv.org/pdf/1409.0473.pdf).
    There are three sets of weights introduced W_a, U_a, and V_a
     """

    def __init__(self, **kwargs):
        super(AttentionLayer, self).__init__(**kwargs)

    def build(self, input_shape):
        assert isinstance(input_shape, list)
        # Create a trainable weight variable for this layer.

        self.W_a = self.add_weight(name='W_a',
                                   shape=tf.TensorShape((input_shape[0][2], input_shape[0][2])),
                                   initializer='uniform',
                                   trainable=True)
        self.U_a = self.add_weight(name='U_a',
                                   shape=tf.TensorShape((input_shape[1][2], input_shape[0][2])),
                                   initializer='uniform',
                                   trainable=True)
        self.V_a = self.add_weight(name='V_a',
                                   shape=tf.TensorShape((input_shape[0][2], 1)),
                                   initializer='uniform',
                                   trainable=True)

        super(AttentionLayer, self).build(input_shape)  # Be sure to call this at the end

    def call(self, inputs, verbose=False):
        """
        inputs: [encoder_output_sequence, decoder_output_sequence]
        """
        assert type(inputs) == list
        encoder_out_seq, decoder_out_seq = inputs
        if verbose:
            print('encoder_out_seq>', encoder_out_seq.shape)
            print('decoder_out_seq>', decoder_out_seq.shape)

        def energy_step(inputs, states):
            """ Step function for computing energy for a single decoder state
            inputs: (batchsize * 1 * de_in_dim)
            states: (batchsize * 1 * de_latent_dim)
            """

            assert_msg = "States must be an iterable. Got {} of type {}".format(states, type(states))
            assert isinstance(states, list) or isinstance(states, tuple), assert_msg

            """ Some parameters required for shaping tensors"""
            en_seq_len, en_hidden = encoder_out_seq.shape[1], encoder_out_seq.shape[2]
            de_hidden = inputs.shape[-1]

            """ Computing S.Wa where S=[s0, s1, ..., si]"""
            # <= batch size * en_seq_len * latent_dim
            W_a_dot_s = K.dot(encoder_out_seq, self.W_a)

            """ Computing hj.Ua """
            U_a_dot_h = K.expand_dims(K.dot(inputs, self.U_a), 1)  # <= batch_size, 1, latent_dim
            if verbose:
                print('Ua.h>', U_a_dot_h.shape)

            """ tanh(S.Wa + hj.Ua) """
            # <= batch_size*en_seq_len, latent_dim
            Ws_plus_Uh = K.tanh(W_a_dot_s + U_a_dot_h)
            if verbose:
                print('Ws+Uh>', Ws_plus_Uh.shape)

            """ softmax(va.tanh(S.Wa + hj.Ua)) """
            # <= batch_size, en_seq_len
            e_i = K.squeeze(K.dot(Ws_plus_Uh, self.V_a), axis=-1)
            # <= batch_size, en_seq_len
            e_i = K.softmax(e_i)

            if verbose:
                print('ei>', e_i.shape)

            return e_i, [e_i]

        def context_step(inputs, states):
            """ Step function for computing ci using ei """

            assert_msg = "States must be an iterable. Got {} of type {}".format(states, type(states))
            assert isinstance(states, list) or isinstance(states, tuple), assert_msg

            # <= batch_size, hidden_size
            c_i = K.sum(encoder_out_seq * K.expand_dims(inputs, -1), axis=1)
            if verbose:
                print('ci>', c_i.shape)
            return c_i, [c_i]

        fake_state_c = K.sum(encoder_out_seq, axis=1)
        fake_state_e = K.sum(encoder_out_seq, axis=2)  # <= (batch_size, enc_seq_len, latent_dim

        """ Computing energy outputs """
        # e_outputs => (batch_size, de_seq_len, en_seq_len)
        last_out, e_outputs, _ = K.rnn(
            energy_step, decoder_out_seq, [fake_state_e],
        )

        """ Computing context vectors """
        last_out, c_outputs, _ = K.rnn(
            context_step, e_outputs, [fake_state_c],
        )

        return c_outputs, e_outputs

    def compute_output_shape(self, input_shape):
        """ Outputs produced by the layer """
        return [
            tf.TensorShape((input_shape[1][0], input_shape[1][1], input_shape[1][2])),
            tf.TensorShape((input_shape[1][0], input_shape[1][1], input_shape[0][1]))
        ]

"""Before running the next cell

*   upload config.py associated to attention model to the notebook

*   Make necessary path changes

*   Run the next cell to run some necessary utils









"""

config = {
  'train_path' : '/content/drive/MyDrive/dl_cs6910/assignment3/dakshina_dataset_v1.0/hi/lexicons/hi.translit.sampled.train.tsv',
  'val_path' : '/content/drive/MyDrive/dl_cs6910/assignment3/dakshina_dataset_v1.0/hi/lexicons/hi.translit.sampled.dev.tsv',
  'test_path' : '/content/drive/MyDrive/dl_cs6910/assignment3/dakshina_dataset_v1.0/hi/lexicons/hi.translit.sampled.test.tsv',
  'hidden_layer_size':128,
  'num_encoder':1,
  'num_decoder':1,
  'embedding_size':16,
  'celltype':"gru",
  'dropout':0.2,
  'beam_size':6,
  'batch_size':64,
  'epoch':30
}

configuration = config
model_folder ="model"#'./content/drive/MyDrive/dl_cs6910/assignment3//model'

train_text =[]
val_text =[]
test_text = []

train_target_text =[]
val_target_text = []
test_target_text = []

train_inp = set()
val_inp = set()
test_inp = set()

train_tar = set()
val_tar = set()
test_tar = set()

with open(configuration.get("train_path"),'r') as f:
  lines = f.read().split("\n")
  for line in lines:
    try:
      target_text,input_text,  _ = line.split("\t")
    except:
      continue
    target_text = "\t" + target_text + "\n"

    train_text.append(input_text)
    train_target_text.append(target_text)

    for char in input_text:
        if char not in train_inp:
            train_inp.add(char)
    for char in target_text:
        if char not in train_tar:
            train_tar.add(char)


with open(configuration.get("val_path"),'r') as f:
  lines = f.read().split("\n")
  
  for line in lines:
    try:
      target_text, input_text, _ = line.split("\t")
    except:
      continue
    #input_text, target_text, _ = line.split("\t")
    target_text = "\t" + target_text + "\n"

    val_text.append(input_text)
    val_target_text.append(target_text)

    for char in input_text:
        if char not in val_inp:
            val_inp.add(char)
    for char in target_text:
        if char not in val_tar:
            val_tar.add(char)

with open(configuration.get("test_path"),'r') as f:
  lines = f.read().split("\n")
  
  for line in lines:
    try:
       target_text,input_text, _ = line.split("\t")
    except:
      continue
    #input_text, target_text, _ = line.split("\t")
    target_text = "\t" + target_text + "\n"

    test_text.append(input_text)
    test_target_text.append(target_text)

    for char in input_text:
        if char not in test_inp:
            test_inp.add(char)
    for char in target_text:
        if char not in test_tar:
            test_tar.add(char)

def encoding(text, target_text):
  decoder_target_data = np.zeros((len(text), 21,65 ), dtype="float32")
  encoder_input_data = np.zeros((len(text), 20), dtype="float32")
  decoder_input_data = np.zeros((len(text), 21), dtype="float32")

  for i, (input, target) in enumerate(zip(text, target_text)):
    for t, char in enumerate(input):
        encoder_input_data[i, t] = input_token_index[char]
    encoder_input_data[i, t + 1 :] =  input_token_index[" "]
    for t, char in enumerate(target):
        decoder_input_data[i, t] = target_token_index[char]
        if t > 0:
            decoder_target_data[i, t - 1, target_token_index[char]] = 1.0
    decoder_input_data[i, t + 1 :] =  target_token_index["\n"]
    decoder_target_data[i, t:, target_token_index["\n"]] = 1.0

  return decoder_target_data, encoder_input_data, decoder_input_data

"""Run the next cell to train the model"""

config=configuration
class RNN():
  def __init__(self):
    self.epoch =30 
    self.batch_size = 256
    self.num_encoder_tokens = len(train_inp)+1#vocab size 
    self.num_decoder_tokens = len(train_tar)#vocab size
    self.max_encoder_seq_length = max([len(txt) for txt in train_text])
    self.max_decoder_seq_length = max([len(txt) for txt in train_target_text])
    self.input_token_index={'u': 0, 's': 1, 'b': 2, 'p': 3, 'k': 4, 'o': 5, 'v': 6, 'x': 7, 'r': 8, 'a': 9, 'h': 10, 'd': 11, 'z': 12, 'f': 13, 'n': 14, 'l': 15, 'g': 16, 'c': 17, 'y': 18, 'm': 19, 'w': 20, 'j': 21, 'q': 22, 'i': 23, 't': 24, 'e': 25, ' ': 26}
    self.target_token_index={'ई': 0, 'ङ': 1, 'ा': 2, 'ओ': 3, 'ट': 4, 'ध': 5, 'म': 6, 'फ': 7, 'द': 8, 'आ': 9, 'ं': 10, 'घ': 11, 'े': 12, 'ः': 13, 'श': 14, 'ॅ': 15, 'ग': 16, 'झ': 17, 'स': 18, 'ऐ': 19, '्': 20, 'न': 21, 'च': 22, '़': 23, 'ह': 24, 'ब': 25, 'ख': 26, 'थ': 27, 'औ': 28, 'ऋ': 29, 'य': 30, 'ढ': 31, 'ठ': 32, 'ड': 33, 'ऊ': 34, 'व': 35, 'इ': 36, 'ॉ': 37, 'छ': 38, 'ै': 39, 'ष': 40, 'ए': 41, 'ण': 42, 'ऑ': 43, 'त': 44, 'ु': 45, 'ो': 46, '\n': 47, 'प': 48, '\t': 49, 'र': 50, 'ृ': 51, 'अ': 52, 'ञ': 53, 'ू': 54, 'ज': 55, 'उ': 56, 'ी': 57, 'ौ': 58, 'ि': 59, 'ॐ': 60, 'ल': 61, 'क': 62, 'ँ': 63, 'भ': 64}

    self.train = self.encoding(train_text, train_target_text)
    self.validation = self.encoding(val_text, val_target_text)
    self.embedding_size = 16 
    self.celltype = "gru"
    self.number_encoder_layer= 1 
    self.number_decoder_layer= 1
    self.hidden_layers = 256
    self.lr = 0.01
    self.beam_size= 1
    self.dr= .2
    print("total epoch: ",self.epoch)



    self.reverse_token_index, self.reverse_target_index = self.reverse_character_maps()

    self.tab_index=self.target_token_index['\t']

    print(self.tab_index,self.target_token_index['\n'])

  # @tf.function
  def map_characters(self):
    input_token_index = dict([(char, i) for i, char in enumerate(train_inp)])
    target_token_index = dict([(char, i) for i, char in enumerate(train_tar)])
    input_token_index[" "] = len(input_token_index)
    print(input_token_index)
    print(target_token_index)
    return input_token_index, target_token_index

  # @tf.function
  def reverse_character_maps(self):
    reverse_token_index = dict([( i,char) for char,i in self.input_token_index.items()])
    reverse_target_index = dict([( i,char) for char,i in self.target_token_index.items()])

    return reverse_token_index, reverse_target_index

  # @tf.function
  
  def encoding(self,text, target_text):
    decoder_target_data = np.zeros((len(text), self.max_decoder_seq_length, self.num_decoder_tokens), dtype="float32")
    encoder_input_data = np.zeros((len(text), self.max_encoder_seq_length), dtype="float32")
    decoder_input_data = np.zeros((len(text), self.max_decoder_seq_length), dtype="float32")

    for i, (input, target) in enumerate(zip(text, target_text)):
      for t, char in enumerate(input):
          encoder_input_data[i, t] = self.input_token_index[char]
      encoder_input_data[i, t + 1 :] =  self.input_token_index[" "]
      for t, char in enumerate(target):
          decoder_input_data[i, t] = self.target_token_index[char]
          if t > 0:
              decoder_target_data[i, t - 1, self.target_token_index[char]] = 1.0
      decoder_input_data[i, t + 1 :] =  self.target_token_index["\n"]
      decoder_target_data[i, t:, self.target_token_index["\n"]] = 1.0

    return decoder_target_data, encoder_input_data, decoder_input_data
    


  # @tf.function
  
  def loss(self,x1,x2,y_true,training):
    y_predict = self.model([x1,x2],training)
    return y_predict,self.cce(y_true,y_predict)

  # @tf.function
  
  def grad(self, input1,input2, targets,training):
    with tf.GradientTape() as tape:
      logits,loss_value = self.loss( input1,input2, targets, training)
    return logits,loss_value, tape.gradient(loss_value, self.model.trainable_variables)

  # @tf.function
  def optimize(self,loss_tensor):
    opt = tf.keras.optimizers.Adam(learning_rate=self.lr)
    #opt = tf.keras.optimizers.RMSprop(learning_rate=self.lr)
    train_op = opt.minimize(loss_tensor)

    return train_op

  # @tf.function
  
  def fill_feed_dict(self,dataset):
    target_output_data= dataset[0]
    train_data = dataset[1]
    target_data = dataset[2]

    start = [random.randint(0,train_data.shape[0]-1) for i in range(self.batch_size) ]

    encoder_input_data = train_data[start,:]
    decoder_input_data = target_data[start,:]
    decoder_output_data = target_output_data[start,:,:]


    return encoder_input_data, decoder_input_data,decoder_output_data,start

  # @tf.function
  
  def greedy_search(self,predictions):
    return tf.cast(tf.argmax(predictions, axis=-1), tf.int32)

  # @tf.function
  
  def get_accuracy(self,prediction,start,type_):

    #result_text = []
    count =0
    print(type_)
    for i in range(prediction.shape[0]):
      string=''
      for j in range(prediction.shape[1]):
        if ((prediction[i,j] ==self.target_token_index['\n']) or (prediction[i,j] ==self.tab_index)):
          break;
          
        else:
          string = string + self.reverse_target_index[prediction[i,j]]
          
      if(type_=="train"):
        
        if(string == train_target_text[start[i]][1:-1]):
          count +=1
      elif(type_=="val"):
        
        if(string == val_target_text[start[i]][1:-1]):
          count +=1

      



    return count/prediction.shape[0]

  # @tf.function
  
  def beam_search_function(self,predictions):

    result,indices = tf.nn.top_k(predictions, self.beam_size)
    log_result = tf.math.log(result)

    y_pred = np.zeros((log_result.shape[0],self.max_decoder_seq_length ))

    for i in range(result.shape[0]):
      for j in range(result.shape[1]):
        if(j==0):
          pred = np.max(log_result[i,j,:].numpy())
          y_pred[i,j] = int(indices.numpy()[i,j,np.argmax(log_result[i,j,:].numpy()) ])
        else:
          pred_ = pred + log_result[i,j,:].numpy()
          pred = np.max(pred_)
          y_pred[i,j] =  int(indices.numpy()[i,j, np.argmax(pred_)] )
    return y_pred


  def rnn_model(self, e_input, d_input):

      encoder_input = keras.Input(shape=(self.max_encoder_seq_length),batch_size=self.batch_size)

      decoder_input = keras.Input(shape=(self.max_decoder_seq_length),batch_size=self.batch_size)

      
      input_embedding=tf.keras.layers.Embedding(input_dim=self.num_encoder_tokens, output_dim=self.embedding_size,input_length=self.max_encoder_seq_length)
      e_embedding_output =input_embedding(e_input)
      
      output_embedding = tf.keras.layers.Embedding(self.num_decoder_tokens, self.embedding_size, input_length=self.max_decoder_seq_length)
      d_embedding_output =output_embedding(d_input)

      encoder = tf.keras.layers.SimpleRNN(self.hidden_layers,return_sequences=True, return_state=True,dropout = self.dr)

      output, state = encoder(e_embedding_output)

      for i in range(self.number_encoder_layer-1):
        encoder = tf.keras.layers.SimpleRNN(self.hidden_layers,return_sequences=True, return_state=True,dropout = self.dr)

        output, state = encoder(output)


      ee_i = input_embedding(encoder_input)
      encoder_inf_out, encoder_inf_state = encoder(ee_i)

      self.encoder_model = tf.keras.Model(inputs=encoder_input, outputs=[encoder_inf_out, encoder_inf_state])

      encoder_inf_output = keras.Input(batch_shape=(self.batch_size, self.max_encoder_seq_length,self.hidden_layers), name='encoder_inf_states')
      decoder_init_state = keras.Input(batch_shape=(self.batch_size, self.hidden_layers), name='decoder_init')

      decoder= tf.keras.layers.SimpleRNN(self.hidden_layers,return_sequences=True, return_state=True)

      d_output, d_state = decoder(d_embedding_output, initial_state=[state])


      for i in range(self.number_decoder_layer-1):
        decoder = tf.keras.layers.SimpleRNN(self.hidden_layers,return_sequences=True, return_state=True)

        d_output, d_state = decoder(d_output,initial_state=[state])

      attention_layer = AttentionLayer()
      attn_out, attn_states = attention_layer([output, d_output])
      decoder_concat_input = tf.keras.layers.Concatenate(axis=-1, name='concat_layer')([d_output, attn_out])



  def gru_model(self,e_input, d_input):

      encoder_input = keras.Input(shape=(self.max_encoder_seq_length),batch_size=self.batch_size)

      decoder_input = keras.Input(shape=(self.max_decoder_seq_length),batch_size=self.batch_size)

      
      input_embedding=tf.keras.layers.Embedding(input_dim=self.num_encoder_tokens, output_dim=self.embedding_size,input_length=self.max_encoder_seq_length)
      e_embedding_output =input_embedding(e_input)
      
      output_embedding = tf.keras.layers.Embedding(self.num_decoder_tokens, self.embedding_size, input_length=self.max_decoder_seq_length)
      d_embedding_output =output_embedding(d_input)

      encoder = tf.keras.layers.GRU(self.hidden_layers,return_sequences=True, return_state=True,dropout = self.dr)

      output, state = encoder(e_embedding_output)

      for i in range(self.number_encoder_layer-1):
        encoder = tf.keras.layers.GRU(self.hidden_layers,return_sequences=True, return_state=True,dropout = self.dr)

        output, state = encoder(output)


      ee_i = input_embedding(encoder_input)
      encoder_inf_out, encoder_inf_state = encoder(ee_i)

      self.encoder_model = tf.keras.Model(inputs=encoder_input, outputs=[encoder_inf_out, encoder_inf_state])

      encoder_inf_output = keras.Input(batch_shape=(self.batch_size, self.max_encoder_seq_length,self.hidden_layers), name='encoder_inf_states')
      decoder_init_state = keras.Input(batch_shape=(self.batch_size, self.hidden_layers), name='decoder_init')

      decoder= tf.keras.layers.GRU(self.hidden_layers,return_sequences=True, return_state=True)

      d_output, d_state = decoder(d_embedding_output, initial_state=[state])


      for i in range(self.number_decoder_layer-1):
        decoder = tf.keras.layers.GRU(self.hidden_layers,return_sequences=True, return_state=True)

        d_output, d_state = decoder(d_output,initial_state=[state])

      attention_layer = AttentionLayer()
      attn_out, attn_states = attention_layer([output, d_output])
      decoder_concat_input = tf.keras.layers.Concatenate(axis=-1, name='concat_layer')([d_output, attn_out])




      decoder_dense = tf.keras.layers.Dense(self.num_decoder_tokens, activation="softmax")

      decoder_outputs = decoder_dense(decoder_concat_input)

      de_i = output_embedding(decoder_input)
      decoder_inf_out, decoder_inf_state = decoder(de_i, initial_state=decoder_init_state)
      attn_inf_out, attn_inf_states = attention_layer([encoder_inf_output, decoder_inf_out])
      decoder_inf_concat = tf.keras.layers.Concatenate(axis=-1, name='concat')([decoder_inf_out, attn_inf_out])
      dense_output = decoder_dense(decoder_inf_concat)


      self.decoder_model = tf.keras.Model(inputs=[encoder_inf_output, decoder_init_state, decoder_input],
                            outputs=[dense_output, attn_inf_states, decoder_inf_state])

      return decoder_outputs, d_state,attn_states




  def lstm_model(self,e_input, d_input):

      encoder_input = keras.Input(shape=(self.max_encoder_seq_length),batch_size=self.batch_size)

      decoder_input = keras.Input(shape=(self.max_decoder_seq_length),batch_size=self.batch_size)

      
      input_embedding=tf.keras.layers.Embedding(input_dim=self.num_encoder_tokens, output_dim=self.embedding_size,input_length=self.max_encoder_seq_length)
      e_embedding_output =input_embedding(e_input)
      
      output_embedding = tf.keras.layers.Embedding(self.num_decoder_tokens, self.embedding_size, input_length=self.max_decoder_seq_length)
      d_embedding_output =output_embedding(d_input)

      encoder = tf.keras.layers.GRU(self.hidden_layers,return_sequences=True, return_state=True,dropout = self.dr)

      output, state = encoder(e_embedding_output)

      for i in range(self.number_encoder_layer-1):

        encoder = tf.keras.layers.GRU(self.hidden_layers,return_sequences=True, return_state=True,dropout = self.dr)

        output, state = encoder(output)


      ee_i = input_embedding(encoder_input)
      encoder_inf_out, encoder_inf_state = encoder(ee_i)

      self.encoder_model = tf.keras.Model(inputs=encoder_input, outputs=[encoder_inf_out, encoder_inf_state])

      encoder_inf_output = keras.Input(batch_shape=(self.batch_size, self.max_encoder_seq_length,self.hidden_layers), name='encoder_inf_states')
      decoder_init_state = keras.Input(batch_shape=(self.batch_size, self.hidden_layers), name='decoder_init')

      decoder= tf.keras.layers.GRU(self.hidden_layers,return_sequences=True, return_state=True)

      d_output, d_state = decoder(d_embedding_output, initial_state=[state])


      for i in range(self.number_decoder_layer-1):
        decoder = tf.keras.layers.GRU(self.hidden_layers,return_sequences=True, return_state=True)

        d_output, d_state = decoder(d_output,initial_state=[state])

      attention_layer = AttentionLayer()
      attn_out, attn_states = attention_layer([output, d_output])
      decoder_concat_input = tf.keras.layers.Concatenate(axis=-1, name='concat_layer')([d_output, attn_out])




      decoder_dense = tf.keras.layers.Dense(self.num_decoder_tokens, activation="softmax")

      decoder_outputs = decoder_dense(decoder_concat_input)

      de_i = output_embedding(decoder_input)
      decoder_inf_out, decoder_inf_state = decoder(de_i, initial_state=decoder_init_state)
      attn_inf_out, attn_inf_states = attention_layer([encoder_inf_output, decoder_inf_out])
      decoder_inf_concat = tf.keras.layers.Concatenate(axis=-1, name='concat')([decoder_inf_out, attn_inf_out])
      dense_output = decoder_dense(decoder_inf_concat)


      self.decoder_model = tf.keras.Model(inputs=[encoder_inf_output, decoder_init_state, decoder_input],
                            outputs=[dense_output, attn_inf_states, decoder_inf_state])

      return decoder_outputs, d_state,attn_states
    





  def run_training(self):
    with tf.device('/device:GPU:0'):


      input = keras.Input(shape=(self.max_encoder_seq_length),batch_size=self.batch_size)

      d_input = keras.Input(shape=(self.max_decoder_seq_length),batch_size=self.batch_size)



      if(self.celltype =="rnn"):

        decoder_outputs,state,attn =self.rnn_model(input,d_input)

      elif(self.celltype =="gru"): 

        decoder_outputs,state,attn =self.gru_model(input,d_input)


      elif(self.celltype =="lstm"): 

        decoder_outputs,state,attn =self.lstm_model(input,d_input)



      

      self.model = tf.keras.Model([input, d_input], [decoder_outputs,])
      final_model = self.model
      
      self.cce = tf.keras.losses.CategoricalCrossentropy(from_logits=True)

      self.opt = tf.keras.optimizers.Adam(learning_rate=self.lr)
      self.epoch_loss_avg = tf.keras.metrics.Mean()
      self.train_metric=train_acc_metric = keras.metrics.CategoricalAccuracy()
      self.val_metric=train_acc_metric = keras.metrics.CategoricalAccuracy()

      model_name = "both-bs-"+str(self.batch_size)+"-cell-"+self.celltype+"-es-"+str(self.embedding_size)+"-ne-"+str(self.number_encoder_layer)+"-nd-"+str(self.number_decoder_layer)+"-hl-"+str(self.hidden_layers)+"-dr-"+str(self.dr)+ 'model.png'

      plot_model(self.model, to_file= model_name)

      print(self.model.layers)
      for epoch in range(self.epoch):
        prediction_decoder_input = np.zeros(self.train[2].shape)

        prediction_decoder_input[:,0] = self.target_token_index["\t"] 

        val_prediction_decoder_input = np.zeros(self.validation[2].shape)
                                        #  --------------------------------------    
                                        # self.validation = self.encoding(val_text, val_target_text)
        val_prediction_decoder_input[:,0] = self.target_token_index["\t"]
        training_steps = int(self.train[1].shape[0]/self.batch_size)
        for step in range(training_steps):
            encoder_input_data, decoder_input_data,decoder_output_data,start  = self.fill_feed_dict(self.train)
            logits, loss_value, grads = self.grad(encoder_input_data, decoder_input_data,decoder_output_data,True)
            self.opt.apply_gradients(zip(grads, self.model.trainable_variables))

            self.epoch_loss_avg.update_state(loss_value)

            self.train_metric.update_state(decoder_output_data, logits)
        
            

        if( self.beam_size == 1):
            y_pred = self.greedy_search(logits)
            accuracy = self.get_accuracy(y_pred.numpy(),start,"train")
        else:
            y_pred = self.beam_search_function(logits)
            accuracy = self.get_accuracy(y_pred,start,"train")

        validation_steps = int(self.validation[1].shape[0]/self.batch_size)
        for step in range(validation_steps):
          encoder_input_data, decoder_input_data,decoder_output_data ,start = self.fill_feed_dict(self.validation)

          val_predictions = self.model([encoder_input_data,decoder_input_data],training=False)

          self.val_metric.update_state(decoder_output_data, val_predictions) 

        val_loss = self.cce(decoder_output_data,val_predictions)

        if(self.beam_size == 1):
            y_pred = self.greedy_search(val_predictions)
            val_accuracy = self.get_accuracy(y_pred.numpy(),start,"val")
        else:
            y_pred = self.beam_search_function(val_predictions)
            val_accuracy = self.get_accuracy(y_pred,start,"val")
        #

        print("cross_entropy_accuracy",self.train_metric.result().numpy())

        print("cross_entropy_val_accuracy",self.val_metric.result().numpy())


        print("epoch:  ",epoch, "   accuracy :  ", accuracy, "    loss: ",self.epoch_loss_avg.result().numpy(),"   val_accuracy :  ", val_accuracy, "  val_loss: ",val_loss.numpy())



      
        model_callback = tf.keras.callbacks.ModelCheckpoint(
            filepath = " ",
            monitor='val_accuracy',
            mode='max',
            save_best_only=True,
            verbose=1)
      
      self.model.save('attention_model2')
      




 
rnn=RNN()
rnn.run_training()

"""Below cell initialises the test data"""

test_text =[]

test_target_text =[]
test_inp = set()

test_tar = set()

with open(configuration.get("test_path"),'r') as f:
  lines = f.read().split("\n")
  
  for line in lines:
    try:
       target_text,input_text, _ = line.split("\t")
    except:
      continue
    #input_text, target_text, _ = line.split("\t")
    target_text = "\t" + target_text + "\n"

    test_text.append(input_text)
    test_target_text.append(target_text)

    for char in input_text:
        if char not in test_inp:
            test_inp.add(char)
    for char in target_text:
        if char not in test_tar:
            test_tar.add(char)
decoder_target_data, encoder_input_data, decoder_input_data=rnn.encoding(test_text, test_target_text)

import numpy as np

def decode_sequence(input_seq):

  output ,states_value = rnn.encoder_model.predict(input_seq)
  #print("states_value: ", states_value[0].shape, states_value[1].shape)
  #states_value = states_value[1]
  # print("states_value: ", states_value.shape)
  target_seq = np.zeros((input_seq.shape[0], 1))

  target_seq[:, 0] = rnn.target_token_index["\t"]


  stop_condition = False
  decoded_sentence = ""
  count = 0
  attention_weights = []
  while not stop_condition:
      #print(states_value.shape)
      output_tokens, attn_s,state = rnn.decoder_model.predict([output,states_value,target_seq])
      # print("output_tokens: ",output_tokens.shape , "state: ",state.shape)
      #print("xyz")

      sampled_token_index = np.argmax(output_tokens[0, -1, :])
      # print("sampled_token_index: ",sampled_token_index)

      sampled_char = rnn.reverse_target_index[sampled_token_index]
      #print(sampled_char)
      #sampled_char = reverse_token_index[sampled_token_index]
      decoded_sentence += sampled_char
       
      if sampled_char == "\n" or len(decoded_sentence) > rnn.max_decoder_seq_length:
          # print("sampled_char: ", str(sampled_char), " len(decoded_sentence): ", len(decoded_sentence), " rnn.max_decoder_seq_length: ",rnn.max_decoder_seq_length)
          stop_condition = True
          # print("count: ", count)

      # print(decoded_sentence)
      count = count + 1
      target_seq = np.zeros((input_seq.shape[0], 1))
      target_seq[:, 0] = sampled_token_index
      attention_weights.append( attn_s)

      states_value = state
  return decoded_sentence, attention_weights
#print("decoded_sentence: ", decoded_sentence)

"""Below cell contains the inference code

*   Runs code for Question 5 (b)




"""

import csv

truth_value=[]
predicted_value =[]

with open('attn_test_value.csv', mode='w') as file:
  fieldnames = ['text', 'truth value', 'predicted value']
  writer = csv.DictWriter(file, fieldnames=fieldnames)
  writer.writeheader()
  decoder_target_data, encoder_input_data, decoder_input_data=rnn.encoding(test_text, test_target_text)
  #print(encoder_input_data))
  count =0
  with tf.device('/device:GPU:0'):
    for seq_index in range(len(test_text)):
        
        input_seq = encoder_input_data[seq_index : seq_index +1]
        input_seq=np.tile(input_seq ,(256,1))
        
        
        decoded_sentence,attn = decode_sequence(input_seq)
        if(test_target_text[seq_index][1:-1] == decoded_sentence[:-1]):
            count +=1
        truth_value.append(test_target_text[seq_index][1:-1])
        predicted_value.append(decoded_sentence[:-1])
        print(test_text[seq_index],test_target_text[seq_index][1:-1] ,decoded_sentence[:-1])

        writer.writerow({'text': test_text[seq_index], 'truth value': test_target_text[seq_index][1:-1], 'predicted value': decoded_sentence[:-1]})



print(count/len(test_text))

"""Next 2 cells upload the inference data to wandb to construct a table"""

import pandas as pd
df = pd.DataFrame(list(zip(test_text, truth_value,predicted_value)),columns =['input text', 'truth value','predicted text'])

#entity="assignment3",project='assignment3-part1'
import wandb
wandb.init(entity="assignment3",project ='ASSign 3 _heatmap_ plot',config=configuration)  
wandb.run.name = "attention_model" #wandb.run.name = 'hl-'+str(wandb.config.hidden_layer_size)+'-ne-'+str(wandb.config.num_encoder)+'-nd-'+str(wandb.config.num_decoder)+'-es-'+str(wandb.config.embedding_size)+'-ct-'+str(wandb.config.celltype)+'-d-'+str(wandb.config.dropout)+'-bs-'+str(wandb.config.batch_size)+'-e-'+str(50)
table = wandb.Table(dataframe=df)
wandb.log({"sample Inputs": table})