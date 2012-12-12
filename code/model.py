from __future__ import with_statement

import os
import pickle
import re
import subprocess
import sys
import nltk

from sets import Set
from sets import ImmutableSet

class Model:
	class Type:
		BOTH = 0
		SVM = 1
		CRF = 2

	sentence_features = ImmutableSet(["pos"])
	word_features = ImmutableSet(["word", "length", "mitre"])
	
	labels = {
		"none":0,
		"treatment":1,
		"problem":2,
		"test":3
	}

	reverse_labels = {}
	for k, v in labels.iteritems():
		reverse_labels[v] = k

	libsvm_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "lib", "libsvm")
	svm_train = os.path.join(libsvm_path, "svm-train")
	if sys.platform == 'win32':
		svm_train = os.path.join(libsvm_path, "windows", "svm-train")
	svm_predict = os.path.join(libsvm_path, "svm-predict")
	if sys.platform == 'win32':
		svm_predict = os.path.join(libsvm_path, "windows", "svm-predict")

	def __init__(self, filename='awesome.model', type=Type.BOTH):
		self.filename = filename
		self.vocab = {}

		self.enabled_features = Model.sentence_features | Model.word_features
	
	def train(self, data, labels):
		svm_model_filename = self.filename + ".svm"
		crf_model_filename = self.filename + ".crf"

		rows = []
		for sentence in data:
			rows.append(self.features_for_sentence(sentence))

		for row in rows:
			for features in row:
				for feature in features:
					if feature not in self.vocab:
						self.vocab[feature] = len(self.vocab) + 1

		self.write_features(svm_model_filename, rows, labels, format = Model.Type.SVM)
		self.write_features(crf_model_filename, rows, labels, format = Model.Type.CRF)

		with open(self.filename, "a") as model:
			pickle.dump(self, model)

		svm_command = [Model.svm_train, "-s 1", "-t 0", svm_model_filename, svm_model_filename + ".trained"]
		output, error = subprocess.Popen(svm_command, stdout = subprocess.PIPE, stderr= subprocess.PIPE).communicate()
		
		
	def predict(self, data):
		with open(self.filename) as model:
			self = pickle.load(model)
		
		svm_model_filename = self.filename + ".svm.trained"
		crf_model_filename = self.filename + ".crf.trained"

		svm_test_input_filename = self.filename + ".test.input"
		svm_test_output_filename = self.filename + ".test.output"

		rows = []
		for sentence in data:
			rows.append(self.features_for_sentence(sentence))

		self.write_features(svm_test_input_filename, rows, None, format = Model.Type.SVM);

		svm_command = [Model.svm_predict, svm_test_input_filename, svm_model_filename, svm_test_output_filename]
		output, error = subprocess.Popen(svm_command, stdout = subprocess.PIPE, stderr= subprocess.PIPE).communicate()

		with open(svm_test_output_filename) as f:
		    lines = f.readlines()
		
		labels_list = []
		for sentence in data:
			labels = []
			for word in sentence:
				label = lines.pop(0)
				label = label.strip()
				labels.append(Model.reverse_labels[int(label)])
			
			labels_list.append(labels)

		return labels_list


	def write_features(self, filename, rows, labels, format=Type.SVM):

		if format == Model.Type.CRF:
			separator = "="
		else:
			separator = ":"

		with open(filename, "w") as f:
			for sentence_index in range(len(rows)):
				sentence = rows[sentence_index]
				
				if labels:
					sentence_labels = labels[sentence_index]

				if labels:
					if len(sentence) != len(sentence_labels):
						raise "Dimension mismatch"

				for word_index in range(len(sentence)):
					features = sentence[word_index]

					if labels:
						label = sentence_labels[word_index]

					columns = {}
					if labels:
						line = [str(Model.labels[label])]
					else:
						line = ["-1"]

					for item in features:
						if item in self.vocab:
							columns[self.vocab[item]] = features[item]

					for key in sorted(columns.iterkeys()):
						line.append(str(key) + separator + str(columns[key]))

					f.write(" ".join(line))
					f.write("\n")

			if format == Model.Type.CRF:
				f.write("\n")

		

	def features_for_sentence(self, sentence):
		features_list = []

		for word in sentence:
			features_list.append(self.features_for_word(word))

		for feature in Model.sentence_features:
			if feature not in self.enabled_features:
				continue

			if feature == "pos":
				tags = nltk.pos_tag(sentence)
				for index, features in enumerate(features_list):
					tag = tags[index][1]
					features[("pos", tag)] = 1

		return features_list

	def features_for_word(self, word):
		features = {}

		for feature in Model.word_features:
			if feature not in self.enabled_features:
				continue

			if feature == "word":
				features[(feature, word)] = 1

			if feature == "length":
				features[(feature, None)] = len(word)
			
			if feature == "mitre":
				for f in Model.mitre_features:
					if re.search(Model.mitre_features[f], word):
						features[(feature, f)] = 1

		return features

	mitre_features = {
		"INITCAP" : r"^[A-Z].*$",
		"ALLCAPS" : r"^[A-Z]+$",
		"CAPSMIX" : r"^[A-Za-z]+$",
		"HASDIGIT" : r"^.*[0-9].*$",
		"SINGLEDIGIT" : r"^[0-9]$",
		"DOUBLEDIGIT" : r"^[0-9][0-9]$",
		"FOURDIGITS" : r"^[0-9][0-9][0-9][0-9]$",
		"NATURALNUM" : r"^[0-9]+$",
		"REALNUM" : r"^[0-9]+.[0-9]+$",
		"ALPHANUM" : r"^[0-9A-Za-z]+$",
		"HASDASH" : r"^.*-.*$",
		"PUNCTUATION" : r"^[^A-Za-z0-9]+$",
		"PHONE1" : r"^[0-9][0-9][0-9]-[0-9][0-9][0-9][0-9]$",
		"PHONE2" : r"^[0-9][0-9][0-9]-[0-9][0-9][0-9]-[0-9][0-9][0-9][0-9]$",
		"FIVEDIGIT" : r"^[0-9][0-9][0-9][0-9][0-9]",
		"NOVOWELS" : r"^[^AaEeIiOoUu]+$",
		"HASDASHNUMALPHA" : r"^.*[A-z].*-.*[0-9].*$ | *.[0-9].*-.*[0-9].*$",
		"DATESEPERATOR" : r"^[-/]$",
	}
	