#include "sculk_plugin.h"
#include <endstone/server.h>
#include <endstone/player.h>
#include <endstone/color_format.h>

namespace sculk {

void SculkPlugin::onLoad() {
    getLogger().info("SculkPlugin (C++) loaded.");
}

void SculkPlugin::onEnable() {
    registerEvent(&SculkPlugin::onPlayerMove, *this);
    registerEvent(&SculkPlugin::onPlayerDeath, *this);
    registerEvent(&SculkPlugin::onPlayerJoin, *this);

    getLogger().info("SculkPlugin (C++) enabled. Plague mechanics active.");
}

void SculkPlugin::onDisable() {
    getLogger().info("SculkPlugin (C++) disabled.");
}

bool SculkPlugin::onCommand(endstone::CommandSender &sender, const endstone::Command &command,
                            const std::vector<std::string> &args) {
    if (command.getName() == "sculk") {
        sender.sendMessage(endstone::ColorFormat::DarkAqua + "[Чума] Меню Скалковой Эпидемии (C++ ядро).");
        return true;
    }
    return false;
}

void SculkPlugin::onPlayerMove(endstone::PlayerMoveEvent &event) {
    // Логика проверки контакта со скалком
}

void SculkPlugin::onPlayerDeath(endstone::PlayerDeathEvent &event) {
    auto &player = event.getPlayer();
    auto it = infections_.find(player.getUniqueId().str());
    if (it != infections_.end() && it->second.is_infected && it->second.stage == 4) {
        // Спавн катализатора
        auto loc = player.getLocation();
        getServer().dispatchCommand(
            getServer().getCommandSender(),
            "setblock " + std::to_string(static_cast<int>(loc.getX())) + " " +
                std::to_string(static_cast<int>(loc.getY())) + " " +
                std::to_string(static_cast<int>(loc.getZ())) + " sculk_catalyst replace");
    }
}

void SculkPlugin::onPlayerJoin(endstone::PlayerJoinEvent &event) {
    auto &player = event.getPlayer();
    player.sendTip(endstone::ColorFormat::DarkAqua + "[Чума] Сервер использует плагин Скалковой Эпидемии.");
}

} // namespace sculk

ENDSTONE_PLUGIN("endstone_sculk_cpp", "1.0.0", sculk::SculkPlugin)
