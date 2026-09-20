import random
questions = ['\nWhat happened during the night? Slept well?', '\nWhat nightmare did you have ? ',
             '\nWho are you so sure that you arent dead yet ?', '\nWho did you kill tonight?', 'Who do you plan to kill tomorrow?']

# Replace 'self' with 'broadcast_func'
def start_question_round(broadcast_func):
    q = random.choice(questions)
    # Call the function directly instead of using .broadcast()
    broadcast_func("\n ====== VILLAGER QUESTION ROUND ======")
    broadcast_func(f"{q}\n")