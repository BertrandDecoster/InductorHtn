% FAST: the allowed set is materialized as facts; no runtime negation.
okItem(a). okItem(c). okItem(d). okItem(f). okItem(h).
ok(?x) :- okItem(?x).
