from cl.hackathon.hackathon_solution import HackathonSolution
from cl.hackathon.hackathon_trade_group_key import HackathonTradeGroupKey


def test_get_trade_ids_list():
    solution = HackathonSolution(trade_group=HackathonTradeGroupKey(trade_group_id="test"))

    solution.trade_ids = "1-3"
    # Basic range
    assert solution.get_trade_ids_list() == [1, 2, 3]
    # Single number
    solution.trade_ids = "5"
    assert solution.get_trade_ids_list() == [5]
    # Combination of range and single number
    solution.trade_ids = "1-3, 5"
    assert solution.get_trade_ids_list() == [1, 2, 3, 5]
    # Multiple ranges and single numbers
    solution.trade_ids = "1-3, 5, 7-9"
    assert solution.get_trade_ids_list() == [1, 2, 3, 5, 7, 8, 9]
    # Overlapping ranges
    solution.trade_ids = "1-3, 2-4"
    assert solution.get_trade_ids_list() == [1, 2, 3, 4]
    # Empty input
    solution.trade_ids = ""
    assert solution.get_trade_ids_list() == []
    # Whitespaces around numbers and ranges
    solution.trade_ids = " 1 - 3 , 5 "
    assert solution.get_trade_ids_list() == [1, 2, 3, 5]
    # Same start and end in a range
    solution.trade_ids = "5-5, 1"
    assert solution.get_trade_ids_list() == [1, 5]
    # Test unsorted input
    solution.trade_ids = "5, 1-3"
    assert solution.get_trade_ids_list() == [1, 2, 3, 5]
