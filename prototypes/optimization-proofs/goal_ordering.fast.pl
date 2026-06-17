% FAST: the constraining goal rich/1 (one solution) runs first; person/1 then
% just verifies that single binding.
person(alice). person(bob).  person(carol). person(dave).
person(erin).  person(frank). person(grace). person(heidi).
rich(grace).
findRich(?p) :- rich(?p), person(?p).
