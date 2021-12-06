

UNIFIED_SCOPES = ('inobi', 'admin', 'viewer', 'public')


INOBI = 'inobi'
DISABLED = 'disabled'

ANY = None


class ConstantGenerator(type):
    # This fix the problem of Transport ADMIN

    prefix = None
    _lower_values = True

    def __getattr__(self, item):
        prefix = self.prefix
        if not prefix:
            prefix = self.__name__.lower() + '_'
        scope = prefix + (item if not self._lower_values else item.lower())
        setattr(self, item, scope)
        return scope


class Project(metaclass=ConstantGenerator):
    CUSTOM = 'proj_custom'
    ANOTHER = 'proj_another'


class Transport(metaclass=ConstantGenerator):

    BOX = 'transport_unit'
    UNKNOWN_BOX = 'transport_unit(unknown)'
    OLD_TOKEN_BOX = 'transport_unit(old)'

    BOXES_V2 = [BOX, UNKNOWN_BOX]
    ANY_BOXES = [BOX, UNKNOWN_BOX, OLD_TOKEN_BOX]

    DRIVER = 'transport_driver'


class Advertisement(metaclass=ConstantGenerator):
    pass


class Application(metaclass=ConstantGenerator):
    SKIP = 'skip'
