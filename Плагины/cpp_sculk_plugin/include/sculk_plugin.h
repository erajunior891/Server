#pragma once

#include <endstone/plugin/plugin.h>
#include <endstone/event/player/player_move_event.h>
#include <endstone/event/player/player_death_event.h>
#include <endstone/event/player/player_join_event.h>
#include <endstone/command/command.h>
#include <endstone/command/command_sender.h>
#include <unordered_map>
#include <string>
#include <chrono>

namespace sculk {

/**
 * @brief Структура состояния заражения игрока
 */
struct PlayerInfection {
    bool is_infected{false};
    int stage{0};                      // 0: Инкубация, 1: Начало, 2: Прогресс, 3: Слияние, 4: Катализация
    double stage_started_at{0.0};      // Время перехода на стадию (epoch seconds)
    double relief_until{0.0};          // Временное облегчение (убийство мобов)
    double immunity_until{0.0};        // Время действия иммунитета после вакцинации
};

class SculkPlugin : public endstone::Plugin {
public:
    void onLoad() override;
    void onEnable() override;
    void onDisable() override;

    bool onCommand(endstone::CommandSender &sender, const endstone::Command &command,
                   const std::vector<std::string> &args) override;

    void onPlayerMove(endstone::PlayerMoveEvent &event);
    void onPlayerDeath(endstone::PlayerDeathEvent &event);
    void onPlayerJoin(endstone::PlayerJoinEvent &event);

    // Методы управления инфекцией
    void infectPlayer(const std::string &uuid, int stage = 0);
    void curePlayer(const std::string &uuid);
    PlayerInfection* getInfection(const std::string &uuid);

private:
    std::unordered_map<std::string, PlayerInfection> infections_;

    double getCurrentTime() const;
    void applyStageEffects(endstone::Player &player, const PlayerInfection &inf);
};

} // namespace sculk
