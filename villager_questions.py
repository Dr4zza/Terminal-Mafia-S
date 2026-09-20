import random
questions = ['\nWhat happened during the night? Slept well?', '\nWhat nightmare did you have ?',
             "\nWho are you so sure that you is'nt dead yet ?", '\nWho did you kill tonight?', '\nWho do you plan to kill tomorrow?']

def start_question_round(broadcast_func):
    q = random.choice(questions)
    broadcast_func("\n ====== VILLAGER QUESTION ROUND ======")
    broadcast_func(f"{q}\n")