"""AutoRole cog for Red-DiscordBot.

放入 cogs/autorole/autorole.py
"""
from __future__ import annotations

import asyncio
from typing import Optional

import discord
from redbot.core import commands, Config, checks

__author__ = "ConvertedFrom-KageRyo"
__version__ = "1.0.0"


class AutoRole(commands.Cog):
    """自動在新成員加入時指派身分組（Red cog 版本）。"""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=0x5f2b3c4d6a7e8f90)
        default_guild = {
            "enabled": False,
            "role_id": None,
            "role_name": None,
            "delay": 0,
            "dm_message": None,
            "restrict_guild": None,
        }
        self.config.register_guild(**default_guild)

    def _bot_member(self, guild: discord.Guild) -> Optional[discord.Member]:
        return guild.me or guild.get_member(self.bot.user.id)

    async def _find_role(self, guild: discord.Guild, data: dict) -> Optional[discord.Role]:
        role_id = data.get("role_id")
        role_name = data.get("role_name")
        if role_id:
            role = guild.get_role(role_id)
            if role:
                return role
        if role_name:
            for r in guild.roles:
                if r.name == role_name:
                    return r
        return None

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        guild = member.guild
        if guild is None:
            return
        data = await self.config.guild(guild).all()
        if not data.get("enabled"):
            return

        restrict = data.get("restrict_guild")
        if restrict and guild.id != restrict:
            return

        role = await self._find_role(guild, data)
        if role is None:
            return

        me = self._bot_member(guild)
        if me is None:
            return
        if not me.guild_permissions.manage_roles:
            return
        if role.position >= (me.top_role.position if me.top_role else 0):
            return

        delay = int(data.get("delay") or 0)
        if delay > 0:
            try:
                await asyncio.sleep(delay)
            except asyncio.CancelledError:
                return

        if role in member.roles:
            return

        try:
            await member.add_roles(role, reason="AutoRole: automatic role assignment")
        except Exception:
            return

        dm = data.get("dm_message")
        if dm:
            try:
                await member.send(
                    dm.format(guild=guild.name, member=member.name, mention=member.mention)
                )
            except Exception:
                pass

    @commands.group()
    @checks.admin_or_permissions(manage_guild=True)
    @commands.guild_only()
    async def autorole(self, ctx: commands.Context):
        """Autorole 設定群組。"""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @autorole.command(name="set")
    async def set_role(self, ctx: commands.Context, role: discord.Role):
        """設定要自動指派的身分組（使用 mention 或 ID）。"""
        await self.config.guild(ctx.guild).role_id.set(role.id)
        await self.config.guild(ctx.guild).role_name.set(None)
        await ctx.send(f"已設定自動指派身分組為 **{role.name}**。")

    @autorole.command(name="setname")
    async def set_role_name(self, ctx: commands.Context, *, role_name: str):
        """用身分組名稱設定要自動指派的身分組（若重名請改用 ID）。"""
        await self.config.guild(ctx.guild).role_name.set(role_name)
        await self.config.guild(ctx.guild).role_id.set(None)
        await ctx.send(f"已設定以名稱搜尋身分組：**{role_name}**（請注意重名情況）。")

    @autorole.command(name="unset")
    async def unset_role(self, ctx: commands.Context):
        """清除已設定的身分組（role_id / role_name）。"""
        await self.config.guild(ctx.guild).role_id.set(None)
        await self.config.guild(ctx.guild).role_name.set(None)
        await ctx.send("已清除自動指派身分組設定。")

    @autorole.command()
    async def enable(self, ctx: commands.Context):
        """啟用自動指派。"""
        await self.config.guild(ctx.guild).enabled.set(True)
        await ctx.send("已啟用 AutoRole。")

    @autorole.command()
    async def disable(self, ctx: commands.Context):
        """停用自動指派。"""
        await self.config.guild(ctx.guild).enabled.set(False)
        await ctx.send("已停用 AutoRole。")

    @autorole.command()
    async def delay(self, ctx: commands.Context, seconds: int):
        """設定延遲（秒）在加入後才指派角色，預設 0。"""
        if seconds < 0:
            await ctx.send("延遲不能是負數。")
            return
        await self.config.guild(ctx.guild).delay.set(seconds)
        await ctx.send(f"已設定延遲為 {seconds} 秒。")

    @autorole.command()
    async def dm(self, ctx: commands.Context, *, message: Optional[str] = None):
        """設定在自動指派後要發送的私訊（可留空以清除）。
        支援佔位符：{guild}、{member}、{mention}"""
        await self.config.guild(ctx.guild).dm_message.set(message)
        if message:
            await ctx.send("已設定歡迎私訊。可使用 {guild}、{member}、{mention} 佔位符。")
        else:
            await ctx.send("已清除歡迎私訊設定。")

    @autorole.command()
    async def show(self, ctx: commands.Context):
        """顯示目前設定。"""
        data = await self.config.guild(ctx.guild).all()
        role = None
        if data.get("role_id"):
            role = ctx.guild.get_role(data.get("role_id"))
        enabled = data.get("enabled", False)
        delay = data.get("delay", 0)
        dm = data.get("dm_message")
        role_name = data.get("role_name") or "未設定"
        role_desc = role.name if role else role_name
        em = (
            f"已啟用: {enabled}\n"
            f"身分組: {role_desc}\n"
            f"延遲: {delay} 秒\n"
            f"DM 訊息: {dm if dm else '未設定'}"
        )
        await ctx.send(em)

    @autorole.command()
    async def test(self, ctx: commands.Context, member: Optional[discord.Member] = None):
        """測試指派（會暫時給予並移除該身分組以驗證權限）。"""
        member = member or ctx.author
        data = await self.config.guild(ctx.guild).all()
        role = None
        if data.get("role_id"):
            role = ctx.guild.get_role(data.get("role_id"))
        elif data.get("role_name"):
            for r in ctx.guild.roles:
                if r.name == data.get("role_name"):
                    role = r
                    break
        if role is None:
            await ctx.send("尚未設定身分組或在此伺服器找不到設定的身分組。")
            return

        me = self._bot_member(ctx.guild)
        if me is None or not me.guild_permissions.manage_roles:
            await ctx.send("機器人沒有管理身分組的權限。")
            return
        if role.position >= (me.top_role.position if me.top_role else 0):
            await ctx.send("機器人的角色階層不足以指派該身分組。")
            return

        try:
            await member.add_roles(role, reason="AutoRole test")
            await asyncio.sleep(1)
            await member.remove_roles(role, reason="AutoRole test")
        except Exception as e:
            await ctx.send(f"測試失敗：{e}")
        else:
            await ctx.send("測試成功：已成功指派並移除該身分組。")

    @autorole.command()
    async def reset(self, ctx: commands.Context):
        """重置並刪除此伺服器所有 autorole 設定。"""
        await self.config.guild(ctx.guild).clear()
        await ctx.send("已重置此伺服器的 AutoRole 設定。")


async def setup(bot):
    await bot.add_cog(AutoRole(bot))
