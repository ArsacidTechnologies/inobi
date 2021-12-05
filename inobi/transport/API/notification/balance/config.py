from datetime import datetime

SUBJECT = 'Оповещение о низком балансе на сим-карте megacom'


def get_subject(ping):
    return SUBJECT


MESSAGE = '''
Здраствуйте!
Оповещаем вас о низком балансе: 
Номер: {phone}
Остаток: {balance} mb
Время: {time}
Просим пополнить баланс!

С уважением,
Команда Inobi
'''


def get_message(ping):
    return MESSAGE.format(
        phone=ping.get('device_phone', ping['device_id']),
        balance=ping.get('balance', '-'),
        time=datetime.fromtimestamp(ping['time']).strftime("%H:%M %d.%m.%Y")
    )

