

import unittest

from inobi import utils


class AsDictMixinTestCase(unittest.TestCase):

    class Kek(utils.AsDictMixin):

        _asdict_fields = 'lat lng->lng lel>lel _xd:xd'.split()

        lat = lng = None
        lel, xd = 1, 2

        @property
        def _xd(self):
            return self.xd

    def setUp(self):
        self.kek = self.Kek()

    def test_asdict_method(self):
        d = self.kek.asdict()
        self.assertEqual(d, {'lat': None, 'lng': None, 'lel': 1, 'xd': 2})


class UpdateMixinTestCase(unittest.TestCase):

    class Mock(utils.UpdateMixin):

        _update_fields = 'a:_a b c'.split()

        def __init__(self, a, b, c, d):
            self.a, self.b, self.c, self.d = a, b, c, d

        @property
        def _a(self):
            return self.a

        @_a.setter
        def _a(self, value):
            self.a = value*2

    def test_update_method(self):
        o = self.Mock(a=1, b=2, c=3, d=4)
        u = o.update(dict(a=321, c='321', d=321))
        self.assertEqual(o.a, 642)
        self.assertEqual(o.c, '321')
        self.assertEqual(o.d, 4)
        self.assertEqual(u, True)
        u = o.update(dict(d=0))
        self.assertEqual(u, False)
