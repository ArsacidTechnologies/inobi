from inobi import db
from .models import Device, Ad, Chronicle
from .devices import find_device


def register(device_mac: str, ad_id: str,
             redirected: bool, lat: float = None, lng: float = None,
             client_mac: str = None, client_device: str = None,
             events: str = None,
             test=False,
             ) -> Chronicle:

    ad = Ad.query.get(ad_id)

    ads_device_id = None
    ads_group_id = None

    device = find_device(device_id=device_mac)

    if device:
        ads_device_id = device.id
        ads_group_id = device.group_id

        lat, lng = device.lat, device.lng

        group = None

        while lat is None or lng is None:
            if group is None:
                group = device.group
            else:
                group = group.parent_group
            if group is None:
                lat, lng = 0, 0
                break
            else:
                lat, lng = group.lat, group.lng

    required_data = {"redirected": redirected, 'lat': lat, 'lng': lng}
    for i in required_data.keys():
        if required_data[i] is None:
            raise ValueError("`{}` parameter is not present.".format(i))

    chronicle = Chronicle(client_mac=client_mac, device=client_device,
                          box_mac=device_mac, ads_device_id=ads_device_id, ads_group_id=ads_group_id,
                          ad=ad, redirected=redirected,
                          lat=lat, lng=lng, _events=events,
                          )

    if test:
        return chronicle

    ad.views += 1

    db.session.add(ad)
    db.session.add(chronicle)

    db.session.commit()

    return chronicle

