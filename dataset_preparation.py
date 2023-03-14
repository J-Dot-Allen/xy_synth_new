#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Feb 11 17:21:13 2023

@author: philipp, Malte Cohrt

dataset_preparation.py

This script loads the list of Presets [Presets.json] and extracts the relevant data for the dataset: ParameterSets, preset_labels and param_labels.
Presets with B-Scenes get removed from the dataset as well as FX-Parameters. Two Presets get removed, because they cause a very high loss and are likely to be FX- or Template-Presets and not Synth-Presets.
A new list of parameter lables (new_param_labels) is created. Only the Parameter items "label" and "value" are used in the Dataset. The dataset is then normalized and a second value encoding the on/off status [1.0/0.0] is added for every Parameter.
The dataset is saved as a TF-Dataset.


DESCRIPTION OF PRESET AND PARAMETER
    
A Preset contains (almost) all the information of the corresponding fxp file.
The Parameters and their values of each Preset are saved in a dict with the param_label as the key.
The dict of the parameters is reachable via the key "param_set". 

Preset = {
    "preset_label": preset.label,
    "plugin_id": preset.plugin_id,
    "plugin_version": preset.plugin_version,
    "num_params": preset.num_params,
    "param_set": dict_of_parameters,
    "chunk_params": get_chunk_params(preset),
    "chunk_header": get_chunk_header(preset),
    "chunk_footer": get_chunk_footer(preset)
    }


Parameters are saved as Dictionary. Each Parameter-Item gets it's own key like: "value", "value_type", "modrouting

param = {
  "param_label": param_label,
  "value_type": value_type.value,
  "value": param_value;
  „modrouting_source_[i]“: int(source),
  „moddepth_[i]“: float(depth), 
  „mod_muted_[i]“: int(muted),
  „modsource_index_[i]“: int(source_index), 
  „mod_source_scene_[i]“: int(source_scene),
  „item_label“: int(item_value),
}


