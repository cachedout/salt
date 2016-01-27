# -*- coding: utf-8 -*-
'''
Utility functions for salt profiling
'''

import logging
import salt.utils.odict

try:
    import json
    HAS_JSON = True
except ImportError:
    HAS_JSON = False

log = logging.getLogger(__name__)

def compile_highstate_profile(profile):
    '''
    Take a profiling dictionary of the following form:

    {'profile':
        {'saltutil.is_running': 1453832872.037091,
         'cmd.run': 1453832870.662169,
         'grains.get': 1453832872.037682,
         'timezone.get_offset': 1453832870.661436,
         'config.option': 1453832872.087138,
         'mine.update': 1453832871.718176,
         'state.sls': 1453832872.032654,
         'config.merge': 1453832871.718164},
         'highstate_profile': {'my_state_chunk': 1453832872.086021}
    }

    Examine the highstate profile data and then sort the execution module timing such that a dictionary
    is returned where each chunk is is a top-level key containing values for attendent execution
    module calls which fall between the current chunk's execution time and then next.
    '''
    if not 'highstate_profile' in profile:
        return {}
    else:
        ret = salt.utils.odict.OrderedDict()
        # Pop the highstate_profile off and store it on its own
        highstate_profile = profile['highstate_profile']

        # Begin ordering chunks by time.
        ordered_chunk_keys = sorted(profile['highstate_profile'], key=profile['highstate_profile'].get)
        del profile['highstate_profile']
        ordered_profile_keys = sorted(profile, key=profile.get)

        chunk_index = 0
        for chunk in ordered_chunk_keys:
            # Look forward one chunk to know where to end
            import pudb; pu.db
            if len(ordered_chunk_keys) > chunk_index + 1:
                next_chunk = ordered_chunk_keys[chunk_index]
                # OK, we have our current chunk and a forward-looking chunk!
                # Now, let's look for some timings that match.
                for func in ordered_profile_keys:
                    if profile[func] < highstate_profile[chunk] and profile[func] < highstate_profile[next_chunk]:
                        # A call belongs to this chunk!
                        # If we don't already have a tracking dict, make one:
                        if highstate_profile[chunk] not in ret:
                            ret[chunk] = salt.utils.odict.OrderedDict()
                        else:
                            ret[chunk].update(profile[func]) 
                        # It can't belong to anything else, remove it.
#                del profile[func]
#                del highstate_profile[chunk]
            else:
                # Otherwise, we are at the last chunk.
                # All remaining calls should belong here.

                # Generate ordered dict from ordered keys
                ordered_profile_dict = salt.utils.odict.OrderedDict()
                delta_dict = salt.utils.odict.OrderedDict()

                for profile_key in ordered_profile_keys:
                    ordered_profile_dict[profile_key] = profile[profile_key]

                for func in ordered_profile_dict:
                    link_prev, link_next, key = ordered_profile_dict._OrderedDict__map[func]
                    try:
                        time_delta = (ordered_profile_dict[link_next[2]] * 1000) - (ordered_profile_dict[func] * 1000)
                        delta_dict[func] = '{0} ms'.format(time_delta)
                    except KeyError:
                        delta_dict[func] = 'Unknown'

                ret[chunk] = ordered_profile_dict
        if HAS_JSON:
            return json.dumps(ret, indent=4)
        else:
            return ret
