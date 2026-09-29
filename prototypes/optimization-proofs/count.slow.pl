% SLOW: findall builds a list that is thrown away; count then re-traverses.
member(a, team1). member(b, team1). member(c, team1).
member(d, team1). member(e, team1).
teamSize(?n) :- findall(?m, member(?m, team1), ?list), count(?n, member(?x, team1)).
