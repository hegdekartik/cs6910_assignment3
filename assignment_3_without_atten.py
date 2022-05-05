# -*- coding: utf-8 -*-
"""assignment-3 without atten.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1bqAsTKp0d7kAwzHfosDQvQg-L33DPE5K
"""

import os
import pandas as pd
import cv2
import tensorflow as tf
import numpy as np
import matplotlib.pyplot as plt
import pathlib
from tensorflow.keras import layers
from tensorflow.keras.layers import Dense, Input, InputLayer, Flatten, Activation, LSTM, SimpleRNN, GRU, TimeDistributed,RNN, Dense
from tensorflow.keras.utils import plot_model
from tensorflow.keras.models import load_model, Sequential,  Model
from tensorflow.keras.callbacks import EarlyStopping
import wandb

def dictLookup(vocab):
    char2int = dict([(char, i) for i, char in enumerate(vocab)])
    int2char = dict((i, char) for char, i in char2int.items())
    return char2int, int2char


def encode(source, target, sourceChar, targetChar, source_char2int=None, target_char2int=None):
    numEncoderTokens = len(sourceChar)
    numDecoderTokens = len(targetChar)
    maxSourceLength = max([len(txt) for txt in source])
    max_target_length = max([len(txt) for txt in target])

    sourceVocab, targetVocab = None, None
    if source_char2int == None and target_char2int == None:
        print("Generating the dictionary lookups for character to integer mapping and back")
        source_char2int, source_int2char = dictLookup(sourceChar)
        target_char2int, target_int2char = dictLookup(targetChar)

        sourceVocab = (source_char2int, source_int2char)
        targetVocab = (target_char2int, target_int2char)

    encoderInputData = np.zeros(
        (len(source), maxSourceLength, numEncoderTokens), dtype="float32"
    )
    decoderIData = np.zeros(
        (len(source), max_target_length, numDecoderTokens), dtype="float32"
    )
    decoderTData = np.zeros(
        (len(source), max_target_length, numDecoderTokens), dtype="float32"
    )

    for i, (input_text, target_text) in enumerate(zip(source, target)):
        for t, char in enumerate(input_text):
            encoderInputData[i, t, source_char2int[char]] = 1.0
        encoderInputData[i, t + 1 :, source_char2int[" "]] = 1.0
        for t, char in enumerate(target_text):
            # decoderTData is ahead of decoderIData by one timestep
            decoderIData[i, t, target_char2int[char]] = 1.0
            if t > 0:
                # decoderTData will be ahead by one timestep
                # and will not include the start character.
                decoderTData[i, t - 1, target_char2int[char]] = 1.0
        decoderIData[i, t + 1 :, target_char2int[" "]] = 1.0
        decoderTData[i, t:, target_char2int[" "]] = 1.0
    if sourceVocab != None and targetVocab != None:
        return (
            encoderInputData,
            decoderIData,
            decoderTData,
            sourceVocab,
            targetVocab,
        )
    else:
        return encoderInputData, decoderIData, decoderTData


def pre(source , target):
    #Preprocessing
    sourceChar = set()
    targetChar = set()

    source = [str(x) for x in source]
    target = [str(x) for x in target]

    sourceWord = []
    targetWord = []
    for src, tgt in zip(source, target):
        tgt = "\t" + tgt + "\n"
        sourceWord.append(src)
        targetWord.append(tgt)
        for char in src:
            if char not in sourceChar:
                sourceChar.add(char)
        for char in tgt:
            if char not in targetChar:
                targetChar.add(char)

    sourceChar = sorted(list(sourceChar))
    targetChar = sorted(list(targetChar))

    #The space needs to be appended to avoid errors in the encode function 
    sourceChar.append(" ")
    targetChar.append(" ")

    numEncoderTokens = len(sourceChar)
    numDecoderTokens = len(targetChar)
    maxSourceLength = max([len(txt) for txt in sourceWord])
    max_target_length = max([len(txt) for txt in targetWord])

    #Print the necessary data 
    print("Number of samples:", len(source))
    print("Source Vocab length:", numEncoderTokens)
    print("Target Vocab length:", numDecoderTokens)
    print("Max sequence length for inputs:", maxSourceLength)
    print("Max sequence length for outputs:", max_target_length)

    return encode(sourceWord, targetWord, sourceChar, targetChar)

