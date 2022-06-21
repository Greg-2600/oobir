#!/bin/bash

curl 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'|
grep -E '<td>[A-Z][A-Z][A-Z]'|
sed 's/<td>//g'|
sed 's/<\/td>//g'|
awk '{print $1}' > SYMBOLS.list