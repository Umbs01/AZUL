% ============================================================================
% AZUL GAME RULES - PROLOG IMPLEMENTATION
% ============================================================================
% This file defines the core game logic for Azul that can be queried from Python

% Tile colors
tile_color(blue).
tile_color(yellow).
tile_color(red).
tile_color(black).
tile_color(white).

% ============================================================================
% WALL PATTERN DEFINITIONS
% ============================================================================

% Standard colored wall pattern (row, col, color)
% Row 0
wall_pattern(0, 0, blue).
wall_pattern(0, 1, yellow).
wall_pattern(0, 2, red).
wall_pattern(0, 3, black).
wall_pattern(0, 4, white).

% Row 1
wall_pattern(1, 0, white).
wall_pattern(1, 1, blue).
wall_pattern(1, 2, yellow).
wall_pattern(1, 3, red).
wall_pattern(1, 4, black).

% Row 2
wall_pattern(2, 0, black).
wall_pattern(2, 1, white).
wall_pattern(2, 2, blue).
wall_pattern(2, 3, yellow).
wall_pattern(2, 4, red).

% Row 3
wall_pattern(3, 0, red).
wall_pattern(3, 1, black).
wall_pattern(3, 2, white).
wall_pattern(3, 3, blue).
wall_pattern(3, 4, yellow).

% Row 4
wall_pattern(4, 0, yellow).
wall_pattern(4, 1, red).
wall_pattern(4, 2, black).
wall_pattern(4, 3, white).
wall_pattern(4, 4, blue).

% Get column for a color in a specific row
get_wall_column(Row, Color, Col) :-
    wall_pattern(Row, Col, Color).

% ============================================================================
% MOVE VALIDATION
% ============================================================================

% Check if a color can be placed in a pattern line
% can_place_in_pattern_line(Row, Color, PatternLines, Wall)
can_place_in_pattern_line(Row, Color, PatternLines, Wall) :-
    % Check pattern line doesn't have a different color
    nth0(Row, PatternLines, CurrentLine),
    (   all_none(CurrentLine)
    ;   has_color(CurrentLine, Color)
    ),
    % Check wall doesn't already have this color in the row
    get_wall_column(Row, Color, Col),
    nth0(Row, Wall, WallRow),
    nth0(Col, WallRow, false).

% Helper: check if all elements are none/null
all_none([]).
all_none([none|T]) :- all_none(T).

% Helper: check if list has specific color
has_color([Color|_], Color) :- !.
has_color([none|T], Color) :- has_color(T, Color).

% Check if pattern line is complete
pattern_line_complete(Row, PatternLines) :-
    nth0(Row, PatternLines, Line),
    LineSize is Row + 1,
    length(Line, LineSize),
    \+ member(none, Line).

% ============================================================================
% MOVE GENERATION
% ============================================================================

% Generate all legal moves for a player
% legal_move(Source, Color, DestRow, Factories, Center, PatternLines, Wall)
legal_move(factory(FactoryIdx), Color, DestRow, Factories, _, PatternLines, Wall) :-
    % Get tiles from factory
    nth0(FactoryIdx, Factories, Factory),
    member(Color, Factory),
    % Check destination
    valid_destination(DestRow, Color, PatternLines, Wall).

legal_move(center, Color, DestRow, _, Center, PatternLines, Wall) :-
    % Get tiles from center
    member(Color, Center),
    % Check destination
    valid_destination(DestRow, Color, PatternLines, Wall).

% Valid destination is either floor line or a valid pattern line
valid_destination(floor, _, _, _).
valid_destination(Row, Color, PatternLines, Wall) :-
    between(0, 4, Row),
    can_place_in_pattern_line(Row, Color, PatternLines, Wall).

% ============================================================================
% SCORING CALCULATIONS
% ============================================================================

% Calculate score for placing a tile at (Row, Col) on the wall
calculate_tile_score(Row, Col, Wall, Score) :-
    % Calculate horizontal score
    count_horizontal(Row, Col, Wall, HScore),
    % Calculate vertical score
    count_vertical(Row, Col, Wall, VScore),
    % Combine scores
    combine_scores(HScore, VScore, Score).

