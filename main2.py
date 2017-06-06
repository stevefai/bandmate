import numpy
from keras.models import Sequential
from keras.layers import Dense, Lambda
from keras.layers import Dropout
from keras.layers import LSTM
from keras.callbacks import ModelCheckpoint
from keras.utils import np_utils
from bassdataset import map_sequence_to_csv
import sys
from probabilityHelpers import get_best_index
from subprocess import call

# load ascii text and covert to lowercase
filename = "D:/bandmate-data/piano-dataset/all.txt"
raw_text = open(filename).read()
raw_text = raw_text.lower()

# create mapping of unique chars to integers
tokens = raw_text.split(" ")
pos = 0
for t in tokens:
    if t == '':
        tokens.pop(pos)
        break
    pos += 1

chars = sorted(list(set(tokens)))
char_to_int = dict((c, i) for i, c in enumerate(chars))
int_to_char = dict((i, c) for i, c in enumerate(chars))
print "charts:::"
print char_to_int
print int_to_char
# summarize the loaded data
n_chars = len(tokens)
n_vocab = len(chars)
print("Total Characters: ", n_chars)
print("Total Vocab: ", n_vocab)

# prepare the dataset of input to output pairs encoded as integers
seq_length = 96
dataX = []
dataY = []
for i in range(0, n_chars - seq_length, 1):
    seq_in = tokens[i:i + seq_length]
    seq_out = tokens[i + seq_length]
    dataX.append([char_to_int[char] for char in seq_in])
    dataY.append(char_to_int[seq_out])
n_patterns = len(dataX)
print("Total Patterns: ", n_patterns)

# reshape X to be [samples, time steps, features]
X = numpy.reshape(dataX, (n_patterns, seq_length, 1))
# normalize
X = X / float(n_vocab)
# one hot encode the output variable
y = np_utils.to_categorical(dataY)

# define the LSTM model
model = Sequential()
model.add(LSTM(128, input_shape=(X.shape[1], X.shape[2])))
model.add(Dropout(0.2))
model.add(Lambda(lambda inpx: inpx))
model.add(Dense(y.shape[1], activation='softmax'))

model.compile(loss='categorical_crossentropy', optimizer='adam')

# define the checkpoint
filepath="weights-improvement-piano-{epoch:02d}-{loss:.4f}.hdf5"
checkpoint = ModelCheckpoint(filepath, monitor='loss', verbose=1, save_best_only=True, mode='min')

callbacks_list = [checkpoint]

# fit the model
model.fit(X, y, epochs=40, batch_size=64, callbacks=callbacks_list)

# # load the network weights
# filename = "weights-improvement-00-0.9542.hdf5"
# model.load_weights(filename)
# model.compile(loss='categorical_crossentropy', optimizer='adam')
#
# # pick a random seed
# # pick a random seed
# start = numpy.random.randint(0, len(dataX)-1)
# pattern = dataX[start]
# print "start:", pattern
# # generate characters
# notes = []
# for i in range(500):
#     x = numpy.reshape(pattern, (1, len(pattern), 1))
#     x = x / float(n_vocab)
#     prediction = model.predict(x, verbose=0)
#     index = get_best_index(prediction[0], 3)
#     result = int_to_char[index]
#     notes.append(int(result))
#     seq_in = [int_to_char[value] for value in pattern]
#     sys.stdout.write(result + " ")
#     pattern.append(index)
#     pattern = pattern[1:len(pattern)]
# csv_notes = map_sequence_to_csv(notes, "D:\\bandmate-data\\results\\1.txt")
# with open("D:\\bandmate-data\\results\\1.txt", 'w+') as the_file:
#     for line in csv_notes:
#         the_file.write(line)
# call(["csvmidi", "D:\\bandmate-data\\results\\1.txt", "D:\\bandmate-data\\results\\1.mid"])
# print "\nDone."
