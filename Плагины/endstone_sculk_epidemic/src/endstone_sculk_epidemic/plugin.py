"""
Главный модуль плагина Endstone: Скалковая Эпидемия.
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from endstone import Player
from endstone.command import Command, CommandSender
from endstone.event import (
    ActorDeathEvent,
    BlockBreakEvent,
    PlayerDeathEvent,
    PlayerInteractEvent,
    PlayerItemConsumeEvent,
    PlayerJoinEvent,
    PlayerMoveEvent,
    PlayerQuitEvent,
    event_handler,
)
from endstone.plugin import Plugin

from .gui import open_book, open_main_menu, open_recipes_menu
from .manager import EpidemicManager

if TYPE_CHECKING:
    from endstone.block import Block


class SculkEpidemicPlugin(Plugin):
    api_version = "0.11"

    commands = {
        "sculk": {
            "description": "Главное меню и статус Скалковой Эпидемии",
            "usages": ["/sculk [info|lore|recipe]"],
            "permissions": ["sculk.command.use"],
        },
        "sculkadmin": {
            "description": "Административное управление Скалковой Чумой",
            "usages": ["/sculkadmin <infect|cure|stage|spread> [player] [stage]"],
            "permissions": ["sculk.command.admin"],
        },
    }

    permissions = {
        "sculk.command.use": {
            "description": "Доступ к меню чумы /sculk",
            "default": "true",
        },
        "sculk.command.admin": {
            "description": "Администрирование чумы",
            "default": "op",
        },
    }

    def on_enable(self) -> None:
        self.data_folder.mkdir(parents=True, exist_ok=True)
        self.manager = EpidemicManager(str(self.data_folder), self.config)

        # Регистрация периодического тикера чумы (каждые 2.5 секунды = 50 тиков)
        self.server.scheduler.run_task(self, self._tick_task, delay=40, period=50)

        # Регистрация слушателей событий
        self.register_events(self)
        self.logger.info("§a[Sculk Epidemic] Плагин успешно включен! Лор и механики инициализированы.§r")

    def on_disable(self) -> None:
        if hasattr(self, "manager"):
            self.manager.save()
        self.logger.info("§e[Sculk Epidemic] Плагин выключен, данные сохранены.§r")

    def _tick_task(self) -> None:
        try:
            self.manager.tick_players(self.server)
        except Exception as e:
            self.logger.error(f"Ошибка в таске эпидемии: {e}")

    def on_command(self, sender: CommandSender, command: Command, args: list[str]) -> bool:
        cmd_name = command.name.lower()

        if cmd_name == "sculk":
            if not isinstance(sender, Player):
                sender.send_message("§cКоманда /sculk доступна только для игроков в игре.")
                return True

            if not args:
                open_main_menu(sender, self.manager, self.server)
                return True

            sub = args[0].lower()
            if sub == "recipe" or sub == "recipes":
                open_recipes_menu(sender, self.manager, self.server)
                return True
            elif sub == "lore":
                book_key = args[1].lower() if len(args) > 1 else "plague"
                open_book(sender, book_key, 0, self.manager, self.server)
                return True
            elif sub == "info":
                stage = self.manager.get_stage(sender)
                inf = self.manager.is_infected(sender)
                sender.send_message(f"§3[Чума] Заражен: {'§cДа' if inf else '§aНет'}§3, Этап: §f{stage}§3.")
                return True
            else:
                open_main_menu(sender, self.manager, self.server)
                return True

        elif cmd_name == "sculkadmin":
            if not sender.has_permission("sculk.command.admin"):
                sender.send_message("§cУ вас нет прав администратора для этой команды.")
                return True

            if not args:
                sender.send_message("§eИспользование: /sculkadmin <infect|cure|stage|spread> [игрок] [этап]")
                return True

            action = args[0].lower()
            target_name = args[1] if len(args) > 1 else (sender.name if isinstance(sender, Player) else None)
            target = self.server.get_player(target_name) if target_name else None

            if action == "infect":
                if not target:
                    sender.send_message(f"§cИгрок {target_name} не найден.")
                    return True
                stage = int(args[2]) if len(args) > 2 and args[2].isdigit() else 0
                self.manager.infect(target, self.server, initial_stage=stage)
                sender.send_message(f"§aИгрок {target.name} заражен этапом {stage}!")
                return True

            elif action == "cure":
                if not target:
                    sender.send_message(f"§cИгрок {target_name} не найден.")
                    return True
                is_panacea = (len(args) > 2 and args[2].lower() in ["panacea", "true", "all"])
                self.manager.cure(target, self.server, is_panacea=is_panacea)
                sender.send_message(f"§aИгрок {target.name} излечен! (Панацея: {is_panacea})")
                return True

            elif action == "stage":
                if not target:
                    sender.send_message(f"§cИгрок {target_name} не найден.")
                    return True
                if len(args) < 3 or not args[2].isdigit():
                    sender.send_message("§cУкажите этап от 0 до 4: /sculkadmin stage <игрок> <0-4>")
                    return True
                st = int(args[2])
                self.manager.set_stage(target, st, self.server)
                sender.send_message(f"§aИгроку {target.name} установлен этап {st}!")
                return True

            elif action == "spread":
                count = 0
                for p in self.server.online_players:
                    if self.manager.infect(p, self.server, initial_stage=0):
                        count += 1
                sender.send_message(f"§aВолна эпидемии заразила {count} игроков!")
                return True

        return False

    @event_handler
    def on_player_move(self, event: PlayerMoveEvent) -> None:
        """Проверка контакта со скалк-блоками для первичного заражения (Этап 0)."""
        player = event.player
        if self.manager.is_infected(player):
            return

        # Проверяем блок под ногами игрока
        loc = event.to_location
        try:
            curr_block: Block = loc.block
            under_block: Block = curr_block.get_relative(0, -1, 0)
        except Exception:
            return

        # Если игрок наступил на скалк
        sculk_types = [
            "minecraft:sculk",
            "minecraft:sculk_vein",
            "minecraft:sculk_catalyst",
            "minecraft:sculk_shrieker",
            "minecraft:sculk_sensor",
        ]

        if curr_block.type in sculk_types or under_block.type in sculk_types:
            chance = int(self.manager.config.get("sculk_contact_infection_chance", 8))
            if random.randint(1, 100) <= chance:
                self.manager.infect(player, self.server, initial_stage=0)

    @event_handler
    def on_player_interact(self, event: PlayerInteractEvent) -> None:
        """Открытие интерфейса книг при нажатии ПКМ с книгой лора в руке."""
        if not event.has_item or not event.item:
            return

        item_id = str(event.item.type.id)
        player = event.player

        if item_id == "sculk:lore_book_plague":
            open_book(player, "plague", 0, self.manager, self.server)
            event.cancel()
        elif item_id == "sculk:lore_book_punishment":
            open_book(player, "punishment", 0, self.manager, self.server)
            event.cancel()
        elif item_id == "sculk:lore_book_piglin":
            open_book(player, "piglin", 0, self.manager, self.server)
            event.cancel()

    @event_handler
    def on_player_item_consume(self, event: PlayerItemConsumeEvent) -> None:
        """Обработка применения Вакцины и Панацеи."""
        if not event.item:
            return

        item_id = str(event.item.type.id)
        player = event.player

        if item_id == "sculk:sculk_vaccine":
            self.manager.cure(player, self.server, is_panacea=False)
        elif item_id == "sculk:sculk_panacea":
            self.manager.cure(player, self.server, is_panacea=True)

    @event_handler
    def on_actor_death(self, event: ActorDeathEvent) -> None:
        """
        Убийство сущностей:
        1. Временное облегчение симптомов чумы (по лору).
        2. На 3 этапе убийства распространяют скалк под ногами!
        """
        killer = None
        ds = event.damage_source
        if ds and ds.actor and isinstance(ds.actor, Player):
            killer = ds.actor
        elif ds and ds.damaging_actor and isinstance(ds.damaging_actor, Player):
            killer = ds.damaging_actor

        if not killer:
            return

        # 1. Снятие симптомов
        self.manager.record_kill(killer, self.server)

        # 2. На 3 этапе убийства распространяют Скалк
        if self.manager.get_stage(killer) == 3:
            loc = event.actor.location
            x, y, z = int(loc.x), int(loc.y), int(loc.z)
            self.server.dispatch_command(
                self.server.command_sender,
                f"setblock {x} {y} {z} sculk keep"
            )
            # Распространение скалковых жил вокруг
            for dx, dz in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                self.server.dispatch_command(
                    self.server.command_sender,
                    f"setblock {x+dx} {y} {z+dz} sculk_vein keep"
                )
            self.server.dispatch_command(
                self.server.command_sender,
                f"playsound block.sculk.spread @a {x} {y} {z} 0.8 1.0"
            )

    @event_handler
    def on_player_death(self, event: PlayerDeathEvent) -> None:
        """
        4 Этап: При смерти от симптомов появляется Скалковый катализатор (по лору)!
        """
        player = event.player
        if self.manager.is_infected(player) and self.manager.get_stage(player) == 4:
            loc = player.location
            x, y, z = int(loc.x), int(loc.y), int(loc.z)
            self.server.dispatch_command(
                self.server.command_sender,
                f"setblock {x} {y} {z} sculk_catalyst replace"
            )
            self.server.dispatch_command(
                self.server.command_sender,
                f"playsound mob.warden.death @a {x} {y} {z} 1.0 0.7"
            )
            self.server.broadcast_message(
                f"§4[Эпидемия] §cИгрок {player.name} пал жертвой 4 этапа Скалковой Чумы! "
                f"На месте его гибели пророс Скалковый катализатор!"
            )
            # Сбрасываем чуму после перерождения
            self.manager.cure(player, self.server, is_panacea=False)

    @event_handler
    def on_player_join(self, event: PlayerJoinEvent) -> None:
        player = event.player
        if self.manager.is_infected(player):
            stage = self.manager.get_stage(player)
            player.send_tip(f"§4⚠ Вы заражены Скалковой Чумой (Этап {stage})! Напишите /sculk для меню.")
        else:
            player.send_tip("§3[Сервер] Напишите /sculk, чтобы изучить древний лор и рецепты.")

    @event_handler
    def on_player_quit(self, event: PlayerQuitEvent) -> None:
        if hasattr(self, "manager"):
            self.manager.save()