% Count horizontally connected tiles
count_horizontal(Row, Col, Wall, Score) :-
    nth0(Row, Wall, WallRow),
    count_left(Col, WallRow, LeftCount),
    count_right(Col, WallRow, RightCount),
    Score is LeftCount + RightCount + 1.

% Count tiles to the left
count_left(0, _, 0) :- !.
count_left(Col, Row, Count) :-
    PrevCol is Col - 1,
    nth0(PrevCol, Row, true),
    !,
    count_left(PrevCol, Row, PrevCount),
    Count is PrevCount + 1.
count_left(_, _, 0).

% Count tiles to the right
count_right(Col, Row, Count) :-
    length(Row, Len),
    NextCol is Col + 1,
    NextCol < Len,
    nth0(NextCol, Row, true),
    !,
    count_right(NextCol, Row, PrevCount),
    Count is PrevCount + 1.
count_right(_, _, 0).

% Count vertically connected tiles
count_vertical(Row, Col, Wall, Score) :-
    count_up(Row, Col, Wall, UpCount),
    count_down(Row, Col, Wall, DownCount),
    Score is UpCount + DownCount + 1.

% Count tiles above
count_up(0, _, _, 0) :- !.
count_up(Row, Col, Wall, Count) :-
    PrevRow is Row - 1,
    nth0(PrevRow, Wall, WallRow),
    nth0(Col, WallRow, true),
    !,
    count_up(PrevRow, Col, Wall, PrevCount),
    Count is PrevCount + 1.
count_up(_, _, _, 0).

% Count tiles below
count_down(Row, Col, Wall, Count) :-
    length(Wall, Len),
    NextRow is Row + 1,
    NextRow < Len,
    nth0(NextRow, Wall, WallRow),
    nth0(Col, WallRow, true),
    !,
    count_down(NextRow, Col, Wall, PrevCount),
    Count is PrevCount + 1.
count_down(_, _, _, 0).

% Combine horizontal and vertical scores
combine_scores(1, 1, 1) :- !.  % No adjacent tiles
combine_scores(H, 1, H) :- H > 1, !.  % Only horizontal
combine_scores(1, V, V) :- V > 1, !.  % Only vertical
combine_scores(H, V, Score) :- H > 1, V > 1, Score is H + V.  % Both directions

% ============================================================================
% END GAME SCORING
% ============================================================================

% Count complete horizontal lines
count_horizontal_lines([], 0).
count_horizontal_lines([Row|Rest], Count) :-
    (   all_true(Row)
    ->  count_horizontal_lines(Rest, RestCount),
        Count is RestCount + 1
    ;   count_horizontal_lines(Rest, Count)
    ).

% Count complete vertical lines
count_vertical_lines(Wall, Count) :-
    length(Wall, Len),
    count_vertical_lines_helper(0, Len, Wall, Count).

count_vertical_lines_helper(Col, Max, _, 0) :- Col >= Max, !.
count_vertical_lines_helper(Col, Max, Wall, Count) :-
    (   column_complete(Col, Wall)
    ->  NextCol is Col + 1,
        count_vertical_lines_helper(NextCol, Max, Wall, RestCount),
        Count is RestCount + 1
    ;   NextCol is Col + 1,
        count_vertical_lines_helper(NextCol, Max, Wall, Count)
    ).

% Check if a column is complete
column_complete(Col, Wall) :-
    forall(nth0(_, Wall, Row), (nth0(Col, Row, true))).

% Count complete colors (all 5 tiles of one color placed)
count_complete_colors(Wall, Count) :-
    findall(Color, (tile_color(Color), color_complete(Color, Wall)), Colors),
    length(Colors, Count).

color_complete(Color, Wall) :-
    findall(1, (
        between(0, 4, Row),
        get_wall_column(Row, Color, Col),
        nth0(Row, Wall, WallRow),
        nth0(Col, WallRow, true)
    ), Positions),
    length(Positions, 5).