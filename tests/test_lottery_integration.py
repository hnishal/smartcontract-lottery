from brownie import network
from scripts.deploy import deploy_lottery
from scripts.helpful_scripts import (
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    fund_with_link,
    get_account,
)
import pytest
import time


def test_can_pick_winner():
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_lottery()
    account = get_account()
    tx_start = lottery.startLottery({"from": account})
    tx_start.wait(1)
    tx_enter1 = lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    tx_enter1.wait(1)
    tx_enter2 = lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    tx_enter2.wait(1)
    fund_with_link(lottery.address)
    tx_end = lottery.endLottery({"from": account})
    tx_end.wait(1)
    time.sleep(180)
    assert lottery.balance() == 0
    assert lottery.recentWinner() == account.address
