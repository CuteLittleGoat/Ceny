#!/usr/bin/env python3
from fetch_prices import parse_price
cases={
"2 269,34 zł":2269.34,
"2269,34 zł":2269.34,
"2.269,34 zł":2269.34,
"2269.34 PLN":2269.34,
"4 240,83 zł":4240.83,
"1810,89 zł":1810.89,
}
for k,v in cases.items():
    got=parse_price(k)
    assert got==v,f'{k}: {got} != {v}'
print('OK')
