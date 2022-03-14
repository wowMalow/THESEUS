with open('gypsy_list.txt', 'r') as file:
    users = file.read()
    uniq = list(set(users.split()))
    uniq.sort()

with open('gypsy_task.txt', 'w') as file:
    for line in uniq:
        file.write(f'{line}\n')
