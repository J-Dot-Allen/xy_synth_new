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
import os
import tensorflow as tf

# MAIN

def main():
    # LOAD DATA
    
    with open("Presets.json", "r") as file:
        Presets = json.load(file)
        
    with open("osc_param_indices.json", "r") as file:
        osc_param_indices = json.load(file)
        
    with open("osc_param_min_max.json", "r") as file:
        osc_param_min_max = json.load(file)
    
    # # # GET DATA
    
    # get param_labels
    all_labels = get_all_param_labels(Presets)
    param_labels = sorted(all_labels)
        
    # GET DATASET
    
    # value_sets as list of dict {'preset_id': 1, 'value_set': [[0., 0.], [0.23, 1.],...]} ordere as param_labels
    value_sets = get_value_sets(Presets, param_labels)

        
    # transform dataset to dataframe
    df = pd.DataFrame(value_sets, columns = param_labels)
    
    # add preset_ids to dataframe
    preset_ids = range(len(Presets))
    df.insert(0, "preset_id", preset_ids)
    
    # DELETE B-SCENES AND FX PARAMETER
    # b_param_labels = [col for col in df if col.startswith('b_')]
    # df = df.drop(columns = b_param_labels)
    
    #Dataset preparation: Deletion of b_-scene Parameters & and droping rows where b_-values are used
    df.drop(list(df.filter(regex = 'b_|FX|fx')), axis = 1, inplace = True)

    df = df[df.scenemode != 1]
    
    # make dataset a list again
    dataset = df.values.tolist()
    
    # # get rid of presets causing very high loss
    # # list of presets causing a very high loss: 580, 633
    dataset = dataset[:580] + dataset[581:632] + dataset[634:]
    
    # get preset_ids
    preset_ids = [ int(x[0]) for x in dataset]
    
    # get value_sets
    value_sets = [x[1:] for x in dataset]
    
    # export value_sets for testing
    with open("value_sets.json", "w") as output:
        json.dump(value_sets, output)
    
    # GET INFO FOR PREDICTIONS
    
    # GET NEW PARAM LABELS
    # get new param_labels, because some got deleted
    new_param_labels = df.columns.values.tolist()[1:] # [1:] to ignore 'preset_id'
    
    # write new param_labels into json file
    with open("new_param_labels.json", "w") as output:
        json.dump(new_param_labels, output)
        
    # GET VALUE TYPES
    # get dict with all value types
    value_types = get_dict_of_value_types(new_param_labels, Presets)
    
    # write dict of value types into JSON file
    with open("value_types.json", "w") as output:
        json.dump(value_types, output) 
        
    # get value types for osc_params
    osc_param_value_types = get_value_types_for_osc_params(new_param_labels, Presets)

    with open("osc_param_value_types.json","w") as output:
        json.dump(osc_param_value_types, output)

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
    val_sets_norm = normalize_dataset(value_sets, min_vals, max_vals, new_param_labels, osc_param_indices, osc_param_min_max, osc_param_value_types, preset_ids, Presets)
    
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

def get_all_param_labels(Presets):
    labels = set()
    for preset in Presets:
        param_set = preset['param_set']
        for param_label in param_set:
            labels.add(param_label)
    return labels

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

def get_dict_of_value_types(param_labels, Presets):
    types = {}
    for preset in Presets:
        # for every preset iterate over param_labels
        for param_label in param_labels:
            # check if param label is in the param_set of the preset
            if param_label in preset['param_set']:
                param = preset['param_set'][param_label]
                #  check if the param_label is already in types
                if param_label in types:
                    # check if value type changes over Presets
                    if types[param_label]!= param["value_type"]:
                        #print(param)
                        #print(f"Value Type seems to change over different Presets! value_type before: {types[param_label]}")
                        
                        # if type changes over Presets -> set value type to float
                        types[param_label] = int(2)
                else:
                    types[param_label] = param["value_type"]
    return types

