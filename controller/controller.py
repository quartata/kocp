import abc
import core
import cvars
import engines.server
import events.manager
import listeners
import messages
import secrets

from . import tournament
from . import commands


# Simple way to pause/unpause the "waiting for players" period
pause = cvars.cvar.find_var("mp_tournament")


class BotMetaclass(abc.ABCMeta):
    def __call__(self, *args):
        instance = super().__call__(*args)

        # make sure these are set to *something*
        instance.name
        instance.player

        return instance


# interface for bot managers to implement
class Bot(metaclass=BotMetaclass):
    # index 0 for the RED bots (team 2), 1 for BLU bots (team 3)
    active_bots = ([], [])
    num_bots = 0

    # tournament vs manually spawned bots
    current_match = None
    current_demo_name = ""
    wins = [0, 0]

    # bots readied up
    ready_count = 0

    # Create an instance of the bot player and spawn it (along with any other threads)
    # Call the callback when the bot is ready
    @abc.abstractmethod
    def spawn(self, team, callback=None):
        Bot.active_bots[team].append(self)
        Bot.num_bots += 1

    # Called per tick
    @abc.abstractmethod
    def think(self):
        pass

    # Called to clean up and kick the bot
    @abc.abstractmethod
    def finish(self):
        pass

    # Doesn't need to be overridden: called at the end of every round if you won/lost
    def round_end(self, win=True):
        pass


def load():
    # General game settings: no crits, no random damage, fixed weapon spreads
    cvars.cvar.find_var("tf_allow_server_hibernation").set_bool(False)
    cvars.cvar.find_var("tf_damage_disablespread").set_bool(True)
    cvars.cvar.find_var("tf_weapon_criticals").set_bool(False)
    cvars.cvar.find_var("tf_weapon_criticals_melee").set_bool(False)
    cvars.cvar.find_var("tf_use_fixed_weaponspreads").set_bool(True)
    
    pause.set_bool(True)

    # Load up the config (turn on STV if in the config also)
    tournament.reload_config()


def start_next_match():
    try:
        matchup = next(tournament.matches)  # next from iterator
    except:  # end of matchups
        Bot.current_match = None

        core.echo_console("Tournament completed.")
        return

    Bot.current_match = matchup

    # Spawn bots
    for i, bot in enumerate(matchup):
        team = i & 1  # i & 1 == i % 2. Just to assign the bots evenly, team doesn't really matter
        bot.spawn(team, callback=ready_up)


def ready_up():
    Bot.ready_count += 1

    if Bot.ready_count >= Bot.num_bots:  # we all ready?
        # Begin match after countdown
        pause.set_bool(False)

        # Register round start/end events
        events.manager.event_manager.register_for_event("teamplay_round_active", start_round)
        events.manager.event_manager.register_for_event("teamplay_round_win", end_round)

        # If STV is on, starting recording a demo
        if tournament.config["stv"]:
            Bot.current_demo_name = secrets.token_hex()
            engines.server.queue_server_command("tv_record", Bot.current_demo_name)


def end_match():
    # unregister event listeners
    events.manager.event_manager.unregister_for_event("teamplay_round_active", start_round)
    events.manager.event_manager.unregister_for_event("teamplay_round_win", end_round)

    # kick the bots
    for team in Bot.active_bots:
        for bot in team:
            bot.finish()

        team.clear()

    # finish the STV demo, if we were recording one
    if Bot.current_demo_name:
        engines.server.queue_server_command("tv_stoprecord")

    # pause waiting for players
    pause.set_bool(True)


def on_tick():
    # tick all the bots we have
    for team in Bot.active_bots:
        for bot in team:
            bot.think()


def start_round(_):
    # bots can move now (round active); let them start thinking
    try:
        listeners.on_tick_listener_manager.register_listener(on_tick)
    except ValueError:
        pass


def end_round(event):
    # Stop thinking for now
    listeners.on_tick_listener_manager.unregister_listener(on_tick)
    winner = event.get_int("team") - 2

    # Let the bots know who won and who lost
    # note that team_num ^ 1 == opposing_team
    for winning_bot in Bot.active_bots[winner]:
        winning_bot.round_end(win=True)

    for losing_bot in Bot.active_bots[winner ^ 1]:
        losing_bot.round_end(win=False)

    # if we're in a tourney, update wins
    # and check if we've reached the end of the match
    if Bot.current_match:
        Bot.wins[winner] += 1

        msg = "%d-%d" % (Bot.wins[0], Bot.wins[1])

        messages.SayText2(msg).send()
        if tournament.config["stv"]:
            engines.server.queue_server_command("tv_msg", msg)

        if Bot.wins[winner] > config["playing_to"]:
            end_match()

            #tournament.upload_match(Bot.current_match, Bot.current_demo_name)
            controller.start_next_match()
