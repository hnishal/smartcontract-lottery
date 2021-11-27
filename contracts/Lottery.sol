//SPDX-License-Identifier: MIT
pragma solidity ^0.6.6;

import "@chainlink/contracts/src/v0.6/interfaces/AggregatorV3Interface.sol";
import "@chainlink/contracts/src/v0.6/VRFConsumerBase.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract Lottery is Ownable, VRFConsumerBase {
    address payable[] public players;
    address payable public recentWinner;
    uint256 public randomness;
    uint256 public usdEntryFee;
    AggregatorV3Interface internal ethUsdPriceFee;
    enum LOTTERY_STATE {
        OPEN,
        CLOSED,
        CALCULATING_WINNER
    }
    LOTTERY_STATE public lottery_state;
    uint256 public fee;
    bytes32 public keyHash;
    event RequestedRandomness(bytes32 requestId);

    constructor(
        address _priceFeedAddress,
        address _vrfCoordinator,
        address _link,
        uint256 _fee,
        bytes32 _keyHash
    ) public VRFConsumerBase(_vrfCoordinator, _link) {
        usdEntryFee = 50 * (10**18);
        ethUsdPriceFee = AggregatorV3Interface(_priceFeedAddress);
        lottery_state = LOTTERY_STATE.CLOSED;
        fee = _fee;
        keyHash = keyHash;
    }

    function enter() public payable {
        //50$ minimum fee
        require(lottery_state == LOTTERY_STATE.OPEN);
        require(msg.value >= getEntranceFee(), "Not Enough Ether");
        players.push(msg.sender);
    }

    function getEntranceFee() public view returns (uint256) {
        (, int256 price, , , ) = ethUsdPriceFee.latestRoundData();
        /*for example we need to convert $50 to eth at rate 1eth= $2000
        so we would do, requiredfee = 50/2000
        but solidity dosent support decimcal divsion 
        so we have to multiply with a big number, e.g. -
        50 *100000 /2000*/
        uint256 adjustePrice = uint256(price) * 10**10;
        uint256 costToEnter = (usdEntryFee * 10**18) / adjustePrice;
        //as we using older versionsolidity we should use safmath function if we wish to deploy this
        return costToEnter;
    }

    function startLottery() public onlyOwner {
        require(
            lottery_state == LOTTERY_STATE.CLOSED,
            "Can't start a new Lottery"
        );
        lottery_state = LOTTERY_STATE.OPEN;
    }

    function endLottery() public onlyOwner {
        // require(
        //     lottery_state == LOTTERY_STATE.OPEN,
        //     "Oops!.  Lottery already ended"
        // );

        // the insecure way to get random number(pseudo number)
        // hashing globally varibales
        //using block.difficulty block.timestamp
        /*uint256 pseudoRand = keccak256(
            abi.encodePacked(
                nonce, //its is predictable (transaction number)
                msg.sender, // msg.sender also predictable
                block.difficulty, //can be manipulated by miners
                block.timestamp //timestamp is easily predictable
            ) % players.length
        );*/
        // all this  predictable variable will make us vulnerable

        lottery_state = LOTTERY_STATE.CALCULATING_WINNER;
        bytes32 requestId = requestRandomness(keyHash, fee);
        emit RequestedRandomness(requestId);
    }

    function fulfillRandomness(bytes32 _requestId, uint256 _randomness)
        internal
        override
    {
        require(
            lottery_state == LOTTERY_STATE.CALCULATING_WINNER,
            "You arent there yet!..."
        );
        require(_randomness > 0, "randomness not found");
        uint256 indexofWinner = _randomness % players.length;

        recentWinner = players[indexofWinner];
        recentWinner.transfer(address(this).balance);
        players = new address payable[](0);
        lottery_state == LOTTERY_STATE.CLOSED;
        randomness = _randomness;
    }
}
