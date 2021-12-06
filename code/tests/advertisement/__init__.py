
import unittest


from inobi.advertisement.db import public, models, classes as old_models, devices, chronicles_v2
from inobi.city.models import City
from inobi import db


class AdvertisementTestCase(unittest.TestCase):

    def setUp(self):
        self.group = self.g = models.Group.query.first()
        self.device = self.d = models.Device.query.first()

    def test_advertisement_group_city(self):
        g = self.group
        c = g.city
        self.assertIsInstance(c, City)
        self.assertEqual(g.city_id, c.id)

    def test_advertisement_device_city(self):
        d = self.device
        c = d.city
        self.assertIsInstance(c, City)
        self.assertEqual(d.city_id, c.id)

    def test_city_of_advertisement_asdictable(self):
        c = self.group.city
        self.assertIsInstance(c.asdict(), dict)

    def test_create_group(self):
        g = devices.create_group('kekeke', city_id='1', parent_group_id=None,
                                 location={"lat": 42.87810263697499, "lng": 74.57038879394533},
                                 )
        self.assertIsInstance(g.id, int)
        devices.delete_group(g)

    def test_register_chronicles_v2(self):
        ad = models.Ad.query.first()
        prev_views = ad.views
        ch = chronicles_v2.register(self.device, ad.id, False)
        self.assertEqual(ch.ad_id, ad.id)
        self.assertEqual(prev_views+1, ad.views)


class AdvertisementOldTestCase(unittest.TestCase):

    def test_get_random_ad_not_fails(self):
        ad = public.get_random_ad()
        self.assertIsInstance(ad, old_models.Ad)

    def test_registration_of_chronicle_not_fails(self):
        ch = old_models.Chronicle.construct('kekmeklelxd',
                                            '8dbbb369-3df1-4039-80d4-47bd1f5f2389',
                                            0, 0, False, [],
                                            None, None)
        self.assertIsNotNone(ch)
        ch = public.register_client_chronicles(ch)
        self.assertIsInstance(ch, old_models.Chronicle)
