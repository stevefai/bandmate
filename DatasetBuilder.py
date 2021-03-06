import os
from subprocess import call

class DatasetBuilder:
    pause_value = 200

    def __init__(self, source, destination):
        self.source = source
        self.destination = destination
        self.time_signature = "1, 0, time_signature, 4, 2, 24, 8\n"

    @staticmethod
    def delete_file(file_path):
        os.remove(file_path)

    @staticmethod
    def fix_time(time, time_unit):
        difference = time % time_unit
        # the note is slightly shifted to the left, so we need to shift it to the next time_unit
        if difference >= time_unit // 2:
            return time // time_unit + 1
        # the note is slightly shifted to the right or not at all, so we need to shift it to the previous time unit
        return time // time_unit

    @staticmethod
    def pad_spaces(prev_time, start_time, x):
        while prev_time < start_time:
            x.append(DatasetBuilder.pause_value)
            prev_time += 1

    @staticmethod
    def delete_extra_spaces(seq):
        tokens = seq
        i = 0
        while i < len(seq):
            if seq[i] == DatasetBuilder.pause_value:
                j = i + 1
                while j < len(seq) and seq[j] == DatasetBuilder.pause_value:
                    j += 1
                j -= 1
                # if we have spaces spanning more than a measure and a half
                if j - i + 1 >= 24:
                    limit = i - i % 16 + 16 + j % 16
                    seq = seq[:limit] + seq[j + 1:]
                    i = limit + 1
                else:
                    i = j + 1
            else:
                i += 1
        return seq

    @staticmethod
    def map_csv_to_sequence(seq):
        tokens = seq[0].split(',')

        x = []

        time_unit = int(seq[0].split(',')[-1]) // 4

        prev_time = 0
        tokens = seq[7].split(',')
        time = DatasetBuilder.fix_time(int(tokens[1]), time_unit)
        deduction = (time // 16)*16 * time_unit
        start_time = time % 16
        DatasetBuilder.pad_spaces(prev_time, start_time, x)

        for i in range(8, len(seq) - 1):
            tokens = seq[i].split(',')
            if i % 2 == 0:
                if "Note_off_c" in tokens[2] or int(tokens[-1]) == 0:
                    time = DatasetBuilder.fix_time(int(tokens[1]) - deduction, time_unit)
                    duration = time - start_time
                    if duration < 1:
                        raise ValueError('One note is too short')
                    while duration > 0:
                        x.append(int(tokens[4]))
                        duration -= 1
                    x.append(DatasetBuilder.pause_value)
                    prev_time = time
                else:
                    raise ValueError('Non-alternating note-on note-off pattern on line ' + str(i))
            else:
                start_time = DatasetBuilder.fix_time(int(tokens[1]) - deduction, time_unit)
                DatasetBuilder.pad_spaces(prev_time, start_time, x)
        return DatasetBuilder.delete_extra_spaces(x)

    @staticmethod
    def map_sequence_to_csv(x, file_path):
        bass_lines = [
            "0, 0, Header, 1, 2, 120\n",
            "1, 0, Start_track\n",
            "1, 0, Title_t, \"" + file_path + "\"\n",
            "1, 0, Time_signature, 4, 2, 24, 8\n",
            "1, 0, End_track\n",
            "2, 0, Start_track\n"
        ]

        time_unit = 30

        i = 0
        while x[i] == DatasetBuilder.pause_value:
            i += 1
        start_time = i*time_unit
        end_time = start_time
        no_note_endings = 0
        for step in range(i + 1, len(x)):
            if x[step] == DatasetBuilder.pause_value:
                if x[step-1] != DatasetBuilder.pause_value:
                    # end of a note
                    end_time = (step - no_note_endings)*time_unit
                    bass_lines.append("2, " + str(start_time) + ", Note_on_c, 1, " + str(x[step-1]) + ", 113\n")
                    bass_lines.append("2, " + str(end_time) + ", Note_off_c, 1, " + str(x[step - 1]) + ", 113\n")
                    no_note_endings += 1
            elif x[step] != DatasetBuilder.pause_value and x[step-1] == DatasetBuilder.pause_value:
                start_time = (step - no_note_endings)*time_unit
        bass_lines.append("2, " + str(end_time) + ", End_track\n")
        return bass_lines

    def process_file(self, file_path):

        try:
            found_bass = False
            found_time_signature = False
            bass_lines = ["0, 0, Header, 1, 2,",
                          "1, 0, Start_track\n",
                          "1, 0, Title_t, \"" + file_path + "\"\n",
                          "1, 0, Time_signature, 4, 2, 24, 8\n",
                          "1, 0, End_track\n",
                          "2, 0, Start_track\n"]

            should_delete = False

            with open(file_path) as my_file:
                bass_track_number = ""

                file_enum = enumerate(my_file, 0)

                for num, line in file_enum:
                    line_lower = line.lower()
                    if num == 0:
                        bass_lines[0] += line.split(',')[-1]
                    if "time_signature" in line_lower:
                        found_time_signature = True
                        if self.time_signature != line_lower:
                            should_delete = True
                            break
                    tokens = line.split(',')
                    if found_bass is True:
                        if tokens[0] == bass_track_number:
                            if "pitch" in line_lower:
                                should_delete = True
                                break
                            elif "Note_on_c" in line or "Note_off_c" in line or "End_track" in line:
                                bass_lines.append("2" + line[len(tokens[0]):])
                                if "End_track" in line and len(bass_lines) < 15:
                                    should_delete = True
                                    break
                    elif " piano" in line_lower or "\"piano\"" in line_lower or " guitar" in line_lower\
                            or "\"guitar\"" in line_lower:
                        found_bass = True
                        bass_track_number = tokens[0]
                        bass_lines.append("2" + line[len(tokens[0]):])

            if found_bass is False or found_time_signature is False or should_delete is True:
                DatasetBuilder.delete_file(file_path)
                return
            else:
                if len(bass_lines) > 1200 or len(bass_lines) < 100:
                    DatasetBuilder.delete_file(file_path)
                    return
                try:
                    x = DatasetBuilder.map_csv_to_sequence(bass_lines)
                    back_to_csv = DatasetBuilder.map_sequence_to_csv(x, file_path)
                    with open(file_path, 'w') as the_file:
                        for line in back_to_csv:
                            the_file.write(line)
                    with open(self.destination + "/all.txt", 'a+') as the_file:
                        for time_step in x:
                            the_file.write(str(time_step) + ' ')
                        the_file.write("\n ")
                except:
                    DatasetBuilder.delete_file(file_path)
                    return
        except:
            pass

    def build(self):
        counter = 0
        for root, dirs, files in os.walk(self.source):
            for name in files:
                if ".mid" in name:
                    counter += 1
                    new_filename = os.path.join(self.destination, name.replace(".mid", ".txt"))
                    call(["midicsv", os.path.join(root, name), new_filename])
                    self.process_file(new_filename)
                    print(counter)




