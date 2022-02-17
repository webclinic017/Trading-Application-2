n = 4
trust = [[1, 3], [1, 4], [2, 3], [2, 4], [4, 3]]

all_people = [*range(1, n+1)]
people_who_trust = []
not_trusted_people = []
for item in trust:
    people_who_trust.append(item[0])
    # not_trusted_people.append(item[0])

people_who_trust = list[set(people_who_trust)]


# not_trusted_people = set(not_trusted_people)
# print(people_who_trust)
# print(not_trusted_people)
# print(not_trusted_people - people_who_trust)