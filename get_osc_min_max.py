# -*- coding: utf-8 -*-
"""
Created on Fri Mar 17 12:29:52 2023

@author: Dell
"""
import json

with open("Presets.json", "r") as file:
    Presets = json.load(file)

with open("new_param_labels.json", "r") as file:
    new_param_labels = json.load(file)
    
with open("osc_param_labels.json", "r") as file:
    osc_param_labels = json.load(file)

with open("value_sets.json", "r") as file:
    value_sets = json.load(file)

def get_osc_params_min_max(value_sets, Presets):
    #get min_max for a_osc_param[j] depending on osc_type and store in dict[f'osc{i}'][f'{osc_type}'][f'a_osc{i}_param{j}']
    
    # create dict to store all dicts for osc_type in
    min_max_by_osc_type = {}
    for i in range (1,4):
        min_max_by_osc_type[f'osc{i}'] = {} 
        
        
    # iterate over all Presets
    for preset in Presets: 
    
        # for every preset get a_osc[i]_type
        for i in range(1,4):
            
            # check if osc_type exists in preset
            if f'a_osc{i}_type' in preset['param_set']:
                
                # get osc_type in preset
                osc_type = int(preset['param_set'][f'a_osc{i}_type']['value'])
          
                
                # check if osc_type exists in types_by_osc_type for osc{i}
                if osc_type not in min_max_by_osc_type[f'osc{i}']:
                    
                    # create dict for osc_type and set param_value as min and max
                    min_max_by_osc_type[f'osc{i}'][osc_type] = {}
                
                # iterate over oscillator parameters j: a_osc{i}_param{j}      
                for j in range (7):
                    
                    # get param_label for oscillator param[j]
                    param_label = f'a_osc{i}_param{j}'
                    
                    # check if param_label exists in preset
                    if param_label in preset['param_set']:
                    
                        # get value of param in preset
                        value = preset['param_set'][param_label]['value']
                        
                        # check if param_label already exists in dict for osc[i]_type
                        if param_label not in min_max_by_osc_type[f'osc{i}'][osc_type]:
                            
                            # if param_label ist not in dict set min and max to param_value 
                            min_max_by_osc_type[f'osc{i}'][osc_type][f'a_osc{i}_param{j}'] = { 'min': value, 'max': value}
                        
                        else:
                            # get current min and max values
                            min_val = min_max_by_osc_type[f'osc{i}'][osc_type][f'a_osc{i}_param{j}']['min']
                            max_val = min_max_by_osc_type[f'osc{i}'][osc_type][f'a_osc{i}_param{j}']['max']
                            
                    
                            
                            #  if max_val == None -> write current value into max_vals
                            if max_val== None:
                                 min_max_by_osc_type[f'osc{i}'][osc_type][f'a_osc{i}_param{j}']['max'] = value
                                 
                            # if max_vals[i] is smaller than current value -> write current value into max_vals
                            elif not value == None and max_val < value:
                                 print(f"before: {min_max_by_osc_type[f'osc{i}'][osc_type][f'a_osc{i}_param{j}']}")
                                 min_max_by_osc_type[f'osc{i}'][osc_type][f'a_osc{i}_param{j}']['max'] = value
                                 print(f'value: {value}')
                                 print(f"after: {min_max_by_osc_type[f'osc{i}'][osc_type][f'a_osc{i}_param{j}']}") 
                            if min_val == None:
                                min_max_by_osc_type[f'osc{i}'][osc_type][f'a_osc{i}_param{j}']['min'] = value
                            elif not value == None and min_val > value:
                                print(f"before: {min_max_by_osc_type[f'osc{i}'][osc_type][f'a_osc{i}_param{j}']}")
                                min_max_by_osc_type[f'osc{i}'][osc_type][f'a_osc{i}_param{j}']['min'] = value
                                print(f'value: {value}')
                                print(f"after: {min_max_by_osc_type[f'osc{i}'][osc_type][f'a_osc{i}_param{j}']}") 
                            
    return min_max_by_osc_type


# osc_param_min_max = get_osc_params_min_max(value_sets, Presets)

# with open("osc_param_min_max.json", "w") as output:
#     json.dump(osc_param_min_max, output)                        
# print(osc_param_labels)


with open("osc_param_min_max.json", "r") as file:
    osc_param_min_max = json.load(file)   

print(osc_param_min_max['osc2']['0']['a_osc1_param3'])

#print(osc_param_min_max)
# get indices of osc_param_labels

# iterate over new_param_labels and check if param_label is in osc_param_labels
# indices = []
# for index, param_label in enumerate(new_param_labels):
#     if param_label in osc_param_labels:
#         indices.append(index)

# with open("osc_param_indices.json", "w") as output:
#     json.dump(indices, output)
        