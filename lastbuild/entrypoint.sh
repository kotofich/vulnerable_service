#!/bin/bash

# Генерируем случайные строки для флагов (12 случайных символов)
USER_SUFFIX=$(head /dev/urandom | tr -dc A-Za-z0-9 | head -c 12)
ROOT_SUFFIX=$(head /dev/urandom | tr -dc A-Za-z0-9 | head -c 12)

# Записываем динамические флаги в файлы
echo "CTF{user_$USER_SUFFIX}" > /home/user/user.txt
echo "CTF{root_$ROOT_SUFFIX}" > /root/root.txt

# Устанавливаем правильные права, чтобы пользователь мог прочитать свой флаг
chown user:user /home/user/user.txt
chmod 644 /home/user/user.txt
chmod 600 /root/root.txt

# Выводим флаги в консоль докера (чтобы ты мог их увидеть через docker logs)
echo "------------------------------------------"
echo "DYNAMIC FLAGS GENERATED:"
echo "User Flag: CTF{user_$USER_SUFFIX}"
echo "Root Flag: CTF{root_$ROOT_SUFFIX}"
echo "------------------------------------------"

# Запускаем SSH сервис
service ssh start

# Запускаем Flask приложение от имени пользователя user
exec su user -c "python3 app.py"