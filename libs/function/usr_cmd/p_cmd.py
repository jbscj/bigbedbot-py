from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import At
from graia.ariadne.message.parser.twilight import (
    RegexMatch,
    Twilight,
    RegexResult,
)
from graia.ariadne.model import Group, Member
from graia.broadcast.exceptions import ExecutionStop
from graia.saya import Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema

from libs.control import Permission
from libs.helper.p import (
    change_daily_p_to_received,
    change_p,
    generate_daily_p,
    get_p,
    get_user_list,
    is_received_daily_p,
)
from libs.helper.rasin import get_rasin
from libs.helper.info import GlobalFunction

channel = Channel.current()

channel.name("p_cmd")
channel.description("Coin System for QQ Groups")
channel.author("Mikezom")


# 我的批
@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([RegexMatch("我的批|余额")])],
        decorators=[
            Permission.require_group_perm(channel.meta["name"]),
            Permission.require_user_perm(Permission.USER),
        ],
    )
)
async def cmd_find_p(app: Ariadne, member: Member, group: Group):
    my_rasin = get_rasin(member.id)
    my_p = get_p(member.id)
    await app.send_group_message(
        group,
        MessageChain(At(member), f" 你现在有 {my_p} 批, {my_rasin}/160 体力。"),
    )


# 领批
@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([RegexMatch("领批")])],
        decorators=[
            Permission.require_group_perm(channel.meta["name"]),
            Permission.require_user_perm(Permission.USER),
        ],
    )
)
async def cmd_receive_daily_p(
    app: Ariadne, member: Member, group: Group
):
    if is_received_daily_p(member.id):
        await app.send_group_message(group, MessageChain("你今天已经领过批啦！"))
    else:
        daily_p = generate_daily_p(member.id)
        change_p(member.id, daily_p)
        change_daily_p_to_received(member.id)
        my_rasin = get_rasin(member.id)

        await app.send_group_message(
            group,
            MessageChain(
                At(member),
                f" 你现在有 {get_p(member.id)}(+{daily_p}) 批,"
                f" {my_rasin}/160 体力。",
            ),
        )


# [Debug]重启每日领批
@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([RegexMatch("刷新每日批池")])],
        decorators=[
            Permission.require_group_perm(channel.meta["name"]),
            Permission.require_user_perm(Permission.MASTER),
        ],
    )
)
async def cmd_reset_has_received_daily_p(
    app: Ariadne, member: Member, group: Group
):
    GlobalFunction.reset_daily_p()
    await app.send_group_message(group, MessageChain("重启！"))


# [Debug]发批
@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight.from_command("/发批 {uid} {num}")],
        decorators=[
            Permission.require_group_perm(channel.meta["name"]),
            Permission.require_user_perm(Permission.MASTER),
        ],
    )
)
async def cmd_give_uid_p(
    app: Ariadne,
    member: Member,
    group: Group,
    uid: RegexResult,
    num: RegexResult,
):
    uid = int(uid.result.display)
    num = int(num.result.display)

    change_p(uid, num)

    await app.send_group_message(
        group, MessageChain(f"{uid}: {get_p(uid)}({+num})")
    )


# 批榜
@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([RegexMatch("批榜")])],
        decorators=[
            Permission.require_group_perm(channel.meta["name"]),
            Permission.require_user_perm(Permission.USER),
        ],
    )
)
async def cmd_p_ranking(app: Ariadne, member: Member, group: Group):
    user_list = get_user_list()
    member_list = await app.get_member_list(group)
    user_ranking = []
    for _member_ in member_list:
        if str(_member_.id) in user_list:
            user_ranking.append((_member_.id, get_p(_member_.id)))

    user_ranking.sort(key=lambda x: x[1], reverse=True)
    msg = ""
    for i, (uid, p_uid) in enumerate(user_ranking[:5]):
        _member_ = await app.get_member(group, uid)
        msg += f"{i+1}. {_member_.name} : {p_uid}\n"

    await app.send_group_message(group, MessageChain(f"你群批榜：\n{msg}"))
