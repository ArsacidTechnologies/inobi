#!/usr/bin/env bash


if [ ! -d migrations ]; then flask db init && flask db migrate -m 'Initialized' && flask db upgrade && python3 runhooks.py --migrations; fi