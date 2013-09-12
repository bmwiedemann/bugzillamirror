#!/bin/sh
find mail/cur/ -type f | sort | xargs ./main.pl
