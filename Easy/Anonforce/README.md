# Anonforce - boot2root machine for FIT and bsides guatemala CTF

Складність: Easy

Ціль: 10.112.167.145

1. Розвідка (Reconnaissance & Enumeration)

    1.1. Сканування портів (Nmap):

     `nmap -sC -sV -O -p- -vv 10.112.167.145`

      ![nmap](./img/nmap_scan.png)
   
    1.2. FTP:

      Знаходжу зашифрований файл та ключ, забираю собі.

      ![dir /notread](./img/notread.png)

      Також дивлюсь домашні директорії користувачів.

      ![dir /home](./img/ftp_home.png)

      Знаходжу прапор `user.txt`.

      ![user.txt](./img/user_txt.png)

   
3. Отримання доступу

      Пробую глянути що це за файл та ключ, але треба пароль.

      ![passphrase error](./img/gpg_error.png)

      Дістаю хеш, та за допомогою `john` дізнаюсь пароль.

      ![passphrase brute](./img/hash_txt_1.png) 

      ![passphrase](./img/john.png)

      Імпортую ключ та дивлюсь вміст зашифрованого файлу.

      ![backup.pgp](./img/backup_pgp.png)

      Беру з попереднього файлу хеш `root`-а та знову використовую `john`.

      ![roothash brute](./img/root_hash.png)

      Підключаюсь по SSH та забираю прапор `root.txt`.

      ![root.txt](./img/root_txt.png)
