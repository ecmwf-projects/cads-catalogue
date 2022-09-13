
"""Construct the whitelist, listing all fields that the user is allowed to
   download."""

import yaml
from os import rename
from os.path import dirname, abspath
import json

from cds_common import constraint_tools

# Import code from ../mars_param_groups.py
import sys
sys.path.append(dirname(dirname(abspath(__file__))))
from mars_param_groups import get_group_params


def main(adaptor):

    confile = 'constraints.json'
    confile_nowl = 'constraints_notwhitelisted.json'

    # The rest of this code assumes that the constraints.json was re-written by
    # geco. It renames it to constraints_notwhitelistes.json and then applies
    # the whitelist to create an altered version. If the constraints.json wasn't
    # re-written by geco then the code shouldn't be run (because
    # constraints.json presumably already has the whitelist applied to it) or
    # the file rename should be undone first.
    if adaptor.constraints_options.get('no_save', False):
        if 1:
            print('Not applying the whitelist to the constraints because '
                  'constraints were not updated')
            return
        else:
            # Only do this if you know confile_nowl is still valid
            rename(confile_nowl, confile)

    # Construct the whitelist
    whitelist = get_whitelist()

    # Apply it to the constraints
    whitelist_constraints(confile, confile_nowl, whitelist, adaptor)

    # Write it out
    write_whitelist(whitelist)


def get_whitelist():

    print('Making whitelist')

    # Get the list of all variables from the form groups
    with open('form.json') as f:
        form = yaml.safe_load(f)
    var_widget = [w for w in form if w['name'] == 'variable'][0]
    groups = var_widget['details']['groups']
    all_vars = sum([g['values'] for g in group_iterator(groups)], [])

    # Select only non-meteorological ones
    non_met_vars = sum([g['params'] for g in get_group_params()
                        if g['whitelist'] == True], [])
    non_met_vars = sorted(list(set(all_vars).intersection(non_met_vars)))

    # Sanity-check
    for string in ['temperature', 'pressure', 'humidity', 'wind',
                   'geopotential', 'cloud']:
        suspect = [v for v in non_met_vars if string in v.lower()
                   if v not in ['total_column_polar_stratospheric_cloud']]
        if suspect:
            raise Exception(f'Suspected meteorological variables: {suspect}')

    # Meteorological fields must not be made available until their validity time
    # is at least 24 hours in the past. The 00Z and 12Z forecasts run out to
    # T+120, so the latest fields from a 00Z forecast on the 1st of the month
    # are at midnight on the 6th, so this forecast should only be made available
    # at midnight on the 7th, so the dates can be whitelisted until current-6
    # for time=00:00. The same can't be done for the 12Z forecast because that
    # would make the T+120 fields available 12 hours too early, so the 12Z
    # forecast is only white listed at current-6.5.
    # Note that the interpretation of "current-6.5" is done in
    # cds_common.date_tools.replace_current and will lead to a change of date at
    # 12UTC.
    # The whitelist is used in three places: geco (only run occasionally
    # when the generate.yaml is updated), dataset.py (called from
    # update_latest_datetime each time the dataset is updated with a new
    # forecast) and the MARS adaptor. In the first two cases the whitelist (and
    # therefore the interpretation of "current") is baked into the constraints
    # at the time of execution, so the constraints will not suddenly allow
    # access to the D-6 12Z forecast at 12UTC - they will have to be
    # re-processed first. The MARS adaptor processes the whitelist at request
    # execution time however, so the adaptor will stop preventing access to the
    # D-6 12Z forecast at 12UTC exactly.
    whitelist = [
        {'time': ['00:00'], 'date': ['2012-07-05/current-6']},
        {'time': ['06:00'], 'date': ['2012-07-05/current-6.25']},
        {'time': ['12:00'], 'date': ['2012-07-05/current-6.5']},
        {'time': ['18:00'], 'date': ['2012-07-05/current-6.75']},
        {'variable': non_met_vars}]

    return whitelist


def group_iterator(groups):
    """Yield each group in turn. Allows for the possibility of nested
       subgroups."""
    for g in groups:
        if 'groups' in g:
            for g2 in group_iterator(g['groups']):
                yield g2
        else:
            yield g


def whitelist_constraints(confile, confile_nowl, whitelist, adaptor):

    print('Applying whitelist to constraints')

    # Read the un-whitelisted constraints
    with open(confile) as f:
        constraints = json.load(f)

    # Rename the file
    rename(confile, confile_nowl)

    # Apply the whitelist and re-write constraints.json
    constraint_tools.apply_whitelist(constraints, whitelist)
    constraint_tools.sort(constraints)
    with open(confile, 'w', encoding='utf-8') as f:
        print('[', file=f)
        if len(constraints) > 1:
            print(',\n'.join([json.dumps(adaptor.tidy(x, use_lists=True),
                                         sort_keys=False)
                              for x in constraints]), file=f)
        print(']', file=f)


def write_whitelist(whitelist):

    outfile = 'whitelist.yaml'
    with open(outfile, 'w') as f:
        f.write('###########################################################\n')
        f.write(f'# DO NOT EDIT. THIS FILE WAS MADE DYNAMICALLY BY {__file__}\n')
        f.write('###########################################################\n')
        yaml.dump(whitelist, f)
    print(f'Wrote {outfile}')


if __name__ == '__main__':
    main()

