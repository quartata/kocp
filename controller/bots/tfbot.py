import cvars
import engines.server
import entities.helpers
import listeners
import filters.players

from .. import controller


class TFBot(controller.Bot):
    # General settings:
    # Crank difficulty up to 11 and make sure the bots don't try to switch class
    cvars.cvar.find_var("tf_bot_join_after_player").set_bool(False)
    cvars.cvar.find_var("tf_bot_keep_class_after_death").set_bool(True)
    cvars.cvar.find_var("tf_bot_reevaluate_class_in_spawnroom").set_bool(False)
    cvars.cvar.find_var("tf_bot_difficulty").set_int(3)

    def __init__(self, name):
        self.name = name
        self.player = None

    def spawn(self, team, callback=None):
        team_name = "blue" if team else "red"
        engines.server.queue_server_command("tf_bot_add", 1, "demoman", team_name, self.name)

        if callback:
            def f():
                for player in filters.players.PlayerIter():
                    name = player.get_name()

                    # Hack to tell if this is the bot we spawned... :/
                    # The name isn't set when OnClientActive is called, sadly
                    if name and player.is_fake_client() and name.endswith(self.name):
                        self.player = player

                        listeners.on_tick_listener_manager.unregister_listener(f)
                        callback()

            listeners.on_tick_listener_manager.register_listener(f)

        super().spawn(team)

    def think(self):
        pass

    def finish(self):
        self.player.kick()
