"""
game_logic.py
--------------
Owner: K (Kesh) -- Game Rules & Faction Logic

Standalone, network-free functions implementing the Mafia game's rules:
  1. Dynamic role assignment (Mafia count scales with player count)
  2. Mafia target selection (majority-vote kill)
  3. Doctor healing
  4. Detective spotting
  5. Day-phase lynch vote resolution
  6. Basic vote-target validation (for graceful invalid-input handling)
  7. Win condition checking

Design contract with the rest of the team:
  - This module never touches sockets, threads, or input()/print(). Z's
    server.py owns all networking; N's client.py owns all display. That
    way K and Z never edit the same lines, per the team split.
  - Every function here takes plain data (player objects, dicts, strings)
    and returns plain data. Z imports whatever's needed into server.py.
  - "Player objects" below only need .name, .role, and .alive attributes,
    matching SinglePlayer in main.py, so game_manager.player_list can be
    passed straight in unmodified.

Role strings used throughout (kept identical to main.py's literals):
    "Mafia", "Doctor", "Detective", "Villager"
"""

import random

# --------------------------------------------------------------------------
# Role name constants. The *values* deliberately match the string literals
# main.py already uses ("Mafia", "Doctor", "Villager"), so any existing
# p.role == "Mafia" check elsewhere in the codebase keeps working untouched.
# "Detective" is new -- see the note on build_role_pool() below.
# --------------------------------------------------------------------------
ROLE_MAFIA = "Mafia"
ROLE_DOCTOR = "Doctor"
ROLE_DETECTIVE = "Detective"
ROLE_VILLAGER = "Villager"

ALL_ROLES = {ROLE_MAFIA, ROLE_DOCTOR, ROLE_DETECTIVE, ROLE_VILLAGER}


