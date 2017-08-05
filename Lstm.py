import numpy
from keras.models import Sequential
from keras.layers import Dense, Lambda
from keras.layers import Dropout
from keras.layers import LSTM
from keras.callbacks import ModelCheckpoint, ReduceLROnPlateau
from keras.utils import np_utils
from DatasetBuilder import DatasetBuilder
import sys
from probabilityHelpers import get_best_index
from subprocess import call


class Lstm:
    def __init__(self, filename):
        self.filename = filename
        self.raw_text = ""
        self.songs = []
        self.dataX = []
        self.dataY = []
        self.n_patterns = 0
        self.n_chars = 0
        self.seq_length = 100
        self.n_vocab = 0
        self.int_to_char = dict()
        self.char_to_int = dict()
        self.model = Sequential()
        self.load_data()


    def load_data(self):
        # load text and covert to lowercase
        self.raw_text = open(self.filename).read()
        self.raw_text = self.raw_text.lower()

        # create mapping of unique chars to integers
        tokens = self.raw_text.split(" ")

        # delete tokens containing anything other than numbers
        i = 0
        l = len(tokens)
        while i < l:
            try:
                int(tokens[i])
                i += 1
            except ValueError:
                tokens.pop(i)
                l -= 1

        chars = sorted(list(set(tokens)))
        self.char_to_int = dict((c, i) for i, c in enumerate(chars))
        self.int_to_char = dict((i, c) for i, c in enumerate(chars))

        self.n_chars = len(tokens)
        self.n_vocab = len(chars)
        print("Total Characters: ", self.n_chars)
        print("Total Vocab: ", self.n_vocab)

        # prepare the dataset of input to output pairs encoded as integers

        songs = self.raw_text.split("\n")
        for song in songs:
            notes = song.split(" ")
            i = 0
            l = len(notes)
            # delete invalid notes (strings that are not integers)
            while i < l:
                try:
                    int(notes[i])
                    i += 1
                except ValueError:
                    notes.pop(i)
                    l -= 1
            song_length = len(notes)
            for i in range(0, song_length - self.seq_length, 1):
                seq_in = notes[i:i + self.seq_length]
                seq_out = notes[i + self.seq_length]
                self.dataX.append([self.char_to_int[char] for char in seq_in])
                self.dataY.append(self.char_to_int[seq_out])

                self.n_patterns = len(self.dataX)
        print("Total Patterns: ", self.n_patterns)

    def train(self, checkpoint_name, improvement):
        # reshape X to be [samples, time steps, features]
        X = numpy.reshape(self.dataX, (self.n_patterns, self.seq_length, 1))
        # normalize
        X = X / float(self.n_vocab)
        # one hot encode the output variable
        y = np_utils.to_categorical(self.dataY)

        # define the LSTM model
        model = Sequential()
        model.add(LSTM(512, input_shape=(X.shape[1], X.shape[2])))
        model.add(Dropout(0.2))
        model.add(Lambda(lambda inpx: inpx))
        model.add(Dense(y.shape[1], activation='softmax'))
        if improvement != "":
            model.load_weights(improvement)
        model.compile(loss='categorical_crossentropy', optimizer='adam')

        # define the checkpoint
        filepath = checkpoint_name
        checkpoint = ModelCheckpoint(filepath, monitor='loss', verbose=1, save_best_only=True, mode='min')

        reduce_lr = ReduceLROnPlateau(monitor='loss', factor=0.2,
                      patience=2, min_lr=0.001)

        callbacks_list = [checkpoint, reduce_lr]

        # fit the model
        model.fit(X, y, epochs=40, batch_size=128, callbacks=callbacks_list)

    def prepare_to_generate(self, improvement, temperature):
        # reshape X to be [samples, time steps, features]
        X = numpy.reshape(self.dataX, (self.n_patterns, self.seq_length, 1))
        # normalize
        X = X / float(self.n_vocab)
        # one hot encode the output variable
        y = np_utils.to_categorical(self.dataY)

        # define the LSTM model
        self.model = Sequential()
        self.model.add(LSTM(512, input_shape=(X.shape[1], X.shape[2])))
        self.model.add(Dropout(0.2))
        self.model.add(Lambda(lambda inpx: inpx / temperature))
        self.model.add(Dense(y.shape[1], activation='softmax'))
        # load the network weights
        filename = improvement
        self.model.load_weights(filename)
        self.model.compile(loss='categorical_crossentropy', optimizer='adam')

    def generate(self, text_file_path, midi_file_path):
        # pick a random seed
        start = numpy.random.randint(0, len(self.dataX) - 1)
        pattern = self.dataX[start]
        print("start:", pattern)
        # generate characters
        notes = []
        for i in range(2000):
            x = numpy.reshape(pattern, (1, len(pattern), 1))
            x = x / float(self.n_vocab)
            prediction = self.model.predict(x, verbose=0)
            index = 0
            while index == 0:
                index = get_best_index(prediction[0], 10)
            result = self.int_to_char[index]
            notes.append(int(result))
            seq_in = [self.int_to_char[value] for value in pattern]
            # sys.stdout.write(result + " ")
            print(i)
            pattern.append(index)
            pattern = pattern[1:len(pattern)]
        csv_notes = DatasetBuilder.map_sequence_to_csv(notes, text_file_path)
        with open(text_file_path, 'w+') as the_file:
            for line in csv_notes:
                the_file.write(line)
        call(["csvmidi", text_file_path, midi_file_path])
        print("\nDone.")
