% SLOW: not(excluded(?x)) is re-proved for every item at query time.
item(a). item(b). item(c). item(d). item(e). item(f). item(g). item(h).
excluded(b). excluded(e). excluded(g).
ok(?x) :- item(?x), not(excluded(?x)).
