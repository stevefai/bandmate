from Lstm import Lstm


# checkpoint name: "weights-improvement-mainpiano-{epoch:02d}-{loss:.4f}.hdf5"

lstm = Lstm("D:/environments/licenta/data/all.txt")
# lstm.train("weights-improvement-{epoch:02d}-{loss:.4f}.hdf5", "weights-improvement-03-0.2972.hdf5")
lstm.prepare_to_generate("weights-improvement-03-0.2972.hdf5", 1000)
lstm.generate("D:/environments/licenta/results/result.txt", "D:/environments/licenta/results/result.mid")
