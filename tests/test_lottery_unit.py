from scripts.helpful_scripts import (
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    get_account,
    fund_with_link,
    get_contract,
)
from brownie import network, exceptions
from scripts.deploy import deploy_lottery
from web3 import Web3
import pytest

# for testnet
# 1 eth = $ 4,504.25
# 0.011100627185436
# 11,100,627,185,436,000

# unit test: testing the smallest peices of code in an isolated environment/system(development netwoek)
# for testing independest functions in contract
# in unit test we hypothetically test all lines of code
# integration test: testing across multiple complex systems(testnet's)


def test_get_entrance_fee():
    print(network.show_active())
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    # arrange
    lottery = deploy_lottery()
    # act
    expected_fee = Web3.toWei(0.025, "ether")
    # as we testin on developmet network we deployed mock and put initial fee to $2000/1eth
    # hence 50/ 2000 = 0.025
    entrance_fee = lottery.getEntranceFee()
    # assert
    assert entrance_fee == expected_fee


def test_cant_enter_unless_started():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    #  arrange
    lottery = deploy_lottery()
    # act / assert
    with pytest.raises(exceptions.VirtualMachineError):
        lottery.enter({"from": get_account(), "value": lottery.getEntranceFee()})


def test_can_start_and_enter_lottery():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    # arrange
    lottery = deploy_lottery()
    account = get_account()
    # act
    tx_start_lottery = lottery.startLottery({"from": account})
    tx_start_lottery.wait(1)
    tx_enter_lottery = lottery.enter(
        {"from": account, "value": lottery.getEntranceFee() + 0.5}
    )
    tx_enter_lottery.wait(1)
    # assert
    assert lottery.players(0) == account


def test_can_end_lottery():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    # arrange
    lottery = deploy_lottery()
    account = get_account()
    # act
    tx_start_lottery = lottery.startLottery({"from": account})
    tx_start_lottery.wait(1)
    tx_enter_lottery = lottery.enter(
        {"from": account, "value": lottery.getEntranceFee() + 0.5}
    )
    tx_enter_lottery.wait(1)
    fund_with_link(lottery.address)
    tx_end_lottery = lottery.endLottery({"from": account})
    tx_end_lottery.wait(1)
    # assert
    assert lottery.lottery_state() == 2


def test_can_pick_winner_correctly():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    # arrange
    lottery = deploy_lottery()
    account = get_account()
    # act
    tx_start_lottery = lottery.startLottery({"from": account})
    tx_start_lottery.wait(1)
    # entering 3 players to lottery
    tx_enter_lottery1 = lottery.enter(
        {"from": account, "value": lottery.getEntranceFee() + 0.5}
    )
    tx_enter_lottery1.wait(1)
    tx_enter_lottery2 = lottery.enter(
        {"from": get_account(index=1), "value": lottery.getEntranceFee() + 0.5}
    )
    tx_enter_lottery2.wait(1)
    tx_enter_lottery3 = lottery.enter(
        {"from": get_account(index=2), "value": lottery.getEntranceFee() + 0.5}
    )
    tx_enter_lottery3.wait(1)

    fund_with_link(lottery.address)
    # calculating initial balances
    starting_balance_of_account0 = account.balance()
    contract_balacne = lottery.balance()

    tx_end = lottery.endLottery({"from": account})
    tx_end.wait(1)
    request_id = tx_end.events["RequestedRandomness"]["requestId"]
    # as we know when we end contract we call requestRandomness which returns randomness
    # now to actually get a random number vrfcoordinator calls fulFillRandomness
    # as we are on development network we have to pretend to be a chainlink node and call
    # callBackWithRandomness which calls rawFulFillRandomness which further call fulFillRandomness
    STATIC_RNG = 888
    # here account[0] will be the winner as 888 % 3=0
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, STATIC_RNG, lottery.address, {"from": account}
    )

    # assert
    assert lottery.recentWinner() == account
    assert lottery.balance() == 0
    assert account.balance() == starting_balance_of_account0 + contract_balacne
