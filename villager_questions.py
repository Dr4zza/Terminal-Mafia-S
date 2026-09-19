import random
questions = ['what happened during the night ? slept well?', 'what nightmare did you have ? ',
             'who are you so sure that you arent dead yet ?', 'who did you kill tonight?', 'who do you plan to kill tomorrow?']


def start_question_round(self):
    q = random.choice(questions)
    self.broadcast("\n ====== VILLAGER QUESTION ROUND ======")
    self.broadcast(f"{q}\n")
