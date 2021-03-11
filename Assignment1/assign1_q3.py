from keras.datasets import fashion_mnist
import numpy as np
import matplotlib.pyplot as plt
import math
import copy
from sklearn.model_selection import train_test_split 

config_ = {
    'learning_rate': 0.01,
    'epochs': 1,
    'no_hidden_layer': 3,
    'size_hidden_layer':128,
    'optimizer': 'rmsprop',
    'batch_size':100,
    'activation': 'sigmoid',
    'weight_initializations': 'xavier',
    'weight_decay': 0
  }

gamma = 0.9
beta = 0.9
epsilon = 0.00000001
beta1 = 0.9
beta2 = 0.99
no_classes = 10


(train_images, train_labels), (test_images, test_labels) = fashion_mnist.load_data()
train_images,val_images, train_labels, val_labels=train_test_split(train_images, train_labels,test_size=0.1,random_state=1)
train_images = np.array(train_images)
train_images = train_images / 255.0
val_images = np.array(val_images)
val_images = val_images / 255.0
test_images = np.array(test_images)
test_images = test_images / 255.0


train_input_neurons = list()
test_input_neurons = list()
val_input_neurons = list()

for i in range(len(train_images)):
  train_input_neurons.append(list(np.concatenate(train_images[i]).flat))

for i in range(len(val_images)):
  val_input_neurons.append(list(np.concatenate(val_images[i]).flat))

for i in range(len(test_images)):
  test_input_neurons.append(list(np.concatenate(test_images[i]).flat))

train_input_neurons = np.array(train_input_neurons).T
val_input_neurons = np.array(val_input_neurons).T
test_input_neurons = np.array(test_input_neurons).T




