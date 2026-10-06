[app]

# Название твоего приложения
title = Bounce It Out

# Имя пакета (без пробелов)
package.name = bounceitout

# Домен приложения
package.domain = org.test

# Где лежит исходный код (. — текущая папка)
source.dir = .

# Расширения файлов, которые нужно включить в APK
source.include_exts = py,png,jpg,kv,atlas,wav,mp3

# Версия приложения
version = 0.1

# Библиотеки, необходимые для работы
requirements = python3,kivy

# Ориентация экрана
orientation = portrait

# Автоматически принимать лицензию Android SDK
android.accept_sdk_license = True

# Настройки Android API
android.api = 33
android.minapi = 21

# Фиксируем стабильную версию NDK
android.ndk = 25b

# Собираем под 64-битные современные процессоры (устраняет ошибку)
android.archs = arm64-v8a

[buildozer]

# Уровень логов
log_level = 2
warn_on_root = 1
