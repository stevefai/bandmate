from DatasetBuilder import DatasetBuilder


class DatasetBuilderTransition(DatasetBuilder):
    @staticmethod
    def map_csv_to_sequence(seq):
        tokens = seq[0].split(',')
        hit_first_note = False
        x = []

        time_unit = int(seq[0].split(',')[-1]) // 4

        prev_time = 0
        tokens = seq[7].split(',')
        time = DatasetBuilder.fix_time(int(tokens[1]), time_unit)
        deduction = (time // 16)*16 * time_unit
        start_time = time % 16
        DatasetBuilder.pad_spaces(prev_time, start_time, x)
        last_val = 0
        for i in range(8, len(seq) - 1):
            tokens = seq[i].split(',')
            if i % 2 == 0:
                if "Note_off_c" in tokens[2] or int(tokens[-1]) == 0:
                    time = DatasetBuilder.fix_time(int(tokens[1]) - deduction, time_unit)
                    duration = time - start_time
                    if duration < 1:
                        raise ValueError('One note is too short')
                    note_val = int(tokens[4])
                    if not hit_first_note:
                        x.append(note_val)
                        hit_first_note = True
                    else:
                        x.append(note_val - last_val)
                    while duration > 1:
                        x.append(0)
                        duration -= 1
                    x.append(DatasetBuilder.pause_value)
                    last_val = note_val
                    prev_time = time
                else:
                    raise ValueError('Non-alternating note-on note-off pattern on line ' + str(i))
            else:
                start_time = DatasetBuilder.fix_time(int(tokens[1]) - deduction, time_unit)
                DatasetBuilder.pad_spaces(prev_time, start_time, x)
        return DatasetBuilder.delete_extra_spaces(x)

    @staticmethod
    def map_sequence_to_csv(x, file_path):
        bass_lines = ["0, 0, Header, 1, 2, 120\n",
                      "1, 0, Start_track\n",
                      "1, 0, Title_t, \"" + file_path + "\"\n",
                      "1, 0, Time_signature, 4, 2, 24, 8\n",
                      "1, 0, End_track\n",
                      "2, 0, Start_track\n"]

        time_unit = 30

        i = 0
        while x[i] == DatasetBuilder.pause_value:
            i += 1
        start_time = i*time_unit
        end_time = start_time

        current_note = x[i]
        no_note_endings = 0
        last_note = 0

        for step in range(i + 1, len(x)):
            if x[step] == DatasetBuilder.pause_value:
                if x[step-1] != DatasetBuilder.pause_value:
                    # end of a note
                    end_time = (step - no_note_endings)*time_unit
                    bass_lines.append("2, " + str(start_time) + ", Note_on_c, 1, " + str(current_note) + ", 113\n")
                    bass_lines.append("2, " + str(end_time) + ", Note_off_c, 1, " + str(current_note) + ", 113\n")
                    last_note = current_note
                    no_note_endings += 1
            elif x[step] != DatasetBuilder.pause_value and x[step-1] == DatasetBuilder.pause_value:
                current_note = last_note + x[step]
                start_time = (step - no_note_endings)*time_unit
        bass_lines.append("2, " + str(end_time) + ", End_track\n")
        return bass_lines
