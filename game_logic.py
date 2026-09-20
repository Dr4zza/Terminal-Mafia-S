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
    for p in player_list:
        if p.name == name:
            return p
    return None


def alive_players(player_list):
    return [p for p in player_list if p.alive]


def alive_count_by_role(player_list):
    counts = {}
    for p in alive_players(player_list):
        counts[p.role] = counts.get(p.role, 0) + 1
    return counts


# ==========================================================================
# 2. VOTE TALLYING (shared by Mafia night-kill and Day lynch vote)
# ==========================================================================
def tally_votes(votes):
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
    target, _ = tally_votes(mafia_votes)
    return target


def apply_doctor_heal(kill_target_name, heal_target_name):
    if kill_target_name is None:
        return False
    return heal_target_name is not None and heal_target_name == kill_target_name


def resolve_night_phase(player_list, mafia_votes, heal_target_name, detective_target_name=None):
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
        "elimnated_role": find_player_by_name(player_list, eliminated).role
    }


# ==========================================================================
# 4b. DETECTIVE SPOTTING
# ==========================================================================
def detective_check(player_list, suspect_name):
    suspect = find_player_by_name(player_list, suspect_name)
    if suspect is None:
        return None
    return suspect.role == ROLE_MAFIA


# ==========================================================================
# 5. DAY-PHASE LYNCH VOTE
# ==========================================================================
def resolve_day_vote(player_list, day_votes):
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
    alive = alive_players(player_list)
    mafia_alive = [p for p in alive if p.role == ROLE_MAFIA]
    town_alive = [p for p in alive if p.role != ROLE_MAFIA]

    if len(mafia_alive) == 0:
        return "VILLAGERS_WIN"

    if len(mafia_alive) >= len(town_alive):
        return "MAFIA_WIN"

    return None
