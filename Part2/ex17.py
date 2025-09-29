name = input("What is your name? :")
import random
adjectives = ["Fuzzy", "Swift", "Gentle", "Clumsy", "Brave", "Spiky"]
animals = ["Elephant", "Penguin", "Kangaroo", "Fox", "Turtle", "Owl"]
print(f"{name}, your codename is", random.choice(adjectives), random.choice(animals))
print("Your lucky number is", random.randint(1, 99))