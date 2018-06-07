import entities.helpers
import players.bots
import players.entity
import queue
import subprocess
import threading

from .. import controller

# Can't put these inside the class, since the decorator can't get to them :/
commands = [None for _ in range(26)]
cache = ([None for _ in range(26)], [None for _ in range(26)])
honor_cache = False


# Simple decorator to add a command to the commands array
def command(cmd):
    def decorator(f):
        commands[ord(cmd) - 97] = f
        return f

    return decorator


# if this code looks ugly, it's because I prematurely optimized it
class SubprocessBot(controller.Bot):
    def __init__(self, name, *process):
        self.name = name
        self.process_args = process

        # Keep one instance of BotCmd around to populate with our buttons,
        # rather than creating a new one and wrapping it every tick (expensive!)
        self.cmd = players.bots.BotCmd()
        self.button_queue = queue.Queue()
        self.angle_queue = queue.Queue()

    def spawn(self, team, callback=None):
        # self.controller wraps CBasePlayer::PlayerRunCommand
        # self.player is for everything else
        # Unfortunately, converting directly from an edict to a Player is ugly...
        edict = players.bots.bot_manager.create_bot(bot)

        self.controller = players.bots.bot_manager.get_bot_controller(edict)
        self.player = players.entity.Player(entities.helpers.index_from_edict(edict))
        self.team = team

        # You *must* set m_Shared.m_iDesiredPlayerClass, otherwise it won't spawn
        # 4 is Demoman
        self.player.set_team(self.team + 2)
        self.player.set_property_uchar("m_Shared.m_iDesiredPlayerClass", 4)
        self.player.spawn()

        # Save the ready callback so the server can call it when the child process reports in
        self.ready_callback = callback
        threading.Thread(target=self.server).start()

        super().spawn(team)

    def server(self):
        global cache
        global honor_cache

        # Spawn subprocess
        self.pipe = subprocess.Popen(self.process_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE)

        # We wrap this in a try, so that all we have to do during cleanup is close the pipe
        # It'll throw an OSError, and we can catch it and exit
        try:
            while True:
                # First letter defines the command, rest are the arguments
                msg = reader.readline()
                cmd = msg[0]
                cmd_index = cmd | 32 - 97  # force lowercase, then remap starting at 0

                command = commands[cmd_index]

                # honor_cache gets set to false to bust the cache every tick
                # If we should still honor it, then fetch cached output *for the given team*
                # That is, if a RED bot fetches their health it gets stored under cache[0]
                # Then when a BLU bot asks for *enemy* health it'll also get fetched from cache[0]
                if command:
                    # If the command is uppercase, it's referring to the enemy
                    # If it's lowercase, it's referring to us
                    # not (cmd & 32) gets you 0 for lowercase and 1 for uppercase
                    # So XORing it with self.team will invert the team number if it was uppercase
                    enemy = not (cmd & 32)
                    team = self.team ^ enemy

                    result = (honor_cache and cache[team][cmd]) or command(team, enemy, msg[1:])
                    os.write(self.pipe, result)

                    cache[team][cmd] = result
                    honor_cache = True  # FIXME: should be atomic?
        except OSError:
            # Pipe closed, finish
            return

    def think(self):
        # Called once per tick
        # We have to do all of the set operations in here, since Source is very much not thread-safe
        # All modifications must be done within a game frame (and done quickly)
        global honor_cache
        honor_cache = False

        buttons = self.button_queue.get(False)
        angle = self.angle_queue.get(False)

        # If there aren't new buttons or angles, we'll just reuse the last ones
        # set in self.cmd
        if buttons:
            self.cmd.buttons = buttons

        if angle:
            pitch, yaw = angle
            self.cmd.view_angles.x = yaw
            self.cmd.view_angles.y = pitch

        self.controller.run_player_move(self.cmd)
        os.write(self.pipe, b"t")  # let child process know a tick has passed

    def finish(self):
        # also kills off the server thread
        global honor_cache

        if self.pipe:
            self.pipe.close()

        honor_cache = False
        self.player.kick()

    def round_end(self, win=True):
        if win:
            os.write(self.pipe, b"w")
        else:
            os.write(self.pipe, b"l")

    # COMMANDS
    @command("b")
    def buttons(self, _, _1, args):
        self.button_queue.put(int(args))

    @command("c")
    def get_clip(self, team, enemy, _):
        global cache

        if enemy:
            weapon = Bot.active_bots[team].get_active_weapon()
        else:
            weapon = self.player.get_active_weapon()

        # Also cache ammo
        cache[team][3] = weapon.get_ammo()
        return b"c%d" % weapon.get_clip()

    @command("d")
    def get_ammo(self, team, enemy, _):
        if enemy:
            weapon = Bot.active_bots[team].get_active_weapon()
        else:
            weapon = self.player.get_active_weapon()

        # Also cache clip
        cache[team][2] = weapon.get_clip()
        return b"d%d" % weapon.get_ammo()

    @command("g")
    def get_grenades(self, team, enemy, _):
        pass

    @command("h")
    def get_health(self, team, enemy, _):
        if enemy:
            player = Bot.active_bots[team]
        else:
            player = self.player
            
        return player.get_health()

    @command("")

    @command("r")
    def ready(self, _, _1):
        if self.ready_callback:
            self.ready_callback()