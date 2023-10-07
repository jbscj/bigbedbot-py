from collections import Counter
from math import ceil

from creart import create
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import RegexMatch, Twilight
from graia.ariadne.model import Group, Member
from graia.ariadne.message.element import At
from graia.broadcast.exceptions import ExecutionStop
from graia.broadcast.interrupt import InterruptControl
from graia.saya import Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema

from libs.control import Permission
from libs.helper.p import change_p, get_p
from libs.helper.random_chest import (
    chest_rewards,
    get_chest_opened_today,
    increment_chest_opened_today,
    total_p_requirement,
)
from libs.helper.rasin import change_rasin, get_rasin

inc = create(InterruptControl)

channel = Channel.current()

channel.name("random_chest_cmd")
channel.description("A Gacha System hommage to CSGO")
channel.author("Mikezom")

COLOR_TO_CN = {
    "blue": "蓝",
    "purple": "紫",
    "pink": "粉",
    "red": "红",
    "gold": "金",
    "black": "黑",
}

DEFAULT_PRICE = 20
BONUS_THRESHOLD = 30


# 开箱
@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([RegexMatch("开箱|抽卡")])],
        decorators=[
            Permission.require_group_perm(channel.meta["name"]),
            Permission.require_user_perm(Permission.USER),
        ],
    )
)
async def cmd_random_chest(app: Ariadne, member: Member, group: Group):
    user_p = get_p(member.id)
    user_rasin = get_rasin(member.id)

    user_chest_opened_today = get_chest_opened_today(member.id)
    if user_chest_opened_today < BONUS_THRESHOLD:
        user_price = ceil(DEFAULT_PRICE / 2)
    else:
        user_price = DEFAULT_PRICE

    if user_p < user_price:
        await app.send_group_message(group, MessageChain("你没批啦！"))
    elif user_rasin < 5:
        await app.send_group_message(group, MessageChain("你没体力啦！"))
    else:
        increment_chest_opened_today(member.id)
        [
            item_name,
            item_color,
            item_value,
        ] = chest_rewards.get_random_item()
        change_p(member.id, int(item_value) - user_price)
        change_rasin(member.id, -5)
        await app.send_message(
            group,
            MessageChain(
                At(member),
                f"你开到了{COLOR_TO_CN[item_color]}箱, {item_name},"
                f" 价值{item_value}批",
            ),
        )


# 开箱十连
@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([RegexMatch("抽卡十连|开箱十连")])],
        decorators=[
            Permission.require_group_perm(channel.meta["name"]),
            Permission.require_user_perm(Permission.USER),
        ],
    )
)
async def cmd_random_chest_times_ten(
    app: Ariadne, member: Member, group: Group
):
    user_p = get_p(member.id)
    user_rasin = get_rasin(member.id)
    user_total_p_required = total_p_requirement(
        member.id, 10, DEFAULT_PRICE, BONUS_THRESHOLD
    )
    if user_p < user_total_p_required:
        await app.send_group_message(group, MessageChain("你没批啦！"))
    elif user_rasin < 50:
        await app.send_group_message(group, MessageChain("你没有足够多的体力！"))
    else:
        items = []
        for _ in range(10):
            new_item = chest_rewards.get_random_item()
            items.append(new_item)

        total_value = sum([int(x[2]) for x in items])

        change_p(member.id, int(total_value) - user_total_p_required)
        change_rasin(member.id, -50)
        increment_chest_opened_today(member.id, 10)

        color_count = Counter([x[1] for x in items])
        if color_count["blue"] == 10:
            await app.send_message(
                group,
                MessageChain(
                    At(member), f"你抽到了10个垃圾, 一共就{total_value}p"
                ),
            )
        elif color_count["gold"] > 0:
            for _item_ in items:
                if _item_[1] == "gold":
                    gold_item = _item_
            await app.send_message(
                group,
                MessageChain(
                    At(member),
                    f"歪哟，发了！\n你开出了{gold_item[0]},"
                    f" 价值{gold_item[2]}批。一共你获得{total_value}批",
                ),
            )
        else:
            best_item = items[0]
            for _item_ in items:
                if int(_item_[2]) > int(best_item[2]):
                    best_item = _item_
            color_stats_string = ""
            for color in color_count:
                color_stats_string += (
                    f"{color_count[color]}个{COLOR_TO_CN[color]}箱，"
                )
            await app.send_message(
                group,
                MessageChain(
                    At(member),
                    f"你抽到了{color_stats_string} \n最贵的是{best_item[0]},"
                    f" 价值{best_item[2]}批。一共获得{total_value}批",
                ),
            )