"""

import json
import pandas as pd
import analyze_functions as afunc
import os
import tensorflow as tf

# MAIN

def main():
    # LOAD JSON 
    with open("Presets.json", "r") as file:
        Presets = json.load(file)
    
    # # # GET DATA
    
    # get param_labels
    all_labels = afunc.get_all_param_labels(Presets)
    param_labels = sorted(all_labels)
        
    # GET DATASET
    
    # value_sets as list of dict {'preset_id': 1, 'value_set': [[0., 0.], [0.23, 1.],...]} ordere as param_labels
    value_sets = get_value_sets(Presets, param_labels)

        
    # transform dataset to dataframe
    df = pd.DataFrame(value_sets, columns = param_labels)
    
    # add preset_ids to dataframe
    preset_ids = range(len(Presets))
    df.insert(0, "preset_id", preset_ids)
    
    # DELETE B-SCENES
    # b_param_labels = [col for col in df if col.startswith('b_')]
    # df = df.drop(columns = b_param_labels)
    
    #Dataset preparation: Deletion of b_-scene Parameters & and droping rows where b_-values are used
    #df.drop(list(df.filter(regex = 'b_|fx|FX')), axis = 1, inplace = True)
    df.drop(list(df.filter(regex = 'b_|FX|fx')), axis = 1, inplace = True)
    df.loc[:, df.columns.str.startswith('foo')]
    df = df[df.scenemode != 1]
    
    # make dataset a list again
    dataset = df.values.tolist()
    
    # # get rid of presets causing very high loss
    # # Liste von Presets, die einen absurden loss erzeugen: 580, 633
    dataset = dataset[:580] + dataset[581:632] + dataset[634:]
    
    # get preset_ids
    preset_ids = [ int(x[0]) for x in dataset]
    
    # get value_sets
    value_sets = [x[1:] for x in dataset]
    
    
    # GET INFO FOR PREDICTIONS
    
    # GET NEW PARAM LABELS
    # get new param_labels, because some got deleted
    new_param_labels = df.columns.values.tolist()[1:] # [1:] to ignore 'preset_id'
    
    # write new param_labels into json file
    with open("new_param_labels.json", "w") as output:
        json.dump(new_param_labels, output)
        
    # GET VALUE TYPES
    # get dict with all value types
    value_types = afunc.get_dict_of_value_types(new_param_labels, Presets)
    
    # write dict of value types into JSON file
    with open("value_types.json", "w") as output:
        json.dump(value_types, output) 
    
    # GET MIN MAX VALUES
    # Get min, max values
    min_vals, max_vals = get_min_max_values(value_sets) 
    min_max_vals = [[x, y] for x,y in zip(min_vals, max_vals)] 
    
    # Write Dict of min, max values
    min_max = {}
    for i, param_label in enumerate(new_param_labels):
        min_max[param_label] = min_max_vals[i]
         
    # write dict of min max vals into json file
    with open("min_max_dict.json", "w") as output:
        json.dump(min_max, output)
      
    # # NORMALIZE VALUE SETS 
    val_sets_norm = normalize_dataset(value_sets, min_vals, max_vals)
    
    # # write dataset_norm into json file
    # with open("dataset_norm.json", "w") as output:
    #     json.dump(dataset_norm, output)
        
    # with open("dataset_norm.json", "r") as file:
    #    dataset_norm = json.load(file)
    
    # REPLACING None VALUES AND ADDING MASK --> 2D DATA STRUCTURE  
    val_sets_2D = add_masks2dataset(val_sets_norm)
    
    # write val_sets_2D into json file
    with open("val_sets_2D.json", "w") as output:
        json.dump(val_sets_2D, output)
    
    # MAKE TF-DATASET

    dataset = tf.data.Dataset.from_tensor_slices({"preset_id": preset_ids, "value_set": val_sets_2D})
    
    # save tf dataset
    dir_path = os.path.dirname(os.path.realpath(__file__))
    path = os.path.join(dir_path, "saved TF_datasets")
    dataset.save(path)


# FUNCTIONS

def get_value_sets(Presets, param_labels):
    dataset = []
    for preset in Presets:
        param_values = [None]*len(param_labels)
        # iterate over param_labels
        for index, param_label in enumerate(param_labels):
            if param_label in preset['param_set']:
                # get param with param_label
                param = preset['param_set'][param_label]
                # write param value at correct index into param_values
                param_values[index] = param['value']
        dataset.append(param_values)
    return dataset

def get_min_max_values(value_sets):
    max_vals = value_sets[0].copy()
    min_vals = value_sets[0].copy()
    for value_set in value_sets:
        for i, value in enumerate(value_set):
            # if max_vals[i] == None -> write current value into max_vals
            if max_vals[i]== None:
                max_vals[i] = value
            # if max_vals[i] is smaller than current value -> write current value into max_vals
            elif not value == None and max_vals[i] < value:
                max_vals[i] = value
            if min_vals[i] == None:
                min_vals[i] = value
            elif not value == None and min_vals[i] > value:
                min_vals[i] = value

    return min_vals, max_vals

def normalize_dataset(value_sets, min_vals, max_vals):
    val_sets_norm = []
    for value_set in value_sets:
        val_set_norm = []
        for i, value in enumerate(value_set):
            if value == None:
                val_norm = None
            else:
                if min_vals[i] == max_vals[i]:
                    if value < 0:
                        val_norm = 0
                    elif value > 1:
                        val_norm = 1
                    else:
                        val_norm = value
                else:
                    val_norm = (value - min_vals[i]) / (max_vals[i] - min_vals[i])
            if not val_norm == None:
                val_norm = float(val_norm)
            val_set_norm.append(val_norm)
        val_sets_norm.append(val_set_norm)
    return val_sets_norm

def add_masks2dataset(value_sets):
    val_sets_2D = []
    for value_set in value_sets:
        val_on_off_pairs = [] # to add preset_id [value_set[0]]
        for val in value_set:  # use [1:] to exlude preset_id
            if pd.isna(val):
                val_on_off_pair = [0., 0.]
            else:
                val_on_off_pair =  [val, 1.]
            val_on_off_pairs.append(val_on_off_pair)
        val_sets_2D.append(val_on_off_pairs)
    return val_sets_2D




        
main()