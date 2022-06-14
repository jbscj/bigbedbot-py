import asyncio

from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.model import Group, Member
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.message import GroupMessage
from graia.broadcast.exceptions import ExecutionStop
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import (
    Twilight,
    FullMatch,
    RegexResult,
    WildcardMatch,
)

from libs.control import Permission

channel = Channel.current()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([FullMatch("开启"), "anything" @ WildcardMatch()])]
    )
)
async def main(app: Ariadne, member: Member, group: Group, anything: RegexResult):

    if anything.matched:
        msg = anything.result.display
        try:
            cmd = Permission.get_corresponding_cmd(msg)
        except:
            raise ExecutionStop()
        
        try: 
            Permission.user_permission_check(member, Permission.MASTER)
        except Exception as e :
            await app.send_group_message(
                group,
                MessageChain(f"只有bot拥有者才能开关功能哦")
            )
            raise ExecutionStop()

        Permission.change_group_permission(group, cmd, True)
        await app.send_group_message(
            group,
            MessageChain(f"成功在群{group.id}开启：{msg}")
        )