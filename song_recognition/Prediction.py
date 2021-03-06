from typing import List
from os import listdir
from AudioProcessing import *
from collections import Counter
import numpy as np
from FingerPrintDatabase import FingerPrintDatabase, get_fingerprints
from SongDatabase import *
from Spectrograms import spectrogram, local_peaks

'''
potential features:
- real time audio
- ratio for more accurate predictions
- website?

'''

# main prediction functions should be here
# it uses other classes for the prediction
class Predictor:
    def __init__(self) -> None:
        self.fingerprints = FingerPrintDatabase()
        self.songs = SongDatabase()
        self.pollster = Counter()
        self.percent_thres = 75
        self.fanout_value = 15
        self.thres_ratio = 1.5
    
    def tally(self, songs : List, time0):
        if not songs is None: 
            self.pollster.update(Counter([(song, time-time0) for song, time in songs]))

    def get_tally_winner(self):
        # print(self.pollster.most_common()[:4])
        if len(self.pollster)==0:
            return 'None'
        common, ratio = self.confidence_ratio()
        self.pollster = Counter()
        print(ratio)
        if ratio < self.thres_ratio:
            return 'None'
        return common
        
    def confidence_ratio(self):
        # uses the built in counters to find an approximate ratio for confident guesses
        counter = self.pollster.most_common()
        # takes the "most common" song
        most_common = counter[0][0][0]
        common_two = None
        for index in range(1, len(counter)):
            if counter[index][0][0] != most_common:
                common_two = index
                break
        if common_two is None:
            ratio = 1e9
        else:
            ratio = counter[0][1] / counter[common_two][1]
        return self.songs.id2name[most_common], ratio

    def add_song(self, file_path : str, songname : str, artist : str):
        if songname in self.songs.name2id:
            return
        audio, sampling_rate = read_song(file_path)
        # these should read in discrete digital data
        spectro, freqs, times = spectrogram(audio)
        # returns (Frequency, Time) data
        thres = np.percentile(spectro, self.percent_thres)
        peaks = local_peaks(spectro, thres)
        self.songs.save_song(peaks, songname, artist, self.fingerprints, self.fanout_value)
    
    def add_songs(self, *, dir_path : str):
        files = listdir(dir_path)
        for file in files:
            if 'DS_Store' in file:
                continue
            print(f'reading {file}')
            file_parts = file.split('_')
            self.add_song(dir_path+"/"+file, *file_parts[:2])
    
    def delete_song(self, songname : str):
        self.songs.delete_song(songname, self.fanout_value,self.fingerprints)

    def save_data(self, dir_path):
        self.songs.save_data(dir_path+"/songs")
        self.fingerprints.save_data(dir_path+"/fingerprints")
    
    def load_data(self, dir_path):
        self.songs.load_data(dir_path+"/songs")
        self.fingerprints.load_data(dir_path+"/fingerprints")

    def predict(self, *, file_path : str = '', record_time : float = 0, samples : np.ndarray = None):
        # this is meant to be a function that indicates the general structure of the program
        # it uses some pseudo functions that should be implemented
        if file_path!='':
            audio, sampling_rate = read_song(file_path)
        elif record_time > 0:
            audio = record_song(record_time)
        else:
            audio = samples
        # these should read in discrete digital data
        spectro, freqs, times = spectrogram(audio)
        # returns (Frequency, Time) data
        thres = np.percentile(spectro, self.percent_thres)
        peaks = local_peaks(spectro,thres)
        # returns a list of peaks (f, t)
        fingerprints, times = get_fingerprints(peaks, self.fanout_value)
        for fingerprint, time in zip(fingerprints,times):
            songs = self.fingerprints.query_fingerprint(fingerprint)
            self.tally(songs, time)
        ret = self.get_tally_winner()
        if ret=='None':
            return "Oops, did not find this song!"
        else:
            return ret


# predictor.save_data('database')
# first_print = (202, 831, 0)
# print(predictor.fingerprints.database[first_print])
# print(predictor.fingerprints.query_fingerprint(first_print))

# predictor.delete_song('Imperial-March')
# print(len(predictor.fingerprints.database))