from brownie import (
    accounts,
    network,
    config,
    MockV3Aggregator,
    VRFCoordinatorMock,
    LinkToken,
    Contract,
    interface,
)
from web3 import Web3

LOCAL_BLOCKCHAIN_ENVIRONMENTS = ["development", "ganache-local"]
MAINNET_FORKS = ["mainnet-fork", "mainnet-fork-dev"]

DECIMALS = 8
STARTNIG_PRICE = 200000000000


def get_account(index=None, id=None):
    if index:
        return accounts[index]
    if id:
        return accounts.load(id)
    if (
        network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS
        or network.show_active() in MAINNET_FORKS
    ):
        return accounts[0]

    return accounts.add(config["wallets"]["from_key"])


def deploy_mocks(decimals=DECIMALS, initial_value=STARTNIG_PRICE):
    account = get_account()
    MockV3Aggregator.deploy(decimals, initial_value, {"from": account})
    link_token = LinkToken.deploy({"from": account})
    VRFCoordinatorMock.deploy(link_token.address, {"from": account})
    print("Mocks Deployed")


contract_to_mock = {
    "vrf_coordinator": VRFCoordinatorMock,
    "eth_usd_price_feed": MockV3Aggregator,
    "link_token": LinkToken,
}


def get_contract(contract_name):
    """This function will grab the contract addresses from the brownie config
    if defined, otherwise, it will deploy a mock version of that contract, and
    return that mock contract.
        Args:
            contract_name (string)
        Returns:
            brownie.network.contract.ProjectContract: The most recently deployed
            version of this contract.
    """
    contract_type = contract_to_mock[contract_name]
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        if len(contract_type) <= 0:
            # MockV3Aggreagator.length
            deploy_mocks()
        # MockV3Aggreagator[-1]
        contract = contract_type[-1]
    else:
        contract_address = config["networks"][network.show_active()][contract_type]
        contract = Contract.from_abi(
            contract_type._name, contract_address, contract_type.abi
        )

    return contract


def fund_with_link(
    contract_adress, account=None, link_token=None, amount=100000000000000000
):  # 0.1 LINK
    account = account if account else get_account()
    link_token = link_token if link_token else get_contract("link_token")
    tx = link_token.transfer(contract_adress, amount, {"from": account})
    # instead using interface to tansfer funds and create contract
    # way to interactwith contract that already exist
    # link_toke_contract = interface.LinkTokenIterface(
    #     link_token.address,
    # )
    # tx = link_toke_contract.transfer(contract_adress, amount, {"from": account})
    tx.wait(1)
    print("Fund Contract!")
    return tx
