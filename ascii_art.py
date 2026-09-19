DAY_ART = r"""
╔══════════════════════════════════════╗
║                                      ║
║                 \ | /                ║
║               -- ☀ --                ║
║                 / | \                ║
║                                      ║
║                D A Y                 ║
║                                      ║
║        The city awakens...           ║
║                                      ║
╚══════════════════════════════════════╝
"""


NIGHT_ART = r"""
╔══════════════════════════════════════╗
║                                      ║
║             *            *           ║
║                  🌙                  ║
║        *                    *        ║
║                                      ║
║              N I G H T               ║
║                                      ║
║        The city falls silent...      ║
║                                      ║
╚══════════════════════════════════════╝
"""


def show_phase(phase):
    if phase == "DAY":
        print(DAY_ART)

    elif phase == "NIGHT":
        print(NIGHT_ART)
