import commands.typed
import players.teams

from . import controller
from . import tournament


@commands.typed.TypedServerCommand("kocp_add_bot")
def add_bot(_, name, team:int):
    tournament.bot_instances[name].spawn(team)


@commands.typed.TypedServerCommand("kocp_idle")
def idle(_):
    tournament.start_idle()


@commands.typed.TypedServerCommand("kocp_tourney")
def tourney(_, bot1="*", bot2="*"):
    tournament.matches = tournament.tourney_gen(bot1, bot2)

    if not controller.Bot.current_match:  # wait for match to finish if we're in the middle of one
        controller.start_next_match()


@commands.typed.TypedServerCommand("kocp_stop")
def end_match(_):
    controller.end_match()


@commands.typed.TypedServerCommand("kocp_force_start")
def force_start(_):
    controller.start_next_match()
