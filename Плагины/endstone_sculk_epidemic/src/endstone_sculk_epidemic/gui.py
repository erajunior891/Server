"""
Графический интерфейс Bedrock Forms для плагина Скалковой Эпидемии.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from endstone.form import ActionForm, Button, MessageForm
from .lore import LORE_BOOKS

if TYPE_CHECKING:
    from endstone import Player, Server
    from .manager import EpidemicManager


def open_main_menu(player: Player, manager: EpidemicManager, server: Server) -> None:
    form = ActionForm(title="§3§lСКАЛКОВАЯ ЭПИДЕМИЯ§r")

    infected = manager.is_infected(player)
    stage = manager.get_stage(player)
    immunity_left = int(manager.get_immunity_time_left(player))
    relief_left = int(manager.get_relief_time_left(player))

    content = []
    if infected:
        content.append(f"§4⚠ ВНИМАНИЕ: Вы заражены! (Этап {stage} из 4)§r")
        stage_names = {
            0: "§80: Скрытая инкубация (без симптомов)§r",
            1: "§e1: Голод и Замедление§r",
            2: "§62: Слабость, Голод, Замедление, Внезапная Тьма§r",
            3: "§c3: Заразный носитель! Убийства сеют скалк§r",
            4: "§44: Критическая агония! Риск стать катализатором§r"
        }
        content.append(f"Текущая фаза: {stage_names.get(stage, 'Неизвестно')}")
        if relief_left > 0:
            content.append(f"§aОблегчение от битвы: еще {relief_left} сек§r")
    else:
        content.append("§aСостояние организма: ЗДОРОВ§r")
        if immunity_left > 0:
            content.append(f"§bАктивен иммунитет: {immunity_left} сек§r")

    content.append("\n§7Выберите интересующий раздел:§r")
    form.content = "\n".join(content)

    form.add_button(
        "§l🩺 Диагностика тела",
        on_click=lambda p: open_diagnostics(p, manager, server)
    )
    form.add_button(
        "§l📖 Библиотека Лора (Книги)",
        on_click=lambda p: open_lore_menu(p, manager, server)
    )
    form.add_button(
        "§l🧪 Рецепты Исцеления",
        on_click=lambda p: open_recipes_menu(p, manager, server)
    )

    if player.is_op:
        form.add_button(
            "§c§l⚙ Панель Администратора",
            on_click=lambda p: open_admin_menu(p, manager, server)
        )

    player.send_form(form)


def open_diagnostics(player: Player, manager: EpidemicManager, server: Server) -> None:
    form = ActionForm(title="§3§lМедицинская Диагностика§r")
    data = manager.get_player_data(str(player.unique_id))
    infected = data.get("is_infected", False)
    stage = data.get("stage", 0)

    lines = ["§f=== СОСТОЯНИЕ ПАЦИЕНТА: " + player.name + " ===§r\n"]
    if infected:
        lines.append(f"§cСтатус: §4ЗАРАЖЕН СКАЛКОВЫМИ СПОРАМИ§r")
        lines.append(f"§cТекущий этап чумы: §f{stage} / 4§r")
        time_in_stage = int(time.time() - data.get("stage_started_at", time.time()))
        lines.append(f"§7В текущей стадии: §f{time_in_stage} сек§r")
        relief = int(manager.get_relief_time_left(player))
        lines.append(f"§7Облегчение симптомов: §a{relief} сек§r")
        lines.append(f"§7Убийств сущностей для сдерживания: §f{data.get('kills_count', 0)}§r")
        lines.append("\n§eРекомендация врача:§r Примите Вакцину (этапы 0-3) или Панацею (этап 4)!")
    else:
        lines.append("§aСтатус: §2ИНФЕКЦИЯ НЕ ОБНАРУЖЕНА§r")
        imm = int(manager.get_immunity_time_left(player))
        if imm > 0:
            lines.append(f"§bЗащитный барьер (Иммунитет): §f{imm} сек§r")
        lines.append(f"§7Успешных исцелений в прошлом: §f{data.get('cured_times', 0)}§r")
        lines.append("\n§aРекомендация:§r Избегайте прямого контакта со скалком без защиты.")

    form.content = "\n".join(lines)
    form.add_button("« Назад", on_click=lambda p: open_main_menu(p, manager, server))
    player.send_form(form)


def open_recipes_menu(player: Player, manager: EpidemicManager, server: Server) -> None:
    form = ActionForm(title="§3§lРецепты Исцеления§r")
    text = (
        "§6§l1. ВАКЦИНА ОТ СКАЛКОВОЙ ЧУМЫ§r\n"
        "§fЭффект:§r Полное снятие чумы (0-3 этапы) + 30 минут иммунитета.\n"
        "§fИнгредиенты (верстак):§r\n"
        " • §bЗелье Слабости§r (ослабляет скалковые колонии)\n"
        " • §3Осколок Эха§r (резонансом очищает ткани)\n\n"
        "§a§l2. ПАНАЦЕЯ ДРЕВНИХ§r\n"
        "§fЭффект:§r Мгновенное спасение от 4 стадии (агонии), регенерация и насыщение.\n"
        "§fИнгредиенты (верстак):§r\n"
        " • §2Зелье Черепашьей Мощи§r\n"
        " • §cЗелье Исцеления§r\n\n"
        "§e§l3. ВРЕМЕННОЕ СДЕРЖИВАНИЕ§r\n"
        "§fУбийство любых враждебных сущностей сжигает адреналином споры в крови "
        "и приостанавливает симптомы чумы на 90 секунд!"
    )
    form.content = text
    form.add_button("« Назад", on_click=lambda p: open_main_menu(p, manager, server))
    player.send_form(form)


def open_lore_menu(player: Player, manager: EpidemicManager, server: Server) -> None:
    form = ActionForm(title="§3§lБиблиотека Сервера§r")
    form.content = "§7Выберите древний фолиант для чтения:§r"

    form.add_button(
        "§3§l1. Фолиант: Скалковая Чума",
        on_click=lambda p: open_book(p, "plague", 0, manager, server)
    )
    form.add_button(
        "§4§l2. Хроника: Великое Наказание",
        on_click=lambda p: open_book(p, "punishment", 0, manager, server)
    )
    form.add_button(
        "§e§l3. Дневник Сэра Пиглинуса",
        on_click=lambda p: open_book(p, "piglin", 0, manager, server)
    )
    form.add_button("« Назад в меню", on_click=lambda p: open_main_menu(p, manager, server))
    player.send_form(form)


def open_book(player: Player, book_key: str, page_idx: int, manager: EpidemicManager, server: Server) -> None:
    book = LORE_BOOKS.get(book_key)
    if not book:
        return

    pages = book["pages"]
    page_idx = max(0, min(len(pages) - 1, page_idx))

    form = ActionForm(title=f"§l{book['title']}§r")
    form.content = f"§8[Страница {page_idx + 1} из {len(pages)}] - Автор: {book['author']}§r\n\n" + pages[page_idx]

    if page_idx < len(pages) - 1:
        form.add_button(
            "Следующая страница »",
            on_click=lambda p: open_book(p, book_key, page_idx + 1, manager, server)
        )
    if page_idx > 0:
        form.add_button(
            "« Предыдущая страница",
            on_click=lambda p: open_book(p, book_key, page_idx - 1, manager, server)
        )
    form.add_button("« К списку книг", on_click=lambda p: open_lore_menu(p, manager, server))
    player.send_form(form)


def open_admin_menu(player: Player, manager: EpidemicManager, server: Server) -> None:
    if not player.is_op:
        player.send_tip("§cУ вас нет прав администратора!")
        return

    form = ActionForm(title="§c§lПанель Администратора Эпидемии§r")
    form.content = "§7Управление распространением чумы и этапами:§r"

    form.add_button("§4[Админ] Заразить себя (Этап 0)", on_click=lambda p: _admin_infect(p, manager, server, 0))
    form.add_button("§c[Админ] Установить себе Этап 1", on_click=lambda p: _admin_set_stage(p, manager, server, 1))
    form.add_button("§c[Админ] Установить себе Этап 2", on_click=lambda p: _admin_set_stage(p, manager, server, 2))
    form.add_button("§4[Админ] Установить себе Этап 3 (Заразный)", on_click=lambda p: _admin_set_stage(p, manager, server, 3))
    form.add_button("§0[Админ] Установить себе Этап 4 (Критический)", on_click=lambda p: _admin_set_stage(p, manager, server, 4))
    form.add_button("§a[Админ] Мгновенно вылечить себя (Вакцина)", on_click=lambda p: _admin_cure(p, manager, server, False))
    form.add_button("§6[Админ] Мгновенно исцелить себя (Панацея)", on_click=lambda p: _admin_cure(p, manager, server, True))
    form.add_button("« Назад в главное меню", on_click=lambda p: open_main_menu(p, manager, server))

    player.send_form(form)


def _admin_infect(p: Player, manager: EpidemicManager, server: Server, stage: int) -> None:
    manager.infect(p, server, initial_stage=stage)
    p.send_tip(f"§a[Админ] Вы заражены этапом {stage}!")


def _admin_set_stage(p: Player, manager: EpidemicManager, server: Server, stage: int) -> None:
    manager.set_stage(p, stage, server)
    p.send_tip(f"§a[Админ] Этап изменен на {stage}!")


def _admin_cure(p: Player, manager: EpidemicManager, server: Server, is_panacea: bool) -> None:
    manager.cure(p, server, is_panacea=is_panacea)
    p.send_tip("§a[Админ] Вы полностью исцелены!")
