% FAST: count directly; no throwaway list.
member(a, team1). member(b, team1). member(c, team1).
member(d, team1). member(e, team1).
teamSize(?n) :- count(?n, member(?x, team1)).
