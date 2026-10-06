[app]

# Название твоего приложения
title = My App

# Имя пакета (без пробелов и спецсимволов)
package.name = myapp

# Домен приложения
package.domain = org.test

# Где лежит исходный код (. — это текущая папка)
source.dir = .

# Расширения файлов, которые нужно включить в APK
source.include_exts = py,png,jpg,kv,atlas

# Версия приложения
version = 0.1

# Библиотеки, необходимые для работы (добавь через запятую, если нужны другие)
requirements = python3,kivy

# Ориентация экрана (portrait или landscape)
orientation = portrait

# Автоматически принимать лицензию Android SDK
android.accept_sdk_license = True

# Версии Android API
android.api = 33
android.minapi = 21

[buildozer]

# Уровень логов (2 — подробный вывод)
log_level = 2
warn_on_root = 1