class NN(object):
  def __init__(self, num_inputs, hidden_layers, num_outputs,batch_size,learning_rate, epoch,activation,weight_init,weight_decay):
    self.num_inputs = num_inputs
    self.hidden_layers = hidden_layers
    self.num_outputs = num_outputs
    self.num_classes = num_outputs
    self.batch_size = batch_size
    self.learning_rate = learning_rate
    self.epoch = epoch
    self.iterations = 0
    self.activation = activation
    self.weight_init = weight_init
    self.weight_decay = weight_decay
    # nuerons in layers
    layers = [num_inputs] + hidden_layers + [num_outputs]

    # randomized weights and biases
    self.weights = []
    self.bias = []
    if self.weight_init == 'random': 
      for i in range(len(layers)-1):
        self.weights.insert(i, (np.random.rand(layers[i+1], layers[i]) - 0.5))
        self.bias.insert(i, (np.random.rand(layers[i+1],1) - 0.5))
    else:
      for i in range(len(layers)-1):
        sd = 6/(layers[i+1]+layers[i])
        self.weights.insert(i, (np.random.uniform(low = -sd ,high = sd, size =(layers[i+1], layers[i]))))
        self.bias.insert(i, (np.random.uniform(low = -sd ,high = sd, size = (layers[i+1],1))))
      
    
    
  def sigmoid(self, x):
    
    x = x.T
    y = np.zeros(x.shape)
    # print("\n____________________________{}".format(y.shape))
    for i in range(y.shape[0]):
      # print(np.exp(-x[i]))
      y[i] = 1.0 / (1 + np.exp(-x[i]))
    
    return y.T


  def tanh(self,x):
    x = x.T
    y = np.zeros(x.shape)
    for i in range(y.shape[0]):
      y[i] = (np.exp(x[i]) - np.exp(-x[i])) / (np.exp(x[i]) + np.exp(-x[i]))
    return y.T

  def Relu(self,x):
    x = x.T
    y = np.zeros(x.shape)
    for i in range(y.shape[0]):
      y[i] = np.maximum(x[i],0)
    return y.T

  def d_sigmoid(self, x):  
    y = self.sigmoid(x)
    y = y * (1 - y)
    return y

  def d_tanh(self,x):
    x = x.T
    y = np.zeros(x.shape)
    for i in range(y.shape[0]):
      y[i] = 1-np.power((np.exp(x[i]) - np.exp(-x[i])) / (np.exp(x[i]) + np.exp(-x[i])),2)
    return y.T

  def d_Relu(self,x):
    x = x.T
    y = np.zeros(x.shape)
    for i in range(y.shape[0]):
      y[i] = np.where(x[i] <= 0, 0, 1)
    return y.T

  def softmax(self, x):
    
    x = x.T
    y = np.zeros(x.shape)
    for i in range(x.shape[0]):
      y[i] = np.exp(x[i])/sum(np.exp(x[i]))
    
    return y.T

  def softmax_num_sable(self, x):
    
    x = x.T
    y = np.zeros(x.shape)
    for i in range(x.shape[0]):
      exps = x[i] - np.max(x[i])
      exps = np.exp(exps)
      y[i] = exps/sum(exps)
    return y.T

  def forward_prop(self, X):
    hiden_operation = 1;
    self.ai = {}
    self.hi = {}
    self.hi[hiden_operation - 1] = X
    self.ai[hiden_operation - 1] = X

    for w,b in zip(self.weights, self.bias):
      if(hiden_operation < len(self.weights)):
        self.ai[hiden_operation] = w.dot(self.hi[hiden_operation-1]) + b
        if(self.activation =='sigmoid'):
          self.hi[hiden_operation] = self.sigmoid(self.ai[hiden_operation])
        elif(self.activation =='tanh'):
          self.hi[hiden_operation] = self.tanh(self.ai[hiden_operation])
        elif(self.activation =='Relu'):
          self.hi[hiden_operation] = self.Relu(self.ai[hiden_operation])
        hiden_operation += 1
        
      else:
        self.ai[hiden_operation] = w.dot(self.hi[hiden_operation-1]) + b
        self.hi[hiden_operation] = self.softmax_num_sable(self.ai[hiden_operation])
    
    return self.hi, self.ai, self.hi[hiden_operation]

  def one_hot(self, y):
    one_hot_Y = np.zeros((len(y), self.num_classes ))
    one_hot_Y[np.arange(len(y)), y] = 1
    one_hot_Y = one_hot_Y
    return one_hot_Y

  def backward_prop(self, h, a, y_hat, y, loss_function):
    eY = self.one_hot(y)
    #print(y_hat)
    if loss_function == 'ce':
      d_al_theta = y_hat - eY.T
    elif loss_function == 'sq':
      d_al_theta = (y_hat - eY.T) * y_hat * (1 - y_hat)  

    self.d_weights = {}
    self.d_bias ={}
    self.d_h = {}
    self.d_a = {}
    no_of_samples = len(h[0])

    L = len(self.hidden_layers)
    self.d_a[L+1] = d_al_theta
    
    # hidden layers gradient
    for k in range(L, -1, -1):#2,1,0
     
      self.d_weights[k] = ((1/no_of_samples) * self.d_a[k+1].dot(h[k].T)) + (self.weight_decay *  self.weights[k])
      self.d_bias[k] = ((1/no_of_samples) * np.sum(self.d_a[k+1], axis = 1, keepdims = True)) + (self.weight_decay *self.bias[k] )
      self.d_h[k] = self.weights[k].T.dot(self.d_a[k+1])
      if(self.activation =='sigmoid'):
        self.d_a[k] = self.d_h[k] * self.d_sigmoid(a[k])
      elif(self.activation =='tanh'):
        self.d_a[k] = self.d_h[k] * self.d_tanh(a[k])
      elif(self.activation =='Relu'):
        self.d_a[k] = self.d_h[k] * self.d_Relu(a[k])
    return self.d_weights, self.d_bias
      
  def get_prediction(self, y):
    # print(np.argmax(y, 1))
    return np.argmax(y, 0)
  
  def get_accuracy(self, prediction, y):
    return np.sum(prediction == y) / y.size

  def make_predictions(self, x):
    _, _, y_hatt = self.forward_prop(x)
    predictions = self.get_prediction(y_hatt)
    return predictions
    # return y_hatt, predictions

  def cross_entropy(self, y,yhat):
    return (-sum([math.log(yhat[y[i],i]) for i in range(len(y))])/len(y)) + (self.weight_decay*0.5 * (np.sum([np.linalg.norm(self.weights[i]) for i in range(len(self.weights))])))

  def test_prediction(self, current_image, y):
    # current_image = X_train[:, index, None]
    prediction = self.make_predictions(current_image)
    label = y
    print("Prediction: ", prediction)
    print("Label: ", label)    
    current_image = current_image.reshape((28, 28)) * 255
    plt.gray()
    plt.imshow(current_image, interpolation='nearest')
    plt.show()

  def logging(self,j):
    output_h, output_a, y_hat = self.forward_prop(train_input_neurons)
    predictions = self.get_prediction(y_hat)
    accuracy = self.get_accuracy(predictions, train_labels)
    loss_train = self.cross_entropy(train_labels,y_hat)
    output_h, output_a, y_hat = self.forward_prop(val_input_neurons)
    val_predictions = self.get_prediction(y_hat)
    val_accuracy = self.get_accuracy(val_predictions, val_labels)
    loss_valid = self.cross_entropy(val_labels,y_hat)
    print("epoch______{} :   {}".format(j, accuracy))



  def gradient_descent(self, input_neurons, learning_rate, epoch):
  
    for j in range(epoch):
      output_h, output_a, y_hat = self.forward_prop(input_neurons)
      #print(len(output_h), len(output_a), len(y_hat))
      d_weights, d_bias = self.backward_prop(output_h, output_a, y_hat, train_labels, 'ce')
      for i in range(len(d_weights)):
        self.weights[i] = self.weights[i] - learning_rate * d_weights[i]
        self.bias[i] = self.bias[i] - learning_rate * d_bias[i]
    
      self.logging(j)

    return self.weights, self.bias

  def sgd(self, input_neurons, learning_rate, epoch):
    for j in range(epoch):

      for i in range(input_neurons.shape[1]):
        output_h, output_a, y_hat = self.forward_prop(input_neurons[:,i].reshape((input_neurons.shape[0],1)))
        d_weights, d_bias = self.backward_prop(output_h, output_a, y_hat, np.array([train_labels[i]]), 'ce')
        

        for d in range(len(d_weights)):
          self.weights[d] = self.weights[d] - learning_rate * d_weights[d]
          self.bias[d] = self.bias[d] - learning_rate * d_bias[d]

      self.logging(j)

    return self.weights, self.bias

  def momentum_gd(self, input_neurons, gamma):
     self.w_update ={} 
     self.b_update ={} 
     for j in range(self.epoch):
        self.iterations = math.ceil(input_neurons.shape[1]/self.batch_size)
        for i in range(self.iterations):
          output_h, output_a, y_hat = self.forward_prop(input_neurons[:,(i*self.batch_size): min((((i+1)*self.batch_size)-1),input_neurons.shape[1]-1)])
          if(self.batch_size==1):
            d_weights, d_bias = self.backward_prop(output_h, output_a, y_hat, np.array([train_labels[i]]), 'ce')
          else:
            d_weights, d_bias = self.backward_prop(output_h, output_a, y_hat, train_labels[(i*self.batch_size): min((((i+1)*self.batch_size)-1),input_neurons.shape[1]-1)], 'ce')

          if(j==0 and i==0):
            for d in range(len(d_weights)):
                self.weights[d] = self.weights[d] - self.learning_rate * d_weights[d]
                self.w_update[d] = self.learning_rate * d_weights[d]
                self.bias[d] = self.bias[d] - self.learning_rate * d_bias[d]
                self.b_update[d] = self.learning_rate * d_bias[d]
          else:
            for d in range(len(d_weights)):
              self.weights[d] = self.weights[d] - ((gamma *self.w_update[d] )+(self.learning_rate * d_weights[d]))
              self.w_update[d] = (gamma *self.w_update[d] )+(self.learning_rate * d_weights[d])
              self.bias[d] = self.bias[d] - ((gamma *self.b_update[d])+(self.learning_rate * d_bias[d]))
              self.b_update[d] = (gamma *self.b_update[d])+(self.learning_rate * d_bias[d])  

        self.logging(j)
        
     return self.weights, self.bias

  def nesterov_accelerated_gd(self, input_neurons, gamma):
     self.w_update ={} 
     self.b_update ={}
     for j in range(self.epoch):
        self.iterations = math.ceil(input_neurons.shape[1]/self.batch_size)
        for i in range(self.iterations):
          output_h, output_a, y_hat = self.forward_prop(input_neurons[:,(i*self.batch_size): min((((i+1)*self.batch_size)-1),input_neurons.shape[1]-1)])
          if(self.batch_size==1):
            d_weights, d_bias = self.backward_prop(output_h, output_a, y_hat, np.array([train_labels[i]]), 'ce')
          else:
            d_weights, d_bias = self.backward_prop(output_h, output_a, y_hat, train_labels[(i*self.batch_size): min((((i+1)*self.batch_size)-1),input_neurons.shape[1]-1)], 'ce')

          if(j!=0 or i!=0):
            for d in range(len(d_weights)):
              self.weights[d] = self.weights[d] - ((gamma *self.w_update[d] ))
              self.bias[d] = self.bias[d] - ((gamma *self.b_update[d]))

          output_h, output_a, y_hat = self.forward_prop(input_neurons[:,(i*self.batch_size): min((((i+1)*self.batch_size)-1),input_neurons.shape[1]-1)])
          if(self.batch_size==1):
            d_weights, d_bias = self.backward_prop(output_h, output_a, y_hat, np.array([train_labels[i]]), 'ce')
          else:
            d_weights, d_bias = self.backward_prop(output_h, output_a, y_hat, train_labels[(i*self.batch_size): min((((i+1)*self.batch_size)-1),input_neurons.shape[1]-1)], 'ce')

          if(j==0 and i==0):
            for d in range(len(d_weights)):
                self.weights[d] = self.weights[d] - self.learning_rate * d_weights[d]
                self.w_update[d] = self.learning_rate * d_weights[d]
                self.bias[d] = self.bias[d] - self.learning_rate * d_bias[d]
                self.b_update[d] = self.learning_rate * d_bias[d]
          else:
            for d in range(len(d_weights)):
              self.weights[d] = self.weights[d] - ((self.learning_rate * d_weights[d]))
              self.w_update[d] = (gamma *self.w_update[d] )+(self.learning_rate * d_weights[d])
              self.bias[d] = self.bias[d] - ((self.learning_rate * d_bias[d]))
              self.b_update[d] = (gamma *self.b_update[d])+(self.learning_rate * d_bias[d])  


        self.logging(j)
     return self.weights, self.bias

  def rmsprop(self, input_neurons, beta,epsilon):
    w_vt ={} 
    b_vt ={}
    for j in range(self.epoch):
        self.iterations = math.ceil(input_neurons.shape[1]/self.batch_size)
        for i in range(self.iterations):
          output_h, output_a, y_hat = self.forward_prop(input_neurons[:,(i*self.batch_size): min((((i+1)*self.batch_size)-1),input_neurons.shape[1]-1)])
          if(self.batch_size==1):
            d_weights, d_bias = self.backward_prop(output_h, output_a, y_hat, np.array([train_labels[i]]), 'ce')
          else:
            d_weights, d_bias = self.backward_prop(output_h, output_a, y_hat, train_labels[(i*self.batch_size): min((((i+1)*self.batch_size)-1),input_neurons.shape[1]-1)], 'ce')

          if(j!=0 or i!=0):
            for d in range(len(d_weights)):
              w_vt[d]= beta * w_vt[d] + (1-beta) * np.power(d_weights[d],2)
              b_vt[d] = beta * b_vt[d] + (1-beta) * np.power(d_bias[d],2)
              w = 1/np.power(w_vt[d]+epsilon,0.5)
              b = 1/np.power(b_vt[d]+epsilon,0.5)
              self.weights[d] = self.weights[d] - self.learning_rate *w* d_weights[d]
              self.bias[d] = self.bias[d] - self.learning_rate *b* d_bias[d]
          else:
            for d in range(len(d_weights)):
              w_vt[d]=  (1-beta) *  np.power(d_weights[d],2)
              b_vt[d] = (1-beta) * np.power(d_bias[d],2)
              w = 1/np.power(w_vt[d]+epsilon,0.5)
              b = 1/np.power(b_vt[d]+epsilon,0.5)
              self.weights[d] = self.weights[d] - self.learning_rate *w* d_weights[d]
              self.bias[d] = self.bias[d] - self.learning_rate *b* d_bias[d]
        self.logging(j)
    return self.weights, self.bias

  def adam(self, input_neurons,beta1,beta2,epsilon):
    w_mt ={} 
    b_mt ={}
    w_vt ={} 
    b_vt ={}
    for j in range(self.epoch):
        self.iterations = math.ceil(input_neurons.shape[1]/self.batch_size)
        for i in range(self.iterations):
          output_h, output_a, y_hat = self.forward_prop(input_neurons[:,(i*self.batch_size): min((((i+1)*self.batch_size)-1),input_neurons.shape[1]-1)])
          if(self.batch_size==1):
            d_weights, d_bias = self.backward_prop(output_h, output_a, y_hat, np.array([train_labels[i]]), 'ce')
          else:
            d_weights, d_bias = self.backward_prop(output_h, output_a, y_hat, train_labels[(i*self.batch_size): min((((i+1)*self.batch_size)-1),input_neurons.shape[1]-1)], 'ce')
          
          if(j!=0 or i!=0):
            for d in range(len(d_weights)):
              w_mt[d]= beta1 * w_mt[d] + (1-beta1) * d_weights[d]
              b_mt[d] = beta1 * b_mt[d] + (1-beta1) * d_bias[d]
              w_vt[d]= beta2 * w_vt[d] + (1-beta2) * np.power(d_weights[d],2)
              b_vt[d] = beta2 * b_vt[d] + (1-beta2) * np.power(d_bias[d],2)
              mt_hat = w_mt[d]/(1-np.power(beta1,(j*self.iterations)+i+1))
              vt_hat = w_vt[d]/(1-np.power(beta2,(j*self.iterations)+i+1))
              bmt_hat = b_mt[d]/(1-np.power(beta1,(j*self.iterations)+i+1))
              bvt_hat = b_vt[d]/(1-np.power(beta2,(j*self.iterations)+i+1))
              #print(mt_hat, vt_hat, bmt_hat, bvt_hat)
              self.weights[d] = self.weights[d] - (self.learning_rate *(1/np.sqrt(vt_hat+epsilon))* mt_hat)
              self.bias[d] = self.bias[d] - (self.learning_rate *(1/np.sqrt(bvt_hat+epsilon))* bmt_hat)
          else:
            for d in range(len(d_weights)):
              w_mt[d]=  (1-beta1) * d_weights[d]
              b_mt[d] = (1-beta1) * d_bias[d]
              w_vt[d]=  (1-beta2) * np.power(d_weights[d],2)
              b_vt[d] = (1-beta2) * np.power(d_bias[d],2)
              mt_hat = w_mt[d]/(1-np.power(beta1,(j*self.iterations)+i+1))
              vt_hat = w_vt[d]/(1-np.power(beta2,(j*self.iterations)+i+1))
              bmt_hat = b_mt[d]/(1-np.power(beta1,(j*self.iterations)+i+1))
              bvt_hat = b_vt[d]/(1-np.power(beta2,(j*self.iterations)+i+1))
              self.weights[d] = self.weights[d] - (self.learning_rate *(1/np.sqrt(vt_hat+epsilon))* mt_hat)
              self.bias[d] = self.bias[d] - (self.learning_rate *(1/np.sqrt(bvt_hat+epsilon))* bmt_hat)
        #print("epoch______{} :   {}".format(j, accuracy))
        self.logging(j)
                  

    return self.weights, self.bias

  def nadam(self, input_neurons,beta1,beta2,epsilon):
    w_mt ={} 
    b_mt ={}
    w_vt ={} 
    b_vt ={}
    for j in range(self.epoch):
        self.iterations = math.ceil(input_neurons.shape[1]/self.batch_size)
        for i in range(self.iterations):
          output_h, output_a, y_hat = self.forward_prop(input_neurons[:,(i*self.batch_size): min((((i+1)*self.batch_size)-1),input_neurons.shape[1]-1)])
          if(self.batch_size==1):
            d_weights, d_bias = self.backward_prop(output_h, output_a, y_hat, np.array([train_labels[i]]), 'ce')
          else:
            d_weights, d_bias = self.backward_prop(output_h, output_a, y_hat, train_labels[(i*self.batch_size): min((((i+1)*self.batch_size)-1),input_neurons.shape[1]-1)], 'ce')
          if(j!=0 or i!=0):
            for d in range(len(d_weights)):
              w_mt[d]= beta1 * w_mt[d] 
              b_mt[d] =beta1 * b_mt[d] 
              w_vt[d]= beta2 * w_vt[d] 
              b_vt[d] = beta2 * b_vt[d] 
              mt_hat = w_mt[d]/(1-np.power(beta1,(j*self.iterations)+i+1))
              vt_hat = w_vt[d]/(1-np.power(beta2,(j*self.iterations)+i+1))
              bmt_hat = b_mt[d]/(1-np.power(beta1,(j*self.iterations)+i+1))
              bvt_hat = b_vt[d]/(1-np.power(beta2,(j*self.iterations)+i+1))

              self.weights[d] = self.weights[d] - self.learning_rate *(1/np.sqrt(vt_hat+epsilon))* mt_hat
              self.bias[d] = self.bias[d] - self.learning_rate *(1/np.sqrt(bvt_hat+epsilon))* bmt_hat

              output_h, output_a, y_hat = self.forward_prop(input_neurons[:,(i*self.batch_size): min((((i+1)*self.batch_size)-1),input_neurons.shape[1]-1)])
              if(self.batch_size==1):
                d_weights, d_bias = self.backward_prop(output_h, output_a, y_hat, np.array([train_labels[i]]), 'ce')
              else:
                d_weights, d_bias = self.backward_prop(output_h, output_a, y_hat, train_labels[(i*self.batch_size): min((((i+1)*self.batch_size)-1),input_neurons.shape[1]-1)], 'ce')


              w_mt[d] += (1-beta1) * d_weights[d]
              b_mt[d] += (1-beta1) * d_bias[d]
              w_vt[d] += (1-beta2) * np.power(d_weights[d],2)
              b_vt[d] += (1-beta2) * np.power(d_bias[d],2)

              mt_hat = w_mt[d]/(1-np.power(beta1,(j*self.iterations)+i+1))
              vt_hat = w_vt[d]/(1-np.power(beta2,(j*self.iterations)+i+1))
              bmt_hat = b_mt[d]/(1-np.power(beta1,(j*self.iterations)+i+1))
              bvt_hat = b_vt[d]/(1-np.power(beta2,(j*self.iterations)+i+1))

              self.weights[d] = self.weights[d] - self.learning_rate *(1/np.sqrt(vt_hat+epsilon))* mt_hat
              self.bias[d] = self.bias[d] - self.learning_rate *(1/np.sqrt(bvt_hat+epsilon))* bmt_hat
            
          else:
            for d in range(len(d_weights)):
              w_mt[d] = (1-beta1) * d_weights[d]
              b_mt[d] = (1-beta1) * d_bias[d]
              w_vt[d] = (1-beta2) * np.power(d_weights[d],2)
              b_vt[d] = (1-beta2) * np.power(d_bias[d],2)

              mt_hat = w_mt[d]/(1-np.power(beta1,(j*self.iterations)+i+1))
              vt_hat = w_vt[d]/(1-np.power(beta2,(j*self.iterations)+i+1))
              bmt_hat = b_mt[d]/(1-np.power(beta1,(j*self.iterations)+i+1))
              bvt_hat = b_vt[d]/(1-np.power(beta2,(j*self.iterations)+i+1))

              self.weights[d] = self.weights[d] - self.learning_rate *(1/np.sqrt(vt_hat+epsilon))* mt_hat
              self.bias[d] = self.bias[d] - self.learning_rate *(1/np.sqrt(bvt_hat+epsilon))* bmt_hat
        
        self.logging(j) 

    return self.weights, self.bias


