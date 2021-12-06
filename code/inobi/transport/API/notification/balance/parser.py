import re


class ParseError(Exception):
    ...


def parse(raw: str):
    if isinstance(raw, (int, float)):
        return raw
    for parser in [megacom_parser]:
        try:
            result = parser(raw)
        except ParseError as e:
            pass
        else:
            return result
    return None


def megacom_parser(raw: str) -> float:
    m = re.search('Lego: (?P<amount>\d+.?\d+) (?P<metric>\w+)', raw, re.IGNORECASE)
    if not m:
        raise ParseError('not found')
    amount, metric = m.group('amount', 'metric')
    return float(amount)
