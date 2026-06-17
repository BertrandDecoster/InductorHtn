% FAST: a cut after the distinguishing test commits to the matched clause.
classify(?x, positive) :- >(?x, 0), !.
classify(?x, zero)     :- ==(?x, 0), !.
classify(?x, negative) :- <(?x, 0).
