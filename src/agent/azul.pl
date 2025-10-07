
% azul.pl - Prolog rules for Azul-lite wall pattern, legality, and scoring.
% Tested with SWI-Prolog. Intended to be used via PySWIP.
% ------------------------------------------------------

% ----- Colors -----
color(blue).
color(yellow).
color(red).
color(black).
color(white).

% ----- Row capacities -----
row_capacity(1,1).
row_capacity(2,2).
row_capacity(3,3).
row_capacity(4,4).
row_capacity(5,5).

% ----- Wall pattern facts (Row, Col, Color)
% Standard Azul pattern: each row is a rotation of [blue, yellow, red, black, white]
% Row 1 (no rotation)
wall_pattern(1,1,blue).
wall_pattern(1,2,yellow).
wall_pattern(1,3,red).
wall_pattern(1,4,black).
wall_pattern(1,5,white).

% Row 2 (rotate left by 1)
wall_pattern(2,1,yellow).
wall_pattern(2,2,red).
wall_pattern(2,3,black).
wall_pattern(2,4,white).
wall_pattern(2,5,blue).

% Row 3 (rotate left by 2)
wall_pattern(3,1,red).
wall_pattern(3,2,black).
wall_pattern(3,3,white).
wall_pattern(3,4,blue).
wall_pattern(3,5,yellow).

% Row 4 (rotate left by 3)
wall_pattern(4,1,black).
wall_pattern(4,2,white).
wall_pattern(4,3,blue).
wall_pattern(4,4,yellow).
wall_pattern(4,5,red).

% Row 5 (rotate left by 4)
wall_pattern(5,1,white).
wall_pattern(5,2,blue).
wall_pattern(5,3,yellow).
wall_pattern(5,4,red).
wall_pattern(5,5,black).

% Find column for a given row and color
wall_column_for(Row, Color, Col) :-
    between(1,5,Col),
    wall_pattern(Row, Col, Color), !.

% ----- Grid helpers -----
% Grid is a list of 5 rows, each row a list of 5 cells (0 or 1).
% cell(Grid, Row, Col, Val) gets the 0/1 at position
cell(Grid, Row, Col, Val) :-
    nth1(Row, Grid, R),
    nth1(Col, R, Val).

% Check if the target cell is empty (0)
empty_cell(Grid, Row, Col) :-
    cell(Grid, Row, Col, V),
    V =:= 0.

% ----- Legality -----
% legal_placement(Row, Color, Grid) is true if placing tile of Color in Row is allowed wrt wall:
%  - Color must not already be placed in that Row (i.e., the target column must be empty).
%  - No other same color in that row (implicit by the pattern: exactly one column matches Color).
legal_placement(Row, Color, Grid) :-
    between(1,5,Row),
    color(Color),
    wall_column_for(Row, Color, Col),
    empty_cell(Grid, Row, Col).

% ----- Scoring calculation after placing a tile at (Row, Col) -----
% Count contiguous tiles horizontally including this cell
h_run_len(Grid, Row, Col, Len) :-
    h_left(Grid, Row, Col, L),
    h_right(Grid, Row, Col, R),
    Len is L + R + 1.

% Count to the left
h_left(Grid, Row, Col, Count) :-
    Col > 1,
    C1 is Col - 1,
    cell(Grid, Row, C1, V),
    ( V =:= 1 -> h_left(Grid, Row, C1, K), Count is K + 1
    ; Count = 0 ).
h_left(_, _, Col, 0) :- Col =< 1.

% Count to the right
h_right(Grid, Row, Col, Count) :-
    Col < 5,
    C1 is Col + 1,
    cell(Grid, Row, C1, V),
    ( V =:= 1 -> h_right(Grid, Row, C1, K), Count is K + 1
    ; Count = 0 ).
h_right(_, _, Col, 0) :- Col >= 5.

% Vertical run length
v_run_len(Grid, Row, Col, Len) :-
    v_up(Grid, Row, Col, U),
    v_down(Grid, Row, Col, D),
    Len is U + D + 1.

v_up(Grid, Row, Col, Count) :-
    Row > 1,
    R1 is Row - 1,
    cell(Grid, R1, Col, V),
    ( V =:= 1 -> v_up(Grid, R1, Col, K), Count is K + 1
    ; Count = 0 ).
v_up(_, Row, _, 0) :- Row =< 1.

v_down(Grid, Row, Col, Count) :-
    Row < 5,
    R1 is Row + 1,
    cell(Grid, R1, Col, V),
    ( V =:= 1 -> v_down(Grid, R1, Col, K), Count is K + 1
    ; Count = 0 ).
v_down(_, Row, _, 0) :- Row >= 5.

% score_for_placement(GridBefore, Row, Color, Score)
% Note: You must ensure the cell at (Row, Col) is empty before placement;
% scoring counts neighbors that are already placed.
score_for_placement(Grid, Row, Color, Score) :-
    wall_column_for(Row, Color, Col),
    % Compute lengths if we set this tile; neighbors are already on the grid
    h_run_len(Grid, Row, Col, HLen),
    v_run_len(Grid, Row, Col, VLen),
    ( HLen =:= 1, VLen =:= 1 -> Score = 1
    ; Score is (HLen > 1 -> HLen ; 0) + (VLen > 1 -> VLen ; 0)
    ).

% ----- Bonuses at end of game (optional, exposed for completeness) -----
% complete_row(Grid, Row): true if row has all 1s
complete_row(Grid, Row) :-
    nth1(Row, Grid, R),
    forall(member(X, R), X =:= 1).

% complete_col(Grid, Col): true if column has all 1s
complete_col(Grid, Col) :-
    findall(V, (between(1,5,R), cell(Grid,R,Col,V)), Vs),
    forall(member(X, Vs), X =:= 1).

% color_complete(Grid, Color): true if color appears exactly once in each row (i.e., 5 tiles placed)
color_complete(Grid, Color) :-
    findall((R,C), (between(1,5,R), wall_column_for(R, Color, C), cell(Grid,R,C,V), V =:= 1), Positions),
    length(Positions, 5).

