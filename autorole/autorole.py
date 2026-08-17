import asyncio
import discord
from redbot.core import commands, Config, checks

__author__ = "YourName"

class AutoRole(commands.Cog):
    """自動在新成員加入時指派身分組。"""

    def __init__(self, bot):
        self.bot = bot
        # 換成隨機長整數作為 identifier，確保不和其他 cog 衝突
        self.config = Config.get_conf(self, identifier=0xA1B2C3D4E5F60708)
        default_guild = {
            "enabled": False,
            "role_id": None,
            "delay": 0,
            "dm_message": None,
        }
        self.config.register_guild(**default_guild)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild = member.guild
        if guild is None:
            return
        data = await self.config.guild(guild).all()
        if not data.get("enabled"):
            return
        role_id = data.get("role_id")
        if not role_id:
            return
        role = guild.get_role(role_id)
        if role is None:
            return

        me = guild.me or guild.get_member(self.bot.user.id)
        # 確認機器人有權限
        if not me.guild_permissions.manage_roles:
            return
        # 確認機器人角色階層高於目標角色
        if role.position >= (me.top_role.position if me.top_role else 0):
            return
        # 等待延遲（如果有設定）
        delay = data.get("delay", 0) or 0
        if delay > 0:
            try:
                await asyncio.sleep(delay)
            except asyncio.CancelledError:
                return
        # 若成員已經有該角色則跳過
        if role in member.roles:
            return
        try:
            await member.add_roles(role, reason="AutoRole: automatic role assignment")
        except Exception:
            # 忽略失敗（例如權限不足或階層變動）
            pass

        # 可選的歡迎私訊（支援 {guild} 佔位符）
        dm = data.get("dm_message")
        if dm:
            try:
                await member.send(dm.format(guild=guild.name, member=member.name))
            except Exception:
                pass

    @commands.group()
    @checks.admin_or_permissions(manage_guild=True)
    @commands.guild_only()
    async def autorole(self, ctx: commands.Context):
        """Autorole 設定群組。"""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @autorole.command()
    async def set(self, ctx: commands.Context, role: discord.Role):
        """設定要自動指派的身分組。"""
        await self.config.guild(ctx.guild).role_id.set(role.id)
        await ctx.send(f"已設定自動指派身分組為 **{role.name}**。")

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
    async def dm(self, ctx: commands.Context, *, message: str = None):
        """設定在自動指派後要發送的私訊（可留空以清除）。支援 {guild} 與 {member} 佔位符。"""
        await self.config.guild(ctx.guild).dm_message.set(message)
        if message:
            await ctx.send("已設定歡迎私訊。可使用 {guild} 與 {member} 佔位符。")
        else:
            await ctx.send("已清除歡迎私訊設定。")

    @autorole.command()
    async def show(self, ctx: commands.Context):
        """顯示目前設定。"""
        data = await self.config.guild(ctx.guild).all()
        role = ctx.guild.get_role(data.get("role_id")) if data.get("role_id") else None
        enabled = data.get("enabled", False)
        delay = data.get("delay", 0)
        dm = data.get("dm_message")
        em = (
            f"已啟用: {enabled}\n"
            f"身分組: {role.name if role else '未設定'}\n"
            f"延遲: {delay} 秒\n"
            f"DM 訊息: {dm if dm else '未設定'}"
        )
        await ctx.send(em)

    @autorole.command()
    async def test(self, ctx: commands.Context, member: discord.Member = None):
        """測試指派（會暫時給予並移除該身分組以驗證權限）。"""
        member = member or ctx.author
        data = await self.config.guild(ctx.guild).all()
        role_id = data.get("role_id")
        if not role_id:
            await ctx.send("尚未設定身分組。")
            return
        role = ctx.guild.get_role(role_id)
        if role is None:
            await ctx.send("設定的身分組在此伺服器找不到。")
            return

        me = ctx.guild.me or ctx.guild.get_member(self.bot.user.id)
        if not me.guild_permissions.manage_roles:
            await ctx.send("機器人沒有管理身分組的權限。")
            return
        if role.position >= (me.top_role.position if me.top_role else 0):
            await ctx.send("機器人的角色階層不足以指派該身分組。")
            return

        try:
            await member.add_roles(role, reason="AutoRole test")
            await member.remove_roles(role, reason="AutoRole test")
        except Exception as e:
            await ctx.send(f"測試失敗：{e}")
        else:
            await ctx.send("測試成功：已成功指派並移除該身分組。")

def setup(bot):
    bot.add_cog(AutoRole(bot))
