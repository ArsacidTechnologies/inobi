from copy import deepcopy


def dump_ping(ping):
    dump = deepcopy(ping)
    if 'organizations' in dump:
        dump.pop('organizations')
    return dump
