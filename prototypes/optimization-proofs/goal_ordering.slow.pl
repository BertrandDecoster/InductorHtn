% SLOW: the broad generator person/1 runs first, so every person is enumerated
% and only then filtered by rich/1.
person(alice). person(bob).  person(carol). person(dave).
person(erin).  person(frank). person(grace). person(heidi).
rich(grace).
findRich(?p) :- person(?p), rich(?p).
