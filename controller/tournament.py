import collections
import core
import cvars
import engines.server
import itertools
import listeners
import json
import paths
import shutil

from . import controller

config = collections.defaultdict(bool, {})
bot_instances = {}  # pool of bot instances
matches = ()  # iterable of next matches


def reload_config():
    # Clear, then update config with the new dictionary loaded.
    with open(paths.PLUGIN_PATH + "/controller/config.json") as fh:
        config.clear()
        config.update(json.load(fh))

    # If SourceTV isn't already on, we'll need to change level for it to take effect
    if config["stv"]:
        tv_enabled = cvars.cvar.find_cvar("tv_enable")

        if not tv_enabled.get_bool():
            tv_enabled.set_bool(True)
            engines.server.queue_server_command("changelevel", engines.server.global_vars.map_name)

            # Add the bots after we finish changing level
            listeners.on_level_init_listener_manager.register_listener(init_bots)
            return

    init_bots()


def init_bots():
    try:
        listeners.on_level_init_listener_manager.unregister_listener(init_bots)
    except ValueError:  # not registered (we didn't need to change level)
        pass

    if isinstance(config["bots"], dict):
        # Construct singleton instances for each bot
        from . import bots

        for name, bot in config["bots"].items():
            klassname, *args = bot
            klass = getattr(bots, bot[0])

            if args:
                bot = klass(name, args)
            else:
                bot = klass(name)

            bot_instances[name.lower()] = bot

        if config["start_idle"]:
            start_idle()


# Loop through each matchup when idling in order to entertain the masses
def start_idle():
    global matches

    matches = itertools.cycle(itertools.combinations(bot_instances.values(), 2))
    controller.start_next_match()


def tourney_gen(bot1, bot2):
    if bot1 == "*":
        if bot2 == "*":  # free for all
            yield from itertools.combinations(bots.values(), 2)
        else:  # call again with the bots swapped (lazy :P)
            yield from tourney_gen(bot2, bot1)
    elif bot2 == "*":
        # one bot vs everyone
        try:
            handle1 = bot_instances[bot1.lower()]
        except KeyError:
            core.echo_console("No such bot %s." % bot1)
            return

        for name, handle2 in bot_instances.items():
            if handle2 != handle1:
                yield (handle1, handle2)
    else:
        # specific matchup
        try:
            yield (bot_instances[bot1.lower()], bot_instances[bot2.lower()])
        except KeyError:
            core.echo_console("No such matchup %s, %s" % (bot1, bot2))


#def upload_result():
#    with open(docroot + "/data.js", "w") as data:
#        data.seek(os.SEEK_END 
