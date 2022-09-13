
"""Write hypercube_tree.json, which is the input for geco""" 

import json
from itertools import product
from datetime import datetime, timedelta


date = (datetime.now() - timedelta(2)).strftime('%Y-%m-%d')

time_refs = ['true_solar_time', 'universal_time']
time_steps = ['15minute', '1day', '1hour', '1minute', '1month']

sky_type_start_date = [
    {'date': ['2004-01-01/' + date],
     'sky_type': ['clear']},
    {'date': ['2004-02-01/' + date],
     'sky_type': ['observed_cloud']}
]

expert_mode_restrictions =[
    {'format': ['csv', 'netcdf'],
     'time_reference': time_refs,
     'time_step': time_steps},
    {'format': ['csv_expert'],
     'time_reference': ['universal_time'],
     'time_step': ['1minute']}]

with open('hypercube_tree.json', 'w') as f:
    f.write('{"_kids": [\n')
    f.write('  ' + ',\n  '.join(
        [json.dumps({**a, **b}) for a, b in product(sky_type_start_date,
                                                    expert_mode_restrictions)]))
    f.write('\n]}\n')
