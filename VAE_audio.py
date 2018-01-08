import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt
# import data
from tensorflow.examples.tutorials.mnist import input_data

mnist = input_data.read_data_sets("MNIST_data", one_hot=True)

SAVE_EVERY = 5
version = "audio"
n_pixels = 28 * 28
# input the image
X = tf.placeholder(tf.float32, shape=([None, n_pixels]))

def weight_variables(shape, name):
    initial = tf.truncated_normal(shape, stddev=0.1)
    return tf.Variable(initial, name=name)

def bias_variable(shape, name):
    initial = tf.truncated_normal(shape, stddev=0.1)
    return tf.Variable(initial, name=name)

def FC_Layer(X, W, b):
    return tf.matmul(X, W) + b

############################ Encoder ############################
latent_dim = 20
h_dim = 500  # size of network

# layer 1
W_enc = weight_variables([n_pixels, h_dim], "W_enc")
b_enc = bias_variable([h_dim], "b_enc")
# tanh - activation function        avoid vanishing gradient in generative models
h_enc = tf.nn.tanh(FC_Layer(X, W_enc, b_enc))

# layer 2   Output mean and std of the latent variable distribution
W_mu = weight_variables([h_dim, latent_dim], "W_mu")
b_mu = bias_variable([latent_dim], "b_mu")
mu = FC_Layer(h_enc, W_mu, b_mu)

W_logstd = weight_variables([h_dim, latent_dim], "W_logstd")
b_logstd = bias_variable([latent_dim], "b_logstd")
logstd = FC_Layer(h_enc, W_logstd, b_logstd)


# Reparameterize import Randomness
noise = tf.random_normal([1, latent_dim])
# z is the ultimate output(latent variable) of our Encoder
z = mu + tf.multiply(noise, tf.exp(0.5*logstd))

############################ Dencoder ############################
# layer 1
W_dec = weight_variables([latent_dim, h_dim], "W_dec")
b_dec = bias_variable([h_dim], "b_dec")
# tanh - decode the latent representation
h_dec = tf.nn.tanh(FC_Layer(z, W_dec, b_dec))

# layer2 - reconstruction the image and output 0 or 1
W_rec = weight_variables([h_dim, n_pixels], "W_dec")
b_rec = bias_variable([n_pixels], "b_rec")
# 784 bernoulli parameter Output
reconstruction = tf.nn.sigmoid(FC_Layer(h_dec, W_rec, b_rec))

# Loss function = reconstruction error + regularization(similar image's latent representation close)
log_likelihood = tf.reduce_sum(X * tf.log(reconstruction + 1e-9) + (1 - X) * tf.log(1 - reconstruction + 1e-9))

KL_divergence = -0.5 * tf.reduce_sum(1 + 2*logstd - tf.pow(mu, 2) - tf.exp(2 * logstd), reduction_indices=1)

VAE_loss = tf.reduce_mean(log_likelihood + KL_divergence)
optimizer = tf.train.AdadeltaOptimizer().minimize(-VAE_loss)

# Training
#init all variables and start the session!
init = tf.global_variables_initializer()
sess = tf.InteractiveSession()
sess.run(init)
## Add ops to save and restore all the variables.
saver = tf.train.Saver()


import time #lets clock training time..
num_iterations = 100   # 1000000
recording_interval = 10    # 1000
#store value for these 3 terms so we can plot them later
variational_lower_bound_array = []
log_likelihood_array = []
KL_term_array = []
iteration_array = [i*recording_interval for i in range(num_iterations/recording_interval)]
for i in range(num_iterations):
    # np.round to make MNIST binary
    #get first batch (200 digits)
    x_batch = np.round(mnist.train.next_batch(200)[0])
    #run our optimizer on our data
    sess.run(optimizer, feed_dict={X: x_batch})
    if (i%recording_interval == 0):
        #every 1K iterations record these values
        vlb_eval = VAE_loss.eval(feed_dict={X: x_batch})
        print "Iteration: {}, Loss: {}".format(i, vlb_eval)
        variational_lower_bound_array.append(vlb_eval)
        log_likelihood_array.append(np.mean(log_likelihood.eval(feed_dict={X: x_batch})))
        KL_term_array.append(np.mean(KL_divergence.eval(feed_dict={X: x_batch})))

    if i%SAVE_EVERY == 0:
            if not os.path.exists('./model/' + version):
                os.makedirs('./model/' + version)
            saver.save(sess, './model/' +version + '/' + str(i))  

plt.figure()
#for the number of iterations we had 
#plot these 3 terms
plt.plot(iteration_array, variational_lower_bound_array)
plt.plot(iteration_array, KL_term_array)
plt.plot(iteration_array, log_likelihood_array)
plt.legend(['Variational Lower Bound', 'KL divergence', 'Log Likelihood'], bbox_to_anchor=(1.05, 1), loc=2)
plt.title('Loss per iteration')


# Here, we plot the reconstructed image on test set images.
import os
load_model = False
if load_model:
    saver.restore(sess, os.path.join(os.getcwd(), "Trained Bernoulli VAE"))

num_pairs = 16
image_indices = np.random.randint(0, 200, num_pairs)
#Lets plot 10 digits
for pair in range(num_pairs):
    #reshaping to show original test image
    x = np.reshape(mnist.test.images[image_indices[pair]], (1,n_pixels))
    plt.figure()
    x_image = np.reshape(x, (28,28))
    plt.subplot(121)
    plt.imshow(x_image)
    plt.title("Test image")
    #reconstructed image, feed the test image to the decoder
    x_reconstruction = reconstruction.eval(feed_dict={X: x})
    #reshape it to 28x28 pixels
    x_reconstruction_image = (np.reshape(x_reconstruction, (28,28)))
    #plot it!
    plt.subplot(122)
    plt.imshow(x_reconstruction_image)
    plt.title("Reconstructed image")

plt.show()

