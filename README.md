# Terminal-Mafia-S

An "Among Us" style social deduction game built entirely in the terminal! Created for the IAC Root 36 Hackathon, this project brings the classic party game of Mafia/Werewolf to your command line using Python socket networking.

## Overview

Terminal-Mafia-S is a multiplayer LAN game where players who are connected to a central host and are secretly assigned roles. Through alternating Day and Night phases, players must use their wits, deception, and deduction to survive.

The game features live chat, real-time voting, hidden night actions, and immersive ASCII art to bring the terminal experience to life.

The real fun is in the confusion and deceptions that engage players in the game and cultivates a sense of thrill in them. 

Every step you take, a predicament awaits!
Amongst cruel killers, doctors, cunning detectives and suspicious eyes hovering around, survival is now a challenge!! 
Will the dawn of victory belong to the brutal mafias or the optimistic village folk?


## Features

- Multiplayer LAN Architecture: Built with Python socket and threading, supporting 4+ players over a local network.

- Dynamic Role Assignment: Roles automatically scale based on the lobby size (Mafia, Doctor, Detective, Villagers).

- Day Phase

- Night Phase

- Mafia: Secret chat to coordinate and vote on a victim.

- Doctor: Chooses one person to save from elimination.

- Detective: Investigates one player to uncover if they are the Mafia.

- Villagers: Receive random, goofy "distraction" prompts (e.g., "What nightmare did you have?") to keep them occupied and hide their typing status!

- Spectator/Ghost Mode: Eliminated players receive a custom "R.I.P. Skill Issue" gravestone and become ghosts. They can watch the game unfold (including the secret Mafia chat) but cannot interact or vote.

- Immersive ASCII Art: Custom UI elements for dawning days, falling nights, detective dossiers, and mafia hits.

## The Roles

- 🔪 Mafia: Work together in secret during the night to eliminate the town. If they equal or outnumber the town, they win!

- 🩺 Doctor: A vital protector. Can choose one person each night to heal, saving them from a Mafia attack.

- 🔎 Detective: The investigator. Checks one player's identity each night to see if they are part of the Mafia.

- 🧑‍🌾 Villager: The uninformed majority. They must use logic, day-time chat, and voting to root out the impostors.

## How to Play

### Prerequisites

All players must be on the same local network (LAN) or hotspot.

Running the Game

Start the Server (Host):
One player must run the server executable. When opening for the first time, a pop-up will appear asking for access to public networks, press "OK".

> TerminalMafiaServer.exe

The server will display a local IP address (e.g., 192.168.x.x). Share this IP with the other players.

Connect to the Game (Clients):
All players (including the host, in a separate executable) must run the client executable.

> TerminalMafiaClient.exe

Enter your username and the host's IP address when prompted.

Start the Match:
Once 4 or more players are in the lobby, the host presses [ENTER] on the server terminal to assign roles and begin the game!

Commands

- Chat: Simply type and press enter to send messages (during the Day, or in the Mafia chat at Night).

- Vote/Action: Type VOTE: [playername] during the designated time limits to lock in your lynch, kill, heal, or investigate target.

*Built with Python, Sockets, and Deception for IAC Root 36.*
