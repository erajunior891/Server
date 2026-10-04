#pragma once

#include <endstone/plugin/plugin.h>
#include <endstone/event/player/player_move_event.h>
#include <endstone/event/player/player_death_event.h>
#include <endstone/event/player/player_join_event.h>
#include <endstone/command/command.h>
#include <endstone/command/command_sender.h>
#include <unordered_map>
#include <string>

namespace sculk {

struct PlayerInfection {
    bool is_infected{false};
    int stage{0};
    double stage_started_at{0.0};
    double relief_until{0.0};
    double immunity_until{0.0};
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

private:
    std::unordered_map<std::string, PlayerInfection> infections_;
    void tick();
};

} // namespace sculk
