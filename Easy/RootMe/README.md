# RootMe - A ctf for beginners, can you root me? 

Складність: Easy

Ціль: 10.114.136.228

1. Розвідка (Reconnaissance & Enumeration)

    1.1. Сканування портів (Nmap):
     Запускаю nmap `nmap -sC -sV -O -p- -vv 10.114.136.228`.

      ![nmap](./img/nmap_scan.png)

    1.2. Веб-розвідка:

      Запускаю gobuster `gobuster dir -w /usr/share/wordlists/seclists/Discovery/Web-Content/common.txt  -u http://10.114.136.228 -t 50 -k -x html,txt,php`.

      ![gobuster](./img/gobuster_common.png)

      Перевіряю результати, звертаю увагу на `http://10.114.136.228/panel/` `http://10.114.136.228/uploads/`.

      ![HTML panel](./img/html_panel.png)

      ![HTML uploads](./img/html_uploads.png)

      Пробую завантажити файл для тесту. Як я і думав файл опинився в каталозі `/uploads/`. 

      ![HTML upload test](./img/html_test.png)

      Відповіді на питання `Task 2`.

      ![Answers task2](./img/task2.png)

2. Точка входу (Initial Access / Foothold)

    2.1. Експлуатація вразливості:

     Перше, про що подумав - це завантажити PHP реверс-шелл `PentestMonkey`. Але сервер видав помилку на PHP файл.

      ![php error](./img/php_error.png)

     Під час перегляду HTML коду я побачив, що використовуються js скрипти, тому знаходжу на `https://www.revshells.com/` реверс-шелл `node.js`.
     Завантажую його через панель та пробую затрігерити, попередньо запустивши слухач.

      ![nodejs reverse shell](./img/nodejs_rev_shell_1.png)

     Але не пішло.

      ![nodejs reverse shell](./img/nodejs_rev_shell_2.png)

     Пробую ще декілька варіантів, але вони не працюють, тому починаю гуглити, які є вразливості під час завантаження файлу. 

    2.2. Отримання реверс-шеллу:

     Перше посилання в гуглі `https://www.vaadata.com/blog/file-upload-vulnerabilities-and-security-best-practices/`, запрацював варіант зі зміною розширення на `.php5`.

      ![reverse shell 1](./img/php5_rev_shell_1.png)

    Запускаю та стабілізую реверс-шелл, забираю прапорт `user.txt`.

     ![reverse shell 2](./img/php5_rev_shell_2.png)

     ![user.txt](./img/user_txt.png)

3. Підвищення привілеїв (Privilege Escalation)

    3.1. Вертикальне підвищення (www-data -> Root):

      Переглядаючи програми з SUID доступом знаходжу `python2.7`.

      ![Python SUID](./img/python_suid.png)

      Йду на `https://gtfobins.org/gtfobins/python/` і бачу що маючи python з SUID я можу заспавнити root шелл або реверс-шелл. Отримую `root` та забираю прапор `root.txt`.

      ![root and root.txt](./img/root.png)  