def DataProcessing(DATAPATH,source_lang = 'en', target_lang = "ta"):


    
    train_path = os.path.join(DATAPATH, target_lang, "lexicons", target_lang+".translit.sampled.train.tsv")
    val_path = os.path.join(DATAPATH, target_lang, "lexicons", target_lang+".translit.sampled.dev.tsv")
    test_path = os.path.join(DATAPATH, target_lang, "lexicons", target_lang+".translit.sampled.test.tsv")
    train = pd.read_csv(
        train_path,
        sep="\t",
        names=["tgt", "src", "count"],
    )
    val = pd.read_csv(
        val_path,
        sep="\t",
        names=["tgt", "src", "count"],
    )
    test = pd.read_csv(
        test_path,
        sep="\t",
        names=["tgt", "src", "count"],
    )

    # creating train data
    train_data = pre(train["src"].to_list(), train["tgt"].to_list())
    (
        trainEncoderInput,
        trainDecoderInput,
        trainDecoderTarget,
        sourceVocab,
        targetVocab,
    ) = train_data
    source_char2int, source_int2char = sourceVocab
    target_char2int, target_int2char = targetVocab

    # creating validation data 
    valData = encode(
        val["src"].to_list(),
        val["tgt"].to_list(),
        list(source_char2int.keys()),
        list(target_char2int.keys()),
        source_char2int=source_char2int,
        target_char2int=target_char2int,
    )
    valEncoderInput, valDecoderInput, valDecoderTarget = valData
    source_char2int, source_int2char = sourceVocab
    target_char2int, target_int2char = targetVocab

    # creating test data
    testData = encode(
        test["src"].to_list(),
        test["tgt"].to_list(),
        list(source_char2int.keys()),
        list(target_char2int.keys()),
        source_char2int=source_char2int,
        target_char2int=target_char2int,
    )
    testEncoderInput, testDecoderInput, testDecoderTarget = testData
    source_char2int, source_int2char = sourceVocab
    target_char2int, target_int2char = targetVocab
    return source_lang,target_lang,source_char2int,target_char2int,trainEncoderInput, trainDecoderInput, trainDecoderTarget,valEncoderInput, valDecoderInput, valDecoderTarget



def build_configurable_model(cell_type,srcChar2Int,numEncoders,latentDim,dropout,tgtChar2Int,numDecoders,hidden):       
    if cell_type == "RNN":
        # one encoder RNN which sequentially encodes the input character sequence (Latin)
        encoderInput = Input(shape=(None, len(srcChar2Int)))
        encoderOutput = encoderInput
        for i in range(1, numEncoders + 1):
            encoder = SimpleRNN(
                latentDim,
                return_state=True,
                return_sequences=True,
                dropout=dropout,
            )
            encoderOutput, state = encoder(encoderInput)
        encoderState = [state]

        # one decoder RNN which takes the last state of the encoder as input and produces one output character at a time (Devanagari).
        decoderInput = Input(shape=(None, len(tgtChar2Int)))
        decoderOutput = decoderInput
        for i in range(1, numDecoders + 1):
            decoder = SimpleRNN(
                latentDim,
                return_sequences=True,
                return_state=True,
                dropout=dropout,
            )
            decoderOutput, _ = decoder(decoderInput, initial_state=encoderState)

        # dense
        hidden = Dense(hidden, activation="relu")
        hiddenOutput = hidden(decoderOutput)
        decoderDense = Dense(len(tgtChar2Int), activation="softmax")
        decoderOutput = decoderDense(hiddenOutput)
        model = Model([encoderInput, decoderInput], decoderOutput)
        
        return model
    


#Check for GPU's
    
physical_devices = tf.config.list_physical_devices('GPU')
try:
    tf.config.experimental.set_memory_growth(physical_devices[0], True)
except:
#Invalid device or cannot modify virtual devices once initialized.
    pass

path = os.path.dirname(os.getcwd())
DATAPATH = path +'/dakshina_dataset_v1.0'
#Processing the data
source_lang,target_lang,source_char2int,target_char2int,trainEncoderInput, trainDecoderInput, trainDecoderTarget,valEncoderInput, valDecoderInput, valDecoderTarget = DataProcessing(DATAPATH)


from tensorflow.keras import Input, Model
from wandb.keras import WandbCallback



def train():

    #HardCode Values
    config_defaults = {
        "cell_type": "RNN",
        "latentDim": 256,
        "hidden": 128,
        "optimiser": "rmsprop",
        "numEncoders": 1,
        "numDecoders": 1,
        "dropout": 0.2,
        "epochs": 1,
        "batch_size": 64,
    }


    wandb.init(config=config_defaults, project="cs6910_assignment3", entity="cs6910_assignment")
    config = wandb.config
    wandb.run.name = (
        str(config.cell_type)
        + source_lang
        + str(config.numEncoders)
        + "___"
        + target_lang
        + "___"
        + str(config.numDecoders)
        + "___"
        + config.optimiser
        + "___"
        + str(config.epochs)
        + "___"
        + str(config.dropout) 
        + "___"
        + str(config.batch_size)
        + "___"
        + str(config.latentDim)
    )
    wandb.run.save()

    # Setting up variables

    numEncoders = config["numEncoders"]
    cell_type = config["cell_type"]
    latentDim = config["latentDim"]
    dropout = config["dropout"]
    numDecoders = config["numDecoders"]
    hidden = config["hidden"]
    tgtChar2Int = target_char2int
    srcChar2Int = source_char2int
    
    #Building the model
    model = build_configurable_model(cell_type,srcChar2Int,numEncoders,latentDim,dropout,tgtChar2Int,numDecoders,hidden)

    #Model Summary    
    model.summary()

    model.compile(
        optimizer=config.optimiser,
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )

    #Early stopping to stop the epoch if the accuracy is not increasing 
    earlystopping = EarlyStopping(
        monitor="val_accuracy", min_delta=0.01, patience=5, verbose=2, mode="auto"
    )

    model.fit(
        [trainEncoderInput, trainDecoderInput],
        trainDecoderTarget,
        batch_size=config.batch_size,
        epochs=config.epochs,
        validation_data=([valEncoderInput, valDecoderInput], valDecoderTarget),
        callbacks=[earlystopping, WandbCallback()],
    )

    #Saving the trained models
    model.save(os.path.join("./TrainedModels", wandb.run.name))    
    wandb.finish()
    
    

train()





