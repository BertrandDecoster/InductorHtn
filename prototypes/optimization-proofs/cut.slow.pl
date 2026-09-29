% SLOW: the three clauses stay choice points though they are mutually
% exclusive; backtracking still explores the dead alternatives.
classify(?x, positive) :- >(?x, 0).
classify(?x, zero)     :- ==(?x, 0).
classify(?x, negative) :- <(?x, 0).