# ==========================================================================
# 1. DYNAMIC ROLE ASSIGNMENT
# ==========================================================================
def build_role_pool(num_players, include_doctor=True, include_detective=True):
    """
    Builds a shuffled list of role strings, one per player.

    Mafia count = num_players // 3 (minimum 1), per the team split ("total
    player count divided by 3"). One Doctor and one Detective are set aside
    next (if there's room and the flags are True), everyone else defaults
    to Villager/crewmate.

    Integration note for Z (main.py):
        Replace the hardcoded line in `player.__init__`:
            role_pool = ['Mafia'] + ['Doctor'] + ['Villager'] * (len(players) - 2)
            random.shuffle(role_pool)
        with:
            from game_logic import build_role_pool
            role_pool = build_role_pool(len(players))
        (build_role_pool already returns it shuffled, so the separate
        random.shuffle call can be deleted).

        NOTE: main.py currently has no "Detective" role anywhere, so
        detective_check() below will never actually fire until this swap
        happens on your end.
    """
    if num_players < 4:
        raise ValueError("Need at least 4 players to assign roles")

    num_mafia = max(1, num_players // 3)
    remaining = num_players - num_mafia

    role_pool = [ROLE_MAFIA] * num_mafia

    if include_doctor and remaining > 0:
        role_pool.append(ROLE_DOCTOR)
        remaining -= 1

    if include_detective and remaining > 0:
        role_pool.append(ROLE_DETECTIVE)
        remaining -= 1

    role_pool += [ROLE_VILLAGER] * remaining

    random.shuffle(role_pool)
    return role_pool


# ==========================================================================
# Small shared helpers
# ==========================================================================
def find_player_by_name(player_list, name):
    """Returns the SinglePlayer with this .name, or None if not found."""
    for p in player_list:
        if p.name == name:
            return p
    return None


def alive_players(player_list):
    """Returns only the still-alive players from player_list."""
    return [p for p in player_list if p.alive]


def alive_count_by_role(player_list):
    """
    {"Mafia": 2, "Doctor": 1, ...} for everyone currently alive.
    Handy for the "print all details (roles remaining)" step from the
    ideas doc -- call this after each elimination to show a summary.
    """
    counts = {}
    for p in alive_players(player_list):
        counts[p.role] = counts.get(p.role, 0) + 1
    return counts


# ==========================================================================
# 2. VOTE TALLYING (shared by Mafia night-kill and Day lynch vote)
# ==========================================================================
def tally_votes(votes):
    """
    votes: {voter_name: target_name}. Empty/None targets count as
    abstentions and are ignored when picking a winner (but still count
    toward the total when checking for a majority).

    Returns (winner, counts):
      winner = the target with a STRICT majority (more than half of all
               votes cast), or None if there's no majority or the top
               spot is tied.
      counts = {target_name: vote_count}, useful for logging/debugging.

    Matches the ideas doc: "Majority name - kill, if equal then dont kill".
    """
    if not votes:
        return None, {}

    counts = {}
    for target in votes.values():
        if not target:
            continue
        counts[target] = counts.get(target, 0) + 1

    if not counts:
        return None, counts

    total_votes = len(votes)
    top_target = max(counts, key=counts.get)
    top_count = counts[top_target]

    if top_count <= total_votes / 2:
        return None, counts

    tied_leaders = [t for t, c in counts.items() if c == top_count]
    if len(tied_leaders) > 1:
        return None, counts

    return top_target, counts


# ==========================================================================
# 3 & 4. MAFIA KILL + DOCTOR HEAL (Night phase)
# ==========================================================================
def resolve_mafia_kill(mafia_votes):
    """mafia_votes: {mafia_player_name: target_name}. Returns the target
    name if the Mafia reach majority agreement, else None (no kill)."""
    target, _ = tally_votes(mafia_votes)
    return target


def apply_doctor_heal(kill_target_name, heal_target_name):
    """True if the Doctor's heal saves the Mafia's chosen kill target."""
    if kill_target_name is None:
        return False
    return heal_target_name is not None and heal_target_name == kill_target_name


def resolve_night_phase(player_list, mafia_votes, heal_target_name, detective_target_name=None):
    """
    One-call wrapper for the whole Night phase: kill -> heal -> optional
    detective check -> win condition. Marks the victim's .alive = False
    on player_list directly if someone dies.

    Integration note for Z (server.py):
        This is exactly the "# remaining stuff to be coded after keshav's
        logic" placeholder in game_loop()/night_time(). Once you've
        collected mafia_votes (via send_to_mafia prompts) and the doctor's
        pick, call:
            from game_logic import resolve_night_phase
            result = resolve_night_phase(game_manager.player_list,
                                          mafia_votes, doctor_heal_target,
                                          detective_target)
            if result["eliminated"]:
                broadcast(f"{result['eliminated']} was killed during the night.")
            else:
                broadcast("No one died last night.")
            if result["win_status"]:
                broadcast(f"GAME OVER: {result['win_status']}")

    Returns:
        {
          "eliminated": name or None,
          "saved": bool,                 # doctor's heal worked
          "detective_result": bool/None, # True=suspect is Mafia, None=no check made
          "win_status": "MAFIA_WIN" / "VILLAGERS_WIN" / None,
        }
    """
    kill_target = resolve_mafia_kill(mafia_votes)
    saved = apply_doctor_heal(kill_target, heal_target_name)
    eliminated = None if saved else kill_target

    if eliminated:
        victim = find_player_by_name(player_list, eliminated)
        if victim is not None:
            victim.alive = False

    detective_result = None
    if detective_target_name:
        detective_result = detective_check(player_list, detective_target_name)

    return {
        "eliminated": eliminated,
        "saved": saved,
        "detective_result": detective_result,
        "win_status": check_win_condition(player_list),
    }


# ==========================================================================
# 4b. DETECTIVE SPOTTING
# ==========================================================================
def detective_check(player_list, suspect_name):
    """True if suspect is Mafia, False if not, None if suspect_name doesn't
    match anyone alive-or-dead (so the caller can send back a friendly
    error instead of crashing)."""
    suspect = find_player_by_name(player_list, suspect_name)
    if suspect is None:
        return None
    return suspect.role == ROLE_MAFIA


# ==========================================================================
# 5. DAY-PHASE LYNCH VOTE
# ==========================================================================
def resolve_day_vote(player_list, day_votes):
    """
    day_votes: {voter_name: target_name}. Reuses tally_votes so both the
    Day lynch and the Mafia night-kill share one "no majority -> no
    elimination" rule.

    Integration note for Z (server.py):
        handle_client() already parses "VOTE:" messages and broadcasts
        them, but never tallies them. Collect each round's votes into a
        dict and call this once the Day discussion timer ends:
            result = resolve_day_vote(game_manager.player_list, day_votes)
    """
    eliminated, _ = tally_votes(day_votes)

    if eliminated:
        victim = find_player_by_name(player_list, eliminated)
        if victim is not None:
            victim.alive = False

    return {
        "eliminated": eliminated,
        "win_status": check_win_condition(player_list),
    }


# ==========================================================================
# 6. VOTE VALIDATION (graceful handling of invalid input)
# ==========================================================================
def is_valid_vote_target(player_list, voter_name, target_name):
    """
    True only if target_name is a *living* player in player_list, other
    than the voter. Z's server.py can call this before accepting a
    VOTE:/kill/heal pick instead of tallying garbage input.
    """
    if not target_name:
        return False
    target = find_player_by_name(player_list, target_name)
    if target is None:
        return False
    if not target.alive:
        return False
    if target_name == voter_name:
        return False
    return True


# ==========================================================================
# 7. WIN CONDITIONS
# ==========================================================================
def check_win_condition(player_list):
    """
    Call this after every elimination (day lynch or night kill).

    Returns "MAFIA_WIN" once Mafia are alive in numbers >= the rest of the
    town (the standard Mafia end condition -- once it's a tie, Mafia can no
    longer be out-voted), "VILLAGERS_WIN" once no Mafia are left alive, or
    None if the game should continue.
    """
    alive = alive_players(player_list)
    mafia_alive = [p for p in alive if p.role == ROLE_MAFIA]
    town_alive = [p for p in alive if p.role != ROLE_MAFIA]

    if len(mafia_alive) == 0:
        return "VILLAGERS_WIN"

    if len(mafia_alive) >= len(town_alive):
        return "MAFIA_WIN"

    return None
