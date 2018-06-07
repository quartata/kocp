# King of the Control Point
[tag:king-of-the-hill] [tag:game] [tag:ai-player] [tag:physics]

![KoCP](...)
---
[**Leaderboard**](...)
[**Watch Live**](...)
[**View Submissions**](...)
[**Submit Bot**](...)

*Team Fortress 2* (TF2) is a multiplayer first-person shooter notable for its class-oriented teamplay and vintage 1950s setting punctuated by sophisticated technology and silly hats. This KoTH focuses on one of its nine classes -- the Demolitions Man (or Demoman for short), a black one-eyed Scotsman notorious for his assortment of exotic, unpredictable and highly explosive projectiles as well as his penchant for cheap whiskey.

Your bots will each control an actual in-game Demoman in an enclosed square arena, fighting in best-of-5 duels. The goal is pretty simple -- kill your opponent, or capture the point at the center of the arena. Utilizing your physically slippery and dynamic weaponry, however, is not so simple...

## The World

In TF2, the fundamental unit of length is the *Hammer Unit* (HU), named after the game's map editor Hammer. To give a sense of scale, the HU is about 2 centimeters (officially described as "1/16th of a foot").

The demoman is _x_x_ HUs, as depicted below:

The arena is _x_ HUs, or <...>. (There is a limit vertically, but it's high enough not to worry about.) Here are pictures of it from a few different angles: <...>

The arena splits up logically into thirds: one-third for where the first player spawns, one-third for the control point (the big metal disc you see in the center), and one-third for the second player. The center of the control point is the origin (0, 0), and each player spawns at (-<...>, 0) and (<...>, 0) respectively. The ground is flat between x = [+/-<...>, +/-<...>], followed by an incline with <...>% grade between x = [+/-<...>, +/-<...>]. In addition to the control point at the very center, there are four small health kits postioned at <...> on the flat elevated part (a pair on each side of the control point).

## The Goal

As mentioned above, the goal is simply 

## The Mechanics

### Movement

As part of a player's overall action for a given tick, there are four major components that control movement: the *viewangle*, the *forwardmove* and the *sidemove*. 

The viewangle controls in what direction your Demoman faces, and is described as a Euler angle: a yaw component, which controls left to right turning, and a pitch component, which controls moving your head up or down. (There is a roll component, however human players cannot normally change their roll.) All angles are in degrees, with yaw ranging from 0 (which points towards positive x) to 359 and pitch ranging from -180 (looking straight down) to 180 (looking straight up). Modifications to the viewangle are instantaneous -- when your action is processed, your Demoman will immediately look in the direction you specify before anything else is done.

The forwardmove and sidemove are velocities: since TF2 is physically simulated, translational movement and steering is accomplished by specifying desired velocities that your Demoman will accelerate/decelerate to automatically. The forwardmove points in the direction your Demoman is facing, while the sidemove points to their left. The cap on the combined speeds `sqrt(forwardmove^2 + sidemove^2)` is 450 HU/s -- however, the Demoman suffers from an inherent 6.66% movement speed reduction. When combined with frictional forces, this means you top out at (450 - ) * .8 = 320 HU/s when just moving forward on the ground. Note that the forwardmove and sidemove represents your desired velocity *before* these reductions -- if you want to move as fast as you can, you'll need to set forwardmove to 450. When you submit a new forwardmove or sidemove velocity, your Demoman will begin to accelerate or decelerate at a rate of 600 HU/s^2 until they reach that 


### Weapons

## The Controller