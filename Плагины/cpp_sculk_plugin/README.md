# ⚙️ C++ Core Plugin — Endstone Sculk Epidemic

Высокопроизводительный нативный модуль для ядра сервера **Endstone** (Minecraft Bedrock Dedicated Server).

---

## 🚀 Преимущества C++ Модуля
- **Минимальный оверхед**: прямое взаимодействие с внутренними структурами сервера Endstone без задержек интерпретатора Python.
- **Быстрый расчёт дистанции**: эффективный алгоритм проверки расстояний между десятками игроков для механики воздушно-капельного заражения.
- **Точные хуки событий**: перехват `PlayerDeathEvent` и мгновенное размещение блоков `sculk_catalyst`.

---

## 🛠️ Сборка с помощью CMake

### Требования:
- Компилятор C++17/20: MSVC (Visual Studio 2022) на Windows или Clang/GCC на Linux.
- CMake версии 3.20 или новее.
- Заголовочные файлы и библиотека ядра Endstone C++ SDK.

### Шаги сборки (Windows):
```cmd
cd Плагины/cpp_sculk_plugin
mkdir build
cd build
cmake .. -A x64
cmake --build . --config Release
```

Собранная динамическая библиотека (`endstone_sculk_cpp.dll`) помещается в каталог `plugins/` на сервере Endstone.
