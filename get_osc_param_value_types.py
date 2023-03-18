# -*- coding: utf-8 -*-
"""
Created on Wed Mar 15 10:51:06 2023

@author: Dell
"""

import json

with open("Presets.json", "r") as file:
    Presets = json.load(file)

with open("new_param_labels.json", "r") as file:
    new_param_labels = json.load(file)


# get all a_osc{i}_type and a_osc{i}_param{j} param_labels
osc_param_labels = set()
for i in range(15):
        if f'a_osc{i}_type' in new_param_labels:
            print( f'a_osc{i}_type')
        for j in range(15):
            if f'a_osc{i}_param{j}' in new_param_labels:
                print( f'a_osc{i}_param{j}')
                osc_param_labels.add(f'a_osc{i}_param{j}')
                
with open("osc_param_labels.json", "w") as output:
    json.dump(list(osc_param_labels), output)  

print(osc_param_labels)
              
                

# osc_type_1_count = 0
# for preset in Presets:
#     param_set = preset['param_set']
    
#     #iterate over osc's
#     for i in range (1,4):
        
#         # check if osc_type is set
#         if f'a_osc{i}_type' in param_set:
            
#             # check if osc_type is 1
#             if param_set[f'a_osc{i}_type']['value'] == 1:
#                 osc_type_1_count += 1

#print(osc_type_1_count)

def get_value_types_for_osc_params(new_param_labels, Presets):
    #get value types for a_osc_param[j] depending on osc_type and store as dict['a_osc{i}_param{j}'] in dict[osc_type]
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
                if osc_type == 0:
                    print('osc_type == 0')
                # check if osc_type exists in types_by_osc_type
                if osc_type not in types_by_osc_type[f'osc{i}']:
                    
                    # create dict for osc_type
                    types_by_osc_type[f'osc{i}'][osc_type] = {}
                
                # iterate over oscillator parameters j: a_osc{i}_param{j}      
                for j in range (8):
                    
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
    # param_4 sehr oft = 2, warum???
    for i in range(1,4):
        types_by_osc_type[f'osc{i}'][1] = {f'a_osc{i}_param1': 2, f'a_osc{i}_param2': 0, f'a_osc{i}_param3': 2, f'a_osc{i}_param4': 0, f'a_osc{i}_param5': 2, f'a_osc{i}_param6': 0}
    
    return types_by_osc_type

osc_param_value_types = get_value_types_for_osc_params(new_param_labels, Presets)
print(osc_param_value_types)

with open("osc_param_value_types.json","w") as output:
    json.dump(osc_param_value_types, output)