def train():
  
  

  batch_size = config_.get('batch_size')
  learning_rate = config_.get('learning_rate')
  epoch = config_.get('epochs') 
  optimizer = config_.get('optimizer')
  no_hidden_layer = config_.get('no_hidden_layer')#
  size_hidden_layer = config_.get('size_hidden_layer')#
  activation = config_.get('activation')#
  weight_init = config_.get('weight_init')#
  weight_decay = config_.get('weight_decay')




  
  ffnn = NN(len(train_input_neurons), [size_hidden_layer]*no_hidden_layer, no_classes,batch_size,learning_rate,epoch,activation,weight_init,weight_decay)
  
  if optimizer == 'sgd':
    weight, bias=ffnn.sgd(train_input_neurons, learning_rate, epoch)
  elif optimizer == 'momentum':
    weight, bias = ffnn.momentum_gd(train_input_neurons,gamma)
  elif optimizer == 'nesterov':
    weight, bias = ffnn.nesterov_accelerated_gd(train_input_neurons,gamma)
  elif optimizer == 'rmsprop':
    weight, bias = ffnn.rmsprop(train_input_neurons,beta,epsilon)
  elif optimizer == 'adam':
    weight, bias = ffnn.adam(train_input_neurons,beta1,beta2,epsilon)
  elif optimizer =='gd':
    weight, bias = ffnn.gradient_descent(train_input_neurons, learning_rate, epoch)
  elif optimizer =='nadam':
    weight, bias = ffnn.nadam(train_input_neurons,beta1,beta2,epsilon)
  else:
    print('Invalid optimizer. Choose from sgd, momentum, nesterov, rmsprop, adam,gd')


  print("validate training_____________________________________________________________________________________________________________")
  ffnn.test_prediction(train_input_neurons[:, 0:1], train_labels[0])
  ffnn.test_prediction(train_input_neurons[:, 1:2], train_labels[1])

  print("test training--------------------------------------------------------------------")
  ffnn.test_prediction(test_input_neurons[:, 0:1], test_labels[0])

  test_prediction = ffnn.make_predictions(test_input_neurons)
  test_accuracy = ffnn.get_accuracy(test_prediction, test_labels)
  print("test accuracy: {}".format(test_accuracy))
    
if __name__ == "__main__":
  train()

#classes = {0 : "T-shirt/top", 1: "Trouser", 2: "Pullover", 3: "Dress", 4: "Coat",5: "Sandal", 6: "Shirt", 7: "Sneaker", 8: "Bag", 9: "Ankle Boot"}