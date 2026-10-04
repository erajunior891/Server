"""
Менеджер Скалковой Эпидемии (прогресс, симптомы, лечение, сохранение).
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
        self.players_data: dict[str, dict] = {}
        self.load()

    def load(self) -> None:
        if os.path.exists(self.players_file):
            try:
                with open(self.players_file, "r", encoding="utf-8") as f:
                    self.players_data = json.load(f)
            except Exception:
                self.players_data = {}
        else:
            self.players_data = {}

    def save(self) -> None:
        os.makedirs(self.data_folder, exist_ok=True)
        try:
            with open(self.players_file, "w", encoding="utf-8") as f:
                json.dump(self.players_data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

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
        self.save()

        # Звуковой и визуальный эффект заражения
        loc = player.location
        server.dispatch_command(
            server.command_sender,
            f"playsound mob.warden.heartbeat {player.name} ~ ~ ~ 0.8 0.6"
        )
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
        self.save()

        server.dispatch_command(
            server.command_sender,
            f"playsound mob.warden.listening {player.name} ~ ~ ~ 1.0 0.8"
        )
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

        if is_panacea:
            # Панацея дает мощный иммунитет и восстановление
            data["immunity_until"] = now + self.config["vaccine_immunity_seconds"] * 2
            server.dispatch_command(server.command_sender, f"effect clear {player.name}")
            server.dispatch_command(server.command_sender, f"effect give {player.name} regeneration 15 2 true")
            server.dispatch_command(server.command_sender, f"effect give {player.name} saturation 10 1 true")
            server.dispatch_command(server.command_sender, f"playsound random.levelup {player.name} ~ ~ ~ 1.0 1.5")
            player.send_title("§6ПАНАЦЕЯ", "§aОрганизм полностью очищен от чумы!", 10, 70, 20)
        else:
            # Вакцина
            data["immunity_until"] = now + self.config["vaccine_immunity_seconds"]
            server.dispatch_command(server.command_sender, f"effect clear {player.name}")
            server.dispatch_command(server.command_sender, f"effect give {player.name} regeneration 8 1 true")
            server.dispatch_command(server.command_sender, f"playsound random.orb {player.name} ~ ~ ~ 1.0 1.2")
            player.send_title("§bВАКЦИНАЦИЯ", "§aЧума побеждена! Иммунитет активен.", 10, 60, 20)

        self.save()

    def record_kill(self, player: Player, server: Server) -> None:
        """Временное убийство сущностей облегчает симптомы (по лору)"""
        p_id = str(player.unique_id)
        data = self.get_player_data(p_id)
        if not data.get("is_infected", False):
            return

        now = time.time()
        relief_time = self.config["kill_relief_seconds"]
        data["relief_until"] = now + relief_time
        data["kills_count"] = data.get("kills_count", 0) + 1
        self.save()

        player.send_tip(f"§a[+] Битва временно подавила симптомы чумы! ({relief_time} сек)")
        server.dispatch_command(server.command_sender, f"playsound mob.warden.heartbeat {player.name} ~ ~ ~ 0.5 1.5")

    def tick_players(self, server: Server) -> None:
        now = time.time()
        stages_cfg = self.config["stages"]

        online_players = list(server.online_players)

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
                self.save()
                server.dispatch_command(
                    server.command_sender,
                    f"playsound mob.warden.roar {player.name} ~ ~ ~ 0.9 0.8"
                )
                player.send_title(
                    f"§4Чума перешла в Этап {new_stage}!",
                    "§cСимптомы ухудшаются...",
                    10, 70, 20
                )
                stage = new_stage

            # Проверка временного облегчения
            is_relieved = float(data.get("relief_until", 0.0)) > now

            # Наложение симптомов в зависимости от этапа
            if stage == 0:
                # 0 Этап: без симптомов
                pass

            elif stage == 1:
                # 1 Этап: Голод + Замедление
                if not is_relieved:
                    server.dispatch_command(server.command_sender, f"effect give {player.name} hunger 4 0 true")
                    server.dispatch_command(server.command_sender, f"effect give {player.name} slowness 4 0 true")
                    if random.random() < 0.15:
                        player.send_tip("§7Вас одолевает странный голод и слабость в ногах...")

            elif stage == 2:
                # 2 Этап: Замедление + Слабость + Голод + Слепота/Тьма (рандомно)
                if not is_relieved:
                    server.dispatch_command(server.command_sender, f"effect give {player.name} slowness 4 1 true")
                    server.dispatch_command(server.command_sender, f"effect give {player.name} weakness 4 0 true")
                    server.dispatch_command(server.command_sender, f"effect give {player.name} hunger 4 1 true")
                    if random.random() < 0.20:
                        server.dispatch_command(server.command_sender, f"effect give {player.name} darkness 5 0 true")
                        server.dispatch_command(server.command_sender, f"playsound mob.warden.nearby_close {player.name} ~ ~ ~ 0.6 0.7")
                        player.send_tip("§8[!] Тьма глубин застилает взор...")

            elif stage == 3:
                # 3 Этап: Убийства распространяют скалк + заражение других игроков
                if not is_relieved:
                    server.dispatch_command(server.command_sender, f"effect give {player.name} slowness 4 1 true")
                    server.dispatch_command(server.command_sender, f"effect give {player.name} weakness 4 1 true")
                    server.dispatch_command(server.command_sender, f"effect give {player.name} hunger 4 1 true")
                    if random.random() < 0.25:
                        server.dispatch_command(server.command_sender, f"effect give {player.name} darkness 6 0 true")

                # Распространение на других игроков поблизости
                rad = float(self.config["spread_radius_stage_3"])
                p_loc = player.location
                for other in online_players:
                    if other.unique_id == player.unique_id:
                        continue
                    o_loc = other.location
                    if o_loc.dimension.type == p_loc.dimension.type:
                        dist_sq = (o_loc.x - p_loc.x) ** 2 + (o_loc.y - p_loc.y) ** 2 + (o_loc.z - p_loc.z) ** 2
                        if dist_sq <= rad * rad:
                            if random.randint(1, 100) <= int(self.config["spread_chance_percent"]):
                                if self.infect(other, server, initial_stage=0):
                                    player.send_tip(f"§c[!] Вы заразили игрока {other.name} при контакте!")
                                    other.send_tip("§c[!] Вы заразились от близкого контакта с носителем чумы!")

            elif stage == 4:
                # 4 Этап: Критическое состояние, периодический урон, риск смерти
                server.dispatch_command(server.command_sender, f"effect give {player.name} slowness 4 2 true")
                server.dispatch_command(server.command_sender, f"effect give {player.name} weakness 4 2 true")
                server.dispatch_command(server.command_sender, f"effect give {player.name} hunger 4 2 true")
                server.dispatch_command(server.command_sender, f"effect give {player.name} darkness 5 0 true")

                # Периодический урон (смерть от симптомов)
                if random.random() < 0.40:
                    server.dispatch_command(server.command_sender, f"damage {player.name} 2 magic")
                    server.dispatch_command(server.command_sender, f"playsound mob.warden.heartbeat {player.name} ~ ~ ~ 1.0 0.5")
                    player.send_tip("§4[!!!] Ваше тело разлагается от Скалковой Чумы! Нужна Панацея!")
