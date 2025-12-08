# Инструкция по клонированию репозитория в Cursor

## Шаг 1: Клонируйте репозиторий

### Вариант 1: Через Cursor (Рекомендуется)

1. Откройте **Cursor** (десктопное приложение)
2. Нажмите **Ctrl+Shift+P** (или Cmd+Shift+P на Mac)
3. Введите: `Git: Clone`
4. Вставьте URL:
```
https://github.com/Edner68/ezois-rza-app.git
```
5. Выберите папку для сохранения (например, `C:\\Projects\\ezois-rza-app`)
6. Нажмите **Open** когда клонирование завершится

### Вариант 2: Через командную строку

```bash
# Перейдите в папку для проектов
cd C:\\Projects

# Клонируйте репозиторий
git clone https://github.com/Edner68/ezois-rza-app.git

# Перейдите в папку проекта
cd ezois-rza-app

# Откройте в Cursor
cursor .
```

---

## Проверьте структуру

После открытия в Cursor вы увидите:

```
ezois-rza-app/
├── app/
│   └── main.py
├── README.md
├── requirements.txt
└── CURSOR_SETUP.md (этот файл)
```

---

## Что дальше?

✅ **Шаг 1 выполнен!**

Теперь перейдите к **Шагу 2**: откройте файл `CURSOR_AGENT_TASK.md` и скопируйте задание для Cursor Agent.
