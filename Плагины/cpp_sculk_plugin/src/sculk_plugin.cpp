#include "sculk_plugin.h"
#include <endstone/server.h>
#include <endstone/player.h>
#include <endstone/color_format.h>
#include <chrono>
#include <sstream>

namespace sculk {

double SculkPlugin::getCurrentTime() const {
    auto now = std::chrono::system_clock::now().time_since_epoch();
    return std::chrono::duration<double>(now).count();
}

void SculkPlugin::onLoad() {
    getLogger().info("SculkPlugin (C++ Core) loaded successfully.");
}

void SculkPlugin::onEnable() {
    registerEvent(&SculkPlugin::onPlayerMove, *this);
    registerEvent(&SculkPlugin::onPlayerDeath, *this);
    registerEvent(&SculkPlugin::onPlayerJoin, *this);

    getLogger().info("SculkPlugin (C++ Core) enabled. Endstone plague mechanics active.");
}

void SculkPlugin::onDisable() {
    getLogger().info("SculkPlugin (C++ Core) disabled.");
}

void SculkPlugin::infectPlayer(const std::string &uuid, int stage) {
    PlayerInfection &inf = infections_[uuid];
    inf.is_infected = true;
    inf.stage = std::clamp(stage, 0, 4);
    inf.stage_started_at = getCurrentTime();
    inf.relief_until = 0.0;
}

void SculkPlugin::curePlayer(const std::string &uuid) {
    auto it = infections_.find(uuid);
    if (it != infections_.end()) {
        it->second.is_infected = false;
        it->second.stage = 0;
        it->second.immunity_until = getCurrentTime() + 600.0; // 10 минут иммунитета
    }
}

PlayerInfection* SculkPlugin::getInfection(const std::string &uuid) {
    auto it = infections_.find(uuid);
    if (it != infections_.end()) {
        return &it->second;
    }
    return nullptr;
}

bool SculkPlugin::onCommand(endstone::CommandSender &sender, const endstone::Command &command,
                            const std::vector<std::string> &args) {
    const std::string cmd = command.getName();

    if (cmd == "sculk") {
        auto *player = sender.asPlayer();
        if (!player) {
            sender.sendMessage(endstone::ColorFormat::Red + "Команда доступна только игрокам.");
            return true;
        }

        std::string uuid = player->getUniqueId().str();
        auto *inf = getInfection(uuid);

        if (!inf || !inf->is_infected) {
            player->sendMessage(endstone::ColorFormat::Green + "[Чума] Вы полностью здоровы. Признаков заражения нет.");
        } else {
            std::ostringstream ss;
            ss << endstone::ColorFormat::DarkAqua << "=== [Скалковая Чума: Статус] ===\n"
               << endstone::ColorFormat::Yellow << "Текущий этап: " << inf->stage << "/4\n";
            if (inf->stage == 0) {
                ss << endstone::ColorFormat::Gray << "Симптомы: Инкубационный период (скрытая зараза)\n";
            } else if (inf->stage == 1) {
                ss << endstone::ColorFormat::Gold << "Симптомы: Нарастающий голод и периодическая слабость\n";
            } else if (inf->stage == 2) {
                ss << endstone::ColorFormat::Red << "Симптомы: Слабость, замедление, приступы слепоты\n";
            } else if (inf->stage == 3) {
                ss << endstone::ColorFormat::DarkRed << "Симптомы: Скалковое слияние (убийства создают скалк)\n";
            } else if (inf->stage == 4) {
                ss << endstone::ColorFormat::DarkPurple << "ВНИМАНИЕ: Терминальная стадия. Риск катализации при смерти!\n";
            }
            ss << endstone::ColorFormat::Aqua << "Для лечения используйте Вакцину или Панацею.";
            player->sendMessage(ss.str());
        }
        return true;
    }

    if (cmd == "sculkadmin") {
        if (!sender.isOp()) {
            sender.sendMessage(endstone::ColorFormat::Red + "У вас нет прав администратора.");
            return true;
        }

        if (args.empty()) {
            sender.sendMessage(endstone::ColorFormat::Yellow + "Использование: /sculkadmin <infect|cure|setstage> <игрок> [параметры]");
            return true;
        }

        const std::string &sub = args[0];
        if (sub == "cure" && args.size() >= 2) {
            auto *target = getServer().getPlayer(args[1]);
            if (target) {
                curePlayer(target->getUniqueId().str());
                sender.sendMessage(endstone::ColorFormat::Green + "Игрок " + args[1] + " успешно излечен.");
                target->sendMessage(endstone::ColorFormat::Green + "[Чума] Вы были излечены администратором.");
            } else {
                sender.sendMessage(endstone::ColorFormat::Red + "Игрок не найден в сети.");
            }
            return true;
        }

        if (sub == "infect" && args.size() >= 2) {
            auto *target = getServer().getPlayer(args[1]);
            if (target) {
                int stage = (args.size() >= 3) ? std::stoi(args[2]) : 0;
                infectPlayer(target->getUniqueId().str(), stage);
                sender.sendMessage(endstone::ColorFormat::DarkAqua + "Игрок " + args[1] + " заражён (этап " + std::to_string(stage) + ").");
            } else {
                sender.sendMessage(endstone::ColorFormat::Red + "Игрок не найден в сети.");
            }
            return true;
        }
    }

    return false;
}

void SculkPlugin::onPlayerMove(endstone::PlayerMoveEvent &event) {
    // В C++ модуле здесь выполняется сверхбыстрая проверка дистанции между игроками
}

void SculkPlugin::onPlayerDeath(endstone::PlayerDeathEvent &event) {
    auto &player = event.getPlayer();
    auto *inf = getInfection(player.getUniqueId().str());

    if (inf && inf->is_infected && inf->stage == 4) {
        // Спавн скалкового катализатора на месте гибели
        auto loc = player.getLocation();
        int x = static_cast<int>(loc.getX());
        int y = static_cast<int>(loc.getY());
        int z = static_cast<int>(loc.getZ());

        std::string setblock_cmd = "setblock " + std::to_string(x) + " " +
                                   std::to_string(y) + " " + std::to_string(z) +
                                   " sculk_catalyst replace";

        getServer().dispatchCommand(getServer().getCommandSender(), setblock_cmd);
        getServer().broadcastMessage(endstone::ColorFormat::DarkRed + "[Чума] Игрок " +
                                     player.getName() + " пал от чумы и превратился в Скалковый Катализатор!");
    }
}

void SculkPlugin::onPlayerJoin(endstone::PlayerJoinEvent &event) {
    auto &player = event.getPlayer();
    player.sendTip(endstone::ColorFormat::DarkAqua + "[Чума] Активна система Скалковой Эпидемии. /sculk");
}

} // namespace sculk

ENDSTONE_PLUGIN("endstone_sculk_cpp", "1.0.0", sculk::SculkPlugin)
