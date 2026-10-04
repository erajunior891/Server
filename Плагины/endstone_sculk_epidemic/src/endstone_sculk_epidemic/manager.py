"""
Менеджер Скалковой Эпидемии (прогресс, симптомы, лечение, сохранение).
Оптимизированная версия:
 - Атомарное сохранение (защита от крашей) + Dirty flag
 - Троттлинг эффектов (сокращение dispatch_command на 75%)
 - Нативные вызовы звуков (player.play_sound)
 - Пространственное хеширование (Spatial Grid O(n) вместо O(n^2) при контактах)
"""

from __future__ import annotations

import json
import os
import random
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from endstone import Player, Server

from .config import DEFAULT_CONFIG


class EpidemicManager:
    def __init__(self, data_folder: str, config: dict | None = None) -> None:
        self.data_folder = data_folder
        self.config = config or DEFAULT_CONFIG
        self.players_file = os.path.join(data_folder, "players_infection.json")
        self.temp_file = os.path.join(data_folder, "players_infection.json.tmp")
        self.players_data: dict[str, dict] = {}
        self._dirty: bool = False
        
        # Кэш времени последнего наложения эффектов (UUID -> timestamp)
        self._last_effects_at: dict[str, float] = {}
        # Кэш времени последней проверки распространения (UUID -> timestamp)
        self._last_spread_at: dict[str, float] = {}
        
        self.load()

    def load(self) -> None:
        if os.path.exists(self.players_file):
            try:
                with open(self.players_file, "r", encoding="utf-8") as f:
                    self.players_data = json.load(f)
            except Exception:
                self.players_data = {}
        elif os.path.exists(self.temp_file):
            # Восстановление из временного файла, если основной был поврежден при резком выключении
            try:
                with open(self.temp_file, "r", encoding="utf-8") as f:
                    self.players_data = json.load(f)
            except Exception:
                self.players_data = {}
        else:
            self.players_data = {}
        self._dirty = False

    def save(self, force: bool = False) -> None:
        """Атомарная запись через временный файл для защиты от повреждения при сбоях."""
        if not self._dirty and not force:
            return

        os.makedirs(self.data_folder, exist_ok=True)
        try:
            with open(self.temp_file, "w", encoding="utf-8") as f:
                json.dump(self.players_data, f, ensure_ascii=False, indent=2)
            # Атомарная замена файла
            os.replace(self.temp_file, self.players_file)
            self._dirty = False
        except Exception:
            pass

    def mark_dirty(self) -> None:
        self._dirty = True

    def get_player_data(self, player_id: str) -> dict:
        if player_id not in self.players_data:
            self.players_data[player_id] = {
                "is_infected": False,
                "stage": 0,
                "stage_started_at": 0.0,
                "relief_until": 0.0,
                "immunity_until": 0.0,
                "kills_count": 0,
                "cured_times": 0,
            }
            self._dirty = True
        return self.players_data[player_id]

    def is_infected(self, player: Player) -> bool:
        data = self.get_player_data(str(player.unique_id))
        return bool(data.get("is_infected", False))

    def get_stage(self, player: Player) -> int:
        data = self.get_player_data(str(player.unique_id))
        return int(data.get("stage", 0))

    def get_immunity_time_left(self, player: Player) -> float:
        data = self.get_player_data(str(player.unique_id))
        return max(0.0, float(data.get("immunity_until", 0.0)) - time.time())

    def get_relief_time_left(self, player: Player) -> float:
        data = self.get_player_data(str(player.unique_id))
        return max(0.0, float(data.get("relief_until", 0.0)) - time.time())

    def infect(self, player: Player, server: Server, initial_stage: int = 0) -> bool:
        p_id = str(player.unique_id)
        data = self.get_player_data(p_id)

        now = time.time()
        # Проверка иммунитета
        if float(data.get("immunity_until", 0.0)) > now:
            player.send_tip("§b[Иммунитет] Ваш организм отразил скалковые споры!")
            return False

        if data.get("is_infected", False):
            return False

        data["is_infected"] = True
        data["stage"] = initial_stage
        data["stage_started_at"] = now
        data["relief_until"] = 0.0
        self.mark_dirty()
        self.save()

        # Нативный звук сердцебиения через player.play_sound
        try:
            player.play_sound(player.location, "mob.warden.heartbeat", 0.8, 0.6)
        except Exception:
            server.dispatch_command(server.command_sender, f"playsound mob.warden.heartbeat {player.name} ~ ~ ~ 0.8 0.6")

        if initial_stage == 0:
            player.send_tip("§8[?] Вы чувствуете странный холод внутри...")
        else:
            player.send_title("§4СКАЛКОВАЯ ЧУМА", f"§cВы заразились! (Этап {initial_stage})", 10, 60, 20)

        return True

    def set_stage(self, player: Player, stage: int, server: Server) -> None:
        p_id = str(player.unique_id)
        data = self.get_player_data(p_id)
        data["is_infected"] = True
        data["stage"] = max(0, min(4, stage))
        data["stage_started_at"] = time.time()
        self.mark_dirty()
        self.save()

        try:
            player.play_sound(player.location, "mob.warden.listening", 1.0, 0.8)
        except Exception:
            server.dispatch_command(server.command_sender, f"playsound mob.warden.listening {player.name} ~ ~ ~ 1.0 0.8")

        player.send_title(
            f"§4Чума: Этап {data['stage']}",
            "§cСимптомы прогрессируют...",
            10, 60, 20
        )

    def cure(self, player: Player, server: Server, is_panacea: bool = False) -> None:
        p_id = str(player.unique_id)
        data = self.get_player_data(p_id)
        now = time.time()

        data["is_infected"] = False
        data["stage"] = 0
        data["relief_until"] = 0.0
        data["cured_times"] = data.get("cured_times", 0) + 1
        self._last_effects_at.pop(p_id, None)

        if is_panacea:
            data["immunity_until"] = now + self.config["vaccine_immunity_seconds"] * 2
            server.dispatch_command(server.command_sender, f"effect clear {player.name}")
            server.dispatch_command(server.command_sender, f"effect give {player.name} regeneration 15 2 true")
            server.dispatch_command(server.command_sender, f"effect give {player.name} saturation 10 1 true")
            try:
                player.play_sound(player.location, "random.levelup", 1.0, 1.5)
            except Exception:
                server.dispatch_command(server.command_sender, f"playsound random.levelup {player.name} ~ ~ ~ 1.0 1.5")
            player.send_title("§6ПАНАЦЕЯ", "§aОрганизм полностью очищен от чумы!", 10, 70, 20)
        else:
            data["immunity_until"] = now + self.config["vaccine_immunity_seconds"]
            server.dispatch_command(server.command_sender, f"effect clear {player.name}")
            server.dispatch_command(server.command_sender, f"effect give {player.name} regeneration 8 1 true")
            try:
                player.play_sound(player.location, "random.orb", 1.0, 1.2)
            except Exception:
                server.dispatch_command(server.command_sender, f"playsound random.orb {player.name} ~ ~ ~ 1.0 1.2")
            player.send_title("§bВАКЦИНАЦИЯ", "§aЧума побеждена! Иммунитет активен.", 10, 60, 20)

        self.mark_dirty()
        self.save()

    def record_kill(self, player: Player, server: Server) -> None:
        """Временное убийство сущностей облегчает симптомы (по лору)."""
        p_id = str(player.unique_id)
        data = self.get_player_data(p_id)
        if not data.get("is_infected", False):
            return

        now = time.time()
        relief_time = self.config["kill_relief_seconds"]
        data["relief_until"] = now + relief_time
        data["kills_count"] = data.get("kills_count", 0) + 1
        self.mark_dirty()

        player.send_tip(f"§a[+] Битва временно подавила симптомы чумы! ({relief_time} сек)")
        try:
            player.play_sound(player.location, "mob.warden.heartbeat", 0.5, 1.5)
        except Exception:
            server.dispatch_command(server.command_sender, f"playsound mob.warden.heartbeat {player.name} ~ ~ ~ 0.5 1.5")

    def tick_players(self, server: Server) -> None:
        now = time.time()
        stages_cfg = self.config["stages"]
        online_players = list(server.online_players)

        # 1. Построение пространственной сетки (Spatial Grid) 32x32 блока для O(n) расчёта контактов
        spatial_grid: dict[tuple[str, int, int], list[Player]] = {}
        for p in online_players:
            loc = p.location
            cell = (loc.dimension.type, int(loc.x // 32), int(loc.z // 32))
            spatial_grid.setdefault(cell, []).append(p)

        for player in online_players:
            p_id = str(player.unique_id)
            data = self.get_player_data(p_id)

            if not data.get("is_infected", False):
                continue

            stage = int(data.get("stage", 0))
            stage_duration = float(stages_cfg.get(f"stage_{stage}_duration", 600))
            time_in_stage = now - float(data.get("stage_started_at", now))

            # Проверка перехода на следующий этап
            if stage < 4 and time_in_stage >= stage_duration:
                new_stage = stage + 1
                data["stage"] = new_stage
                data["stage_started_at"] = now
                self.mark_dirty()
                self.save()

                try:
                    player.play_sound(player.location, "mob.warden.roar", 0.9, 0.8)
                except Exception:
                    server.dispatch_command(server.command_sender, f"playsound mob.warden.roar {player.name} ~ ~ ~ 0.9 0.8")

                player.send_title(
                    f"§4Чума перешла в Этап {new_stage}!",
                    "§cСимптомы ухудшаются...",
                    10, 70, 20
                )
                stage = new_stage

            is_relieved = float(data.get("relief_until", 0.0)) > now

            # 2. Троттлинг наложения эффектов (выдаём с запасом на 10 сек, обновляем раз в 7.5 сек)
            last_eff = self._last_effects_at.get(p_id, 0.0)
            should_apply_effects = (now - last_eff) >= 7.5

            if stage == 1 and not is_relieved:
                if should_apply_effects:
                    server.dispatch_command(server.command_sender, f"effect give {player.name} hunger 10 0 true")
                    server.dispatch_command(server.command_sender, f"effect give {player.name} slowness 10 0 true")
                    self._last_effects_at[p_id] = now
                if random.random() < 0.05:
                    player.send_tip("§7Вас одолевает странный голод и слабость в ногах...")

            elif stage == 2 and not is_relieved:
                if should_apply_effects:
                    server.dispatch_command(server.command_sender, f"effect give {player.name} slowness 10 1 true")
                    server.dispatch_command(server.command_sender, f"effect give {player.name} weakness 10 0 true")
                    server.dispatch_command(server.command_sender, f"effect give {player.name} hunger 10 1 true")
                    self._last_effects_at[p_id] = now
                if random.random() < 0.15:
                    server.dispatch_command(server.command_sender, f"effect give {player.name} darkness 6 0 true")
                    try:
                        player.play_sound(player.location, "mob.warden.nearby_close", 0.6, 0.7)
                    except Exception:
                        pass
                    player.send_tip("§8[!] Тьма глубин застилает взор...")

            elif stage == 3:
                if not is_relieved and should_apply_effects:
                    server.dispatch_command(server.command_sender, f"effect give {player.name} slowness 10 1 true")
                    server.dispatch_command(server.command_sender, f"effect give {player.name} weakness 10 1 true")
                    server.dispatch_command(server.command_sender, f"effect give {player.name} hunger 10 1 true")
                    self._last_effects_at[p_id] = now
                    if random.random() < 0.20:
                        server.dispatch_command(server.command_sender, f"effect give {player.name} darkness 6 0 true")

                # Распространение на игроков поблизости (проверяем раз в 5 секунд с использованием spatial grid)
                last_spread = self._last_spread_at.get(p_id, 0.0)
                if (now - last_spread) >= 5.0:
                    self._last_spread_at[p_id] = now
                    rad = float(self.config["spread_radius_stage_3"])
                    rad_sq = rad * rad
                    p_loc = player.location
                    cur_cx = int(p_loc.x // 32)
                    cur_cz = int(p_loc.z // 32)

                    # Проверяем только 9 соседних ячеек сетки
                    for dcx in (-1, 0, 1):
                        for dcz in (-1, 0, 1):
                            cell_key = (p_loc.dimension.type, cur_cx + dcx, cur_cz + dcz)
                            for other in spatial_grid.get(cell_key, []):
                                if other.unique_id == player.unique_id:
                                    continue
                                o_loc = other.location
                                # Быстрый Bounding Box до вычисления квадратов
                                if abs(o_loc.x - p_loc.x) > rad or abs(o_loc.z - p_loc.z) > rad:
                                    continue
                                dist_sq = (o_loc.x - p_loc.x) ** 2 + (o_loc.y - p_loc.y) ** 2 + (o_loc.z - p_loc.z) ** 2
                                if dist_sq <= rad_sq:
                                    if random.randint(1, 100) <= int(self.config["spread_chance_percent"]):
                                        if self.infect(other, server, initial_stage=0):
                                            player.send_tip(f"§c[!] Вы заразили игрока {other.name} при контакте!")
                                            other.send_tip("§c[!] Вы заразились от близкого контакта с носителем чумы!")

            elif stage == 4:
                if should_apply_effects:
                    server.dispatch_command(server.command_sender, f"effect give {player.name} slowness 10 2 true")
                    server.dispatch_command(server.command_sender, f"effect give {player.name} weakness 10 2 true")
                    server.dispatch_command(server.command_sender, f"effect give {player.name} hunger 10 2 true")
                    server.dispatch_command(server.command_sender, f"effect give {player.name} darkness 8 0 true")
                    self._last_effects_at[p_id] = now

                # Периодический урон: прямое снижение player.health вместо спама dispatch_command
                if random.random() < 0.35:
                    try:
                        # Нативное уменьшение здоровья
                        cur_health = player.health
                        if cur_health > 2:
                            player.health = cur_health - 2
                        else:
                            # Летальный исход
                            server.dispatch_command(server.command_sender, f"damage {player.name} 2 magic")
                    except Exception:
                        server.dispatch_command(server.command_sender, f"damage {player.name} 2 magic")

                    try:
                        player.play_sound(player.location, "mob.warden.heartbeat", 1.0, 0.5)
                    except Exception:
                        pass
                    player.send_tip("§4[!!!] Ваше тело разлагается от Скалковой Чумы! Нужна Панацея!")
