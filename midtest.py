import os
from subprocess import call

source = "D:/bandmate-data/bass-dataset"
destination = "D:/bandmate-data/midtest"

counter = 0
for root, dirs, files in os.walk(source):
    for name in files:
        if ".txt" in name:
            counter += 1
            new_filename = os.path.join(destination, name.replace(".txt", ".mid"))
            call(["csvmidi", os.path.join(root, name), new_filename])
            print(counter)