def get_value_types_for_osc_params(new_param_labels, Presets):
    #get value types for a_osc_param[j] depending on osc_type and store in dict[f'osc{i}'][f'{osc_type}'][f'a_osc{i}_param{j}']
    #create dict to store all dicts for osc_type in
    types_by_osc_type = {}
    for i in range (1,4):
        types_by_osc_type[f'osc{i}'] = {} 
    #print(types_by_osc_type)
    changing_types = set()
    for preset in Presets: 
    
        # for every preset get a_osc[i]_type
        for i in range(1,4):
            
            # check if osc_type exists in preset
            if f'a_osc{i}_type' in preset['param_set']:
                
                
                # get osc_type in preset
                osc_type = int(preset['param_set'][f'a_osc{i}_type']['value'])
                # #print(osc_type)
                # if osc_type == 1:
                
                # check if osc_type exists in types_by_osc_type
                if osc_type not in types_by_osc_type[f'osc{i}']:
                    
                    # create dict for osc_type
                    types_by_osc_type[f'osc{i}'][osc_type] = {}
                
                # iterate over oscillator parameters j: a_osc{i}_param{j}      
                for j in range(7):
                    
                    # get param_label for oscillator param[j]
                    param_label = f'a_osc{i}_param{j}'
                    
                    # check if param_label exists in preset
                    if param_label in preset['param_set']:
                    
                        # get param in preset
                        param = preset['param_set'][param_label]
                        
                        # check if param_label already exists in dict for osc[i]_type
                        if param_label in types_by_osc_type[f'osc{i}'][osc_type]:
                            
                            # check if value type changes over Presets
                            if types_by_osc_type[f'osc{i}'][osc_type][param_label]!= param['value_type']:
                                # print(f"Value Type seems to change over different Presets! \n param_label: {param_label}; value_type before: {types_by_osc_type[f'osc{i}'][osc_type][param_label]}")
                                #print(f'new param: {param}')
                                #print(f'a_osc{i}_type: osc_type {osc_type} \n')
                                pass
                        # write param[j] type into dict for osc[i]_type
                        types_by_osc_type[f'osc{i}'][osc_type][param_label] =  preset['param_set'][param_label]['value_type']
                        # print(preset['preset_label'])
                        # print(preset['param_set'][f'a_osc{i}_type'])
                        # print(param)
                        # print(types_by_osc_type)
                        changing_types.add(f'osc{i}, osc_type: {osc_type}, {param_label}')

    # manually set values for osc_type = 1
    for i in range(1,4):
        types_by_osc_type[f'osc{i}']['1'] = {f'a_osc{i}_param1': 2, f'a_osc{i}_param2': 0, f'a_osc{i}_param3': 2, f'a_osc{i}_param4': 0, f'a_osc{i}_param5': 2, f'a_osc{i}_param6': 0}
    
    return types_by_osc_type

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

def normalize_dataset(value_sets, min_vals, max_vals, new_param_labels, osc_param_indices, osc_param_min_max, osc_param_value_types, preset_ids, Presets):
    val_sets_norm = []
    
    # iterate over value_sets and get preset_id
    for index, value_set in enumerate(value_sets):
        
        val_set_norm = []
        preset_id = preset_ids[index]
        
        # iterate over values
        for i, value in enumerate(value_set):
            
            if value == None:
                val_norm = None
            
            # get param_label
            param_label = new_param_labels[i]
                
            # check if param is osc{i}_param
            for i in range (1,4):
                if param_label in osc_param_value_types[f'osc{i}']['1']:
                    #print(param_label)
                    
                    if f'a_osc{i}_type' not in Presets[preset_id]['param_set']:
                        osc_type = 0
                        #print(f'preset_id: {preset_id}')
                    else:
                        # get osc_type:
                        osc_type = Presets[preset_id]['param_set'][f'a_osc{i}_type']['value']
                        # round to int
                        osc_type = round(osc_type)
                    
                    # get min_val
                    min_val = osc_param_min_max[f'osc{i}'][f'{osc_type}'][param_label]['min']
                    #print(min_val)
                    
                    # get max_val
                    max_val = osc_param_min_max[f'osc{i}'][f'{osc_type}'][param_label]['max']
                    #print(max_val)

            else:
                min_val = min_vals[i]
                max_val = max_vals[i]
                
            if min_val == max_val:
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
        #print(val_set_norm)
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