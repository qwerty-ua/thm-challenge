
# LazyAdmin - Easy linux machine to practice your skills

Складність: Easy

Ціль: 10.113.166.242

1. Розвідка (Reconnaissance & Enumeration)

    1.1. Сканування портів (Nmap):

      `nmap -sC -sV -O -p- -vv 10.113.166.242`

      ![nmap](./img/nmap_scan.png)

    1.2. Веб-розвідка:

      Бачу сторінку `Apache2`, в коді коментім або якихось данних не має.
    
      ![main page](./img/html.png)

      Запускаю `gobuster` з словником `common.txt`.

   `gobuster dir -w /usr/share/wordlists/seclists/Discovery/Web-Content/common.txt  -u http://10.113.166.242 -t 50 -k -x html,txt,php`
   
      ![gobuster](./img/gobuster_common.png)

      Запускаю скан ще раз для `/content/`.

      ![gobuster /content/](./img/gobuster_html_content.png)

      Переглядаю результати. 

      ![SweetRice1](./img/sweetrice.png)

      ![SweetRice2](./img/sweetrice_2.png)

      ![changelog](./img/sweetrice_changelog_txt.png)

      ![mysql backup](./img/mysql_backup.png)

      Починаю гуглити про SweetRice 1.5.1, знаходжу. Після цього ще дивлюсь вміст завантаженого бекапу та знаходжу користувача `manager` та його хеш.

      ![exploit-db](./img/exploit-db.png)

      ![credential](./img/mysql_backup_creds.png)
   
      ![manager pass](./img/manager_pass.png)   
    
3. Точка входу (Initial Access / Foothold)

    2.1. Експлуатація вразливості:

      Для початку, перевіряю отриманий логін та пароль.
          
      ![login](./img/login_pass_check.png)

      Поглянувши тут https://www.exploit-db.com/exploits/40700 , бачу `# In SweetRice CMS Panel In Adding Ads Section SweetRice Allow To Admin Add PHP Codes In Ads File`. Тому закидую код реверс-шеллу `PentestMonkey`.

      ![ads_reverse_shell](./img/ads_rev_shell.png)


   2.2. Отримання реверс-шеллу:

      Знаходжу завантажений файл, піднімаю реверс-шелл та стабілізую його.

      ![reverse shell 1](./img/rev_shell_1.png)

      ![reverse shell 2](./img/rev_shell_2.png)

4. Підвищення привілеїв (Privilege Escalation)

    3.1. Вертикальне підвищення (www-data -> Root):

     Перевіряю `sudo -l`, бачу виконання скрипта без пароля з правами `root`. Закидаю свій реверс-шелл та запускаю.

     ![root1](./img/root_scripts_1.png)

     ![root2](./img/root_scripts_2.png)

     Забираю прапори `user.txt` та `root.txt`.

     ![root.txt,user.txt](./img/root_user_txt.png)
