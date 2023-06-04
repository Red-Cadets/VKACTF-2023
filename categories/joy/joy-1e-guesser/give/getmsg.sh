#!/bin/bash
set -ef -o pipefail

echo "Угадайте число и выиграйте флаг!"
(( winning_number=`shuf -i 1-18446744073709551615 -n 1` ))

read num    
if [[ $num -eq $winning_number ]]
then
 cat flag.txt
else
 echo "Не повезло"
fi
