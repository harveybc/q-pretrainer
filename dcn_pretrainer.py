# svm_pretrainer: Trains a svm for each action, exports predicted results as csv,
#                 prints nmse and exports svm pre-trained models to be used in a 
#                 q-agent.

import sys
from sklearn import svm
from sklearn.model_selection import GridSearchCV
from numpy import genfromtxt
from numpy import shape
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error
from joblib import dump, load
from sklearn import preprocessing
from sklearn.metrics import confusion_matrix

## \class QPretrainer
## \brief Trains a SVM with data generated with q-datagen and export predicted data and model data.
class QPretrainer():    
    ## init method
    ## Loads the training and validation datasets
    def __init__(self):
        # Training set
        self.ts = []
        # Validation set
        self.vs = []
        # Number of features in dataset
        self.num_f = 0   
        self.num_features = 0
        self.window_size = 30
        # Number of training signals in dataset
        self.num_s = 19
        # number of folds for cross validation during grid search svm parameter tunning
        self.nfolds=3
        # First argument is the training dataset, last 25% of it is used as validation set
        self.ts_f = sys.argv[1]
        # Third argument is the prefix (including path) for the dcn pre-trained models 
        # for the actions, all modes are files with .model extention and the prefix is
        # concatenated with a number indicating the action:
        # 0 = TP
        # 1 = SL
        # 2 = dInv
        # 3 = direction (1: buy, -1: sell)
        self.num_ticks = 0
        self.model_prefix = sys.argv[2]
        # svm model
        self.svr_rbf = []
        self.learning_rate = 0.001

    def set_dcn_model(self):
        # Deep Convolutional Neural Network for Regression
        model = Sequential()
        # for observation[19][48], 19 vectors of 128-dimensional vectors,input_shape = (19, 48)
        # first set of CONV => RELU => POOL
        model.add(Conv1D(512, 5,input_shape=(self.num_features,self.window_size)))
        model.add(Activation('relu'))
        model.add(MaxPooling1D(pool_size=2, strides=2))
        # second set of CONV => RELU => POOL
        model.add(Conv1D(32, 5))
        model.add(Activation('relu'))
        model.add(MaxPooling1D(pool_size=2, strides=2))
        # second set of CONV => RELU => POOL
        model.add(Flatten())  # this converts our 3D feature maps to 1D feature vectors
        model.add(Dense(64)) # valor óptimo:64 @400k
        model.add(Activation('relu'))
        # output layer
        model.add(Dense(1, activation = 'sigmoid'))
        model.add(Activation('softmax'))
        # multi-GPU support
        #model = to_multi_gpu(model)
        #self.reduce_lr = ReduceLROnPlateau(monitor='loss', factor=0.3, patience=5, min_lr=1e-4)
        # use SGD optimizer
        #opt = Adam(lr=self.learning_rate)
        opt = SGD(lr=self.learning_rate, momentum=0.9)
        model.compile(loss="binary_crossentropy", optimizer=opt, metrics=["accuracy"])
        #model.compile(loss="mse", optimizer=opt, metrics=["accuracy"])
        return model 

    ## Load  training and validation datasets, initialize number of features and training signals
    def load_datasets(self):
        self.ts_g = genfromtxt(self.ts_f, delimiter=',', skip_header = 1)
        # split training and validation sets into features and training signal for regression
        self.num_f = self.ts_g.shape[1] - self.num_s
        self.num_features = self.num_f // self.window_size
        self.num_ticks = self.ts_g.shape[0]
        # split dataset into 75% training and 25% validation 
        self.ts_s = self.ts_g[1:(3*self.num_ticks)//4,:]
        self.ts = self.ts_s.copy()
        self.vs_s = self.ts_g[(3*self.num_ticks)//4 : self.num_ticks,:]
        self.vs = self.vs_s.copy() 
    ## Train SVMs with the training dataset using cross-validation error estimation
    ## Returns best parameters
    def train_model(self, signal):
        #converts to nparray
        self.ts = np.array(self.ts)
        self.x = self.ts[1:,0:self.num_f]
        #if signal == 0:
        #    print("Training set self.x = ",self.x)
        # TEST, remve 1 and replace by self.num_f
        self.y = self.ts[1:,self.num_f + signal]                  
        #print("Training action (", signal, ") self.y = ", self.y)
        # svr_rbf = SVR(kernel='rbf', C=1e3, gamma=0.1)
        #Cs = [1e-4, 1e-3, 1e-2, 1e-1, 2e0, 2e1, 2e2, 2e4]
        #gammas = [2e-20, 2e-10, 2e0, 2e10]
        epsilons = [1e-2, 1e-1,2e-1,3e-1,5e-1]
        Cs = [2e-5,2e-4,2e-3,2e-2, 2e-1,2e1,2e2,2e3,2e4]
        #Cs = [1, 10,100,1000]
        #gammas = [1e-8, 1e-7, 1e-6, 1e-5, 1e-4, 1e-3, 1e-2, 1e-1, 0.2,0.5, 0.9]
        param_grid = {'C': Cs, 'epsilon':epsilons}
        grid_search = GridSearchCV(svm.SVR(gamma="auto"),param_grid, cv=self.nfolds)
        grid_search.fit(self.x, self.y)
        return grid_search.best_params_
    
    ## Evaluate the trained models in the validation set to obtain the error
    def evaluate_validation(self, params, signal):
        self.vs = np.array(self.vs)
        # TODO: NO ES TS SINO VS
        self.x_v = self.vs[1:,0:self.num_f]
        # TEST, remve 1 and replace by self.num_f
        self.y_v = self.vs[1:,self.num_f + signal]
        # create SVM model with RBF kernel with existing parameters
        self.svr_rbf = svm.SVR(gamma="auto", C=params["C"], epsilon=params["epsilon"])
        # Fit the SVM modelto the data and evaluate SVM model on validation x
        self.x = self.ts[1:,0:self.num_f]
        self.y = self.ts[1:,self.num_f + signal]
        if signal == 0:
            print("Validation set self.x_v = ",self.x_v)
        #TODO, NO ES PREDICT X SINO X_V
        y_rbf = self.svr_rbf.fit(self.x, self.y).predict(self.x_v)
        #scaler = preprocessing.StandardScaler()
        # TODO: PRUEBA DE SCALER DE OUTPUT DE SVM
        #y_rbf = scaler.fit_transform([y_rbf_o])
        if signal == 0:
            print("Validation set y_rbf = ",y_rbf)
        # plot original and predicted data of the validation dataset
        lw = 2
        # TODO: NO ES TS SINO VS
        x_seq = list(range(0, self.vs.shape[0]-1))
        # 0 = Buy/CloseSell/nopCloseBuy
        print("x_seq.len = ", len(x_seq) , "y.len = " ,len(self.y_v) )
        fig=plt.figure()
        plt.plot(x_seq, self.y_v, color='darkorange', label='data')
        plt.plot(x_seq, y_rbf, color='navy', lw=lw, label='RBF model')
        plt.xlabel('data')
        plt.ylabel('target')
        plt.title('Signal ' + str(signal))
        plt.legend()
        fig.savefig('predict_' + str(signal) + '.png')
        if signal==18:
            plt.show()
        else:
            plt.show(block=False)
        return confusion_matrix(self.y_v, y_rbf)
 
     
    ## Generate DCN  input matrix
    def dcn_input(self, data):
        #obs_matrix = np.array([np.array([0.0] * self.num_features)]*len(data), dtype=object)
        obs_matrix = []
        obs = np.array([np.array([0.0] * self.window_size)] * self.num_features)
        # for each observation
        data_p = np.array(data)
        for i, ob in enumerate(data):
            # for each feature, add an array of window_size elements
            for j in range(0,self.num_features):
                #print("obs=",obs)
                #print("data_p=",data_p[i, j * self.window_size : (j+1) * self.window_size])
                obs[j] = data_p[i, j * self.window_size : (j+1) * self.window_size]
                #obs[j] = ob[0]
            obs_matrix.append(obs.copy())
        return obs_matrix
 
 ## Train SVMs with the training dataset using cross-validation error estimation
    ## Returns best parameters
    def train_model_c(self, signal):
        #converts to nparray
        self.ts = np.array(self.ts)
        self.x_pre = self.ts[1:,0:self.num_f]
        self.x = self.dcn_input(self.x_pre)
        self.y = self.ts[1:,self.num_f + signal].astype(int)                  
        # TODO: Cambiar var svr_rbf por p_model
        # setup the DCN model
        self.svr_rbf = set_dcn_model()
        # train DCN model with the training data
        self.svr_rbf.fit(self.x, self.y, batch_size=100, nb_epoch=100, verbose=1)
        return self.svr_rbf 

        
    ## Evaluate the trained models in the validation set to obtain the error
    def evaluate_validation_c(self, model, signal):
        self.vs = np.array(self.vs)
        # TODO: NO ES TS SINO VS
        self.x_v_pre = self.vs[1:,0:self.num_f]
        self.x_v = self.dcn_input(self.x_v_pre)
        # TEST, remve 1 and replace by self.num_f
        self.y_v = self.vs[1:,self.num_f + signal].astype(int)
        if signal == 0:
            print("Validation set self.x_v = ",self.x_v)
        # predict the class of in the validation set
        y_rbf = svr_rbf.predict_classes(self.x_v)
        if signal == 0:
            print("Validation set y_rbf = ",y_rbf)
        # plot original and predicted data of the validation dataset
        lw = 2
        # TODO: NO ES TS SINO VS
        x_seq = list(range(0, self.vs.shape[0]-1))
        # 0 = Buy/CloseSell/nopCloseBuy
        print("x_seq.len = ", len(x_seq) , "y.len = " ,len(self.y_v) )
        fig=plt.figure()
        plt.plot(x_seq, self.y_v, color='darkorange', label='data')
        plt.plot(x_seq, y_rbf, color='navy', lw=lw, label='RBF model')
        plt.xlabel('data')
        plt.ylabel('target')
        plt.title('Signal ' + str(signal))
        plt.legend()
        fig.savefig('predict_' + str(signal) + '.png')
        if signal==18:
            plt.show()
        else:
            plt.show(block=False)
        return mean_squared_error(self.y_v, y_rbf)
 
    ## Export the trained models and the predicted validation set predictions, print statistics 
    def export_model(self, signal):
        dump(self.svr_rbf, self.model_prefix + str(signal)+'.svm') 
        
# main function 
if __name__ == '__main__':
    pt = QPretrainer()
    pt.load_datasets()
    #for i in range(0,pt.num_s):
    for i in range(16,19):
        print('Training model '+str(i))
        # verifies if the actions are for classification(the last 6 ones)
        if (i>=10):
            params = pt.train_model_c(i)
            print('best_params_' + str(i) + ' = ',params)
            error = pt.evaluate_validation_c(params,i)
            print('error on validation set:' + str(i) + ' = ' + str(error))
        else:    
            params = pt.train_model(i)
            print('best_params_' + str(i) + ' = ',params)
            mse = pt.evaluate_validation(params,i)
            print('mean_squared_error on validation set:' + str(i) + ' = ' + str(mse))
        pt.export_model(i)
    
    