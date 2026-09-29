
# Phantom Fob - The fob locks but won’t unlock. Codes change every second, forge the signal; don’t replay it.

Складність: Medium  

Ціль: 10.114.131.219

## 1. Розвідка (Reconnaissance & Enumeration)

### 1.1. Сканування портів (Nmap):
   ```bash
   └─$ sudo nmap -sC -sV -p- -vv -oN nmap_result.txt 10.114.131.219
   ```

(nmap)[./img/nmap.png]

```text
nc 10.114.131.219 29536

<open can0>
<rawmode>

результа пакети типу

< frame 0B4 1790716653.557371 03d302dd8ece0367 >

03 d3 02 dd 8e ce 03 67

< frame CAN_ID TIMESTAMP PAYLOAD>

 nc 10.114.131.219 29536 > data.raw        -- пакети без натискання кнопок
 nc 10.114.131.219 29536 > lock-data.raw   -- натискання кнопки "lock" 5 разів
 nc 10.114.131.219 29536 > horn-data.raw   -- натискання кнопки "horn" 5 разів
 nc 10.114.131.219 29536 > arm-data.raw    -- натискання кнопки "arm" 5 разів
 nc 10.114.131.219 29536 > disarm-data.raw -- натискання кнопки "disarm" 5 разів
 nc 10.114.131.219 29536 > concurrently-data.raw -- записуємо в дамп результат команд нижче
 команди:
 
curl -sS -X POST http://10.114.131.219:8080/press \
    -H 'Content-Type: application/json' \
    -d '{"button":"LOCK"}' &

curl -sS -X POST http://10.114.131.219:8080/press \
    -H 'Content-Type: application/json' \
    -d '{"button":"HORN"}' &

curl -sS -X POST http://10.114.131.219:8080/press \
    -H 'Content-Type: application/json' \
    -d '{"button":"IMMOB_ARM"}' &

curl -sS -X POST http://10.114.131.219:8080/press \
    -H 'Content-Type: application/json' \
    -d '{"button":"IMMOB_DISARM"}' &

wait
```

Скрипт для знайходження CAN_ID
```bash
for file in data concurrently-data lock-data horn-data arm-data disarm-data; do
   echo "$file"

   tr '<' '\n' < "$file.raw" |
   awk 'toupper($1)=="FRAME" {
       count[toupper($2)]++
   }
   END {
       for (id in count)
           print count[id], id
   }' |
    sort -n
done
```

Результат:
```text
data
9 335
34 245
34 447
66 561
66 6D3
135 171
135 329
322 1B9
645 0B4
concurrently-data
4 18A
6 335
20 245
20 447
39 561
39 6D3
80 171
80 329
190 1B9
381 0B4
lock-data
5 18A
22 335
76 245
76 447
149 561
149 6D3
304 171
304 329
726 1B9
1452 0B4
horn-data
5 18A
23 335
78 245
79 447
153 561
153 6D3
311 171
311 329
733 1B9
1464 0B4
arm-data
5 18A
26 335
91 245
92 447
179 561
179 6D3
364 171
364 329
869 1B9
1737 0B4
disarm-data
5 18A
21 335
74 245
76 447
146 561
146 6D3
299 171
299 329
716 1B9
1432 0B4
```
З чого видно, що `18A` - CAN_ID відповідає за натискання кнопок

Перенлядаю вміст пакетів `18A` за допомогою скрипта
```bash
for file in data concurrently-data lock-data horn-data arm-data disarm-data; do
   echo "$file"

   tr '<' '\n' < "$file.raw" |
   awk 'toupper($1)=="FRAME" &&
        toupper($2)=="18A" {
        print toupper($4)
   }' |
   sed -E 's/(..)/\1 /g'
done
```

Результат:
```text
data
concurrently-data
2C 7F 20 F3 84 39 40 43 
2C 7F 20 CF 84 39 1B 44 
2C 7F 20 21 84 39 6C 45 
2C 7F 20 1D 84 39 67 46 
lock-data
2C 7F DF 15 84 B0 40 2F 
2C 7F B7 E3 84 A5 40 30 
2C 7F 7C 48 84 44 40 31 
2C 7F F1 36 84 BC 40 32 
2C 7F 93 56 84 39 40 33 
horn-data
2C 7F E5 08 84 BD 1B 34 
2C 7F EF 2F 84 D9 1B 35 
2C 7F 08 FB 84 8B 1B 36 
2C 7F B6 96 84 77 1B 37 
2C 7F 2D 38 84 A1 1B 38 
arm-data
2C 7F 16 2F 84 5D 6C 39 
2C 7F 51 AB 84 9D 6C 3A 
2C 7F 67 E2 84 BD 6C 3B 
2C 7F BF F3 84 75 6C 3C 
2C 7F C0 8C 84 0C 6C 3D 
disarm-data
2C 7F 6D 06 84 DD 67 3E 
2C 7F 0B 13 84 4B 67 3F 
2C 7F 91 32 84 E3 67 40 
2C 7F B5 43 84 CF 67 41 
2C 7F A8 E8 84 80 67 42 
```

Ананліз байтів у фреймі 
```text
b0  2C
b1  7F
b2  фіксується коли швидко відправляємо команди кнопки
b3  контрольна сума
b4  84
b5  фіксується коли швидко відправляємо команди кнопки
b6  повторюється але для кожної кнопки різний
b7  Схоже на  лічильник, який після натискання кнопки дає id +1

2C 7F 20 F3 84 39 40 43 -- lock
2C 7F 20 CF 84 39 1B 44 -- horn
2C 7F 20 21 84 39 6C 45 -- IMMOB_ARM
2C 7F 20 1D 84 39 67 46 -- IMMOB_disARM
```

Із проходження іншого чудака https://www.youtube.com/watch?v=hpM84hdaH4k, він каже для вирахування контрольної суми може бути XOR з константою або додавання з константою.
По XOR я щось не дуже в'їхав, то почав спочатку з додавання:

2C 7F 20 F3 84 39 40 43 -- lock
1. 2C + 7F + 20 + 84 + 39 + 40 + 43 = 20B
2. 20B mod 100 = B
Тоді F3 - B = E8

2C 7F 20 CF 84 39 1B 44
1. 2C +7F +20 + 84 +39+ 1B+ 44 = 1E7 = E7
2. CF - E7 = -18
3. -18 mod 100 = E8

Тому припускаю що у мене додавання.

Також я взяв у нього пайтон скрипти і переробив під себе.

