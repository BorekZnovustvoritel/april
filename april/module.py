import asyncio

import discord
from random import randint
from discord.ext import commands

from pie import check, i18n, logger, utils
from .database import AprilConfig, Nicknames

_ = i18n.Translator("modules/april").translate
guild_log = logger.Guild.logger()


class April(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @staticmethod
    def _generate_hex() -> str:
        symbols = "0123456789abcdef"
        ans = ""
        for _ in range(6):
            ans += symbols[randint(0, len(symbols) - 1)]
        return ans

    @commands.guild_only()
    @check.acl2(check.ACLevel.MOD)
    @commands.group(name="april")
    async def april(self, ctx):
        """April fools."""
        await utils.discord.send_help(ctx)

    @commands.guild_only()
    @check.acl2(check.ACLevel.MOD)
    @april.command(name="add")
    async def april_add(
        self, ctx, old_role: discord.Role, new_role: discord.Role = None
    ):
        """Add role configuration.
        old_role: MOD-TEAM role, new_role: role to simulate the old role. If not specified, one will be created."""
        to_be_deleted = False
        if not new_role:
            new_role = await ctx.guild.create_role(
                name=f"BETTER {old_role.name}", color=old_role.color
            )
            to_be_deleted = True
        """Add a MOD TEAM role."""
        AprilConfig.add(ctx.guild, old_role, new_role, to_be_deleted)
        await ctx.reply(_(ctx, "Yup."))

    @commands.guild_only()
    @check.acl2(check.ACLevel.MOD)
    @april.command(name="remove")
    async def april_remove(self, ctx, role: discord.Role):
        """Remove role from config"""
        AprilConfig.remove(ctx.guild, role.id)
        await ctx.reply(_(ctx, "Done that."))

    @commands.guild_only()
    @check.acl2(check.ACLevel.SUBMOD)
    @april.command(name="list")
    async def april_list(self, ctx):
        """List server config and the list of roles"""
        res = AprilConfig.get_all(ctx.guild)

        class Item:
            def __init__(self, old_role, new_role):
                self.old_role = old_role
                self.new_role = new_role

        active = (
            _(ctx, "Active") if Nicknames.get_all(ctx.guild) else _(ctx, "Inactive")
        )
        items = [Item(_(ctx, "Server"), active)]
        for conf in res:
            i = Item(
                getattr(ctx.guild.get_role(conf.role_id), "name", conf.role_id),
                getattr(ctx.guild.get_role(conf.new_role_id), "name", conf.new_role_id),
            )
            items.append(i)
        table = utils.text.create_table(
            items,
            header={"old_role": _(ctx, "Old role"), "new_role": _(ctx, "New role")},
        )
        for page in table:
            await ctx.send("```" + page + "```")

    @commands.guild_only()
    @check.acl2(check.ACLevel.MOD)
    @april.command(name="start")
    async def april_start(self, ctx):
        """Let's do it."""
        nicks = list(Nicknames.get_all(ctx.guild))
        if len(nicks) > 0:
            await ctx.reply(_(ctx, "Already running, bruh."))
            return
        res = AprilConfig.get_all(ctx.guild)
        if not res:
            await ctx.reply(_(ctx, "Nothing is configured."))
            return
        roles = [ctx.guild.get_role(c.role_id) for c in res]
        lowest_role = min(r.position for r in roles if r)
        pos_for_new_roles = max(0, lowest_role)
        for role in roles:
            for member in role.members:
                Nicknames.add(member, ctx.guild)
                try:
                    await member.edit(nick=f"Deleted user {April._generate_hex()}")
                except Exception as e:
                    await ctx.reply(
                        _(ctx, "Cannot edit {username}'s nickname.").format(
                            username=member.display_name
                        )
                    )
        new_roles = [ctx.guild.get_role(c.new_role_id) for c in res]
        new_roles = [r for r in new_roles if r]
        positions = dict()
        for role in new_roles:
            positions.update({role: pos_for_new_roles})
        await ctx.guild.edit_role_positions(positions)
        await ctx.reply(_(ctx, "Let's goo!"))

    @commands.guild_only()
    @check.acl2(check.ACLevel.MOD)
    @april.command(name="stop")
    async def april_stop(self, ctx):
        """Enough is enough."""
        role_configs = AprilConfig.get_all(ctx.guild)
        roles_to_be_deleted = filter(lambda x: x.to_be_deleted, role_configs)
        for role_conf in roles_to_be_deleted:
            role = ctx.guild.get_role(role_conf.new_role_id)
            if not role:
                continue
            try:
                await role.delete()
                AprilConfig.remove(ctx.guild, role_conf.role_id)
            except Exception:
                await ctx.reply(
                    _(ctx, "I had some problems deleting the role {role}.").format(
                        role=role
                    )
                )
        other_roles = filter(lambda x: not x.to_be_deleted, role_configs)
        for role_conf in other_roles:
            role = ctx.guild.get_role(role_conf.new_role_id)
            if not role:
                continue
            for member in role.members:
                try:
                    await member.remove_roles(role)
                    await asyncio.sleep(0.02)  # To prevent rate limiting
                except Exception:
                    await ctx.reply(
                        _(
                            ctx,
                            "I had some problems unassigning role {role} from user {member}",
                        ).format(role=role, member=member.display_name)
                    )
        nicks = Nicknames.get_all(ctx.guild)
        for nick in nicks:
            member = await ctx.guild.fetch_member(nick.user_id)
            if not member:
                continue
            try:
                await member.edit(nick=nick.old_nickname)
            except Exception:
                await ctx.reply(
                    _(ctx, "Cannot edit {username}'s nickname.").format(
                        username=member.display_name
                    )
                )
        Nicknames.delete_all(ctx.guild)
        await ctx.reply(_(ctx, "Bye bye."))

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if isinstance(message.channel, discord.abc.PrivateChannel):
            return
        nicks = Nicknames.get_all(message.guild)
        if not nicks:
            return
        for nick in nicks:
            if message.author.id == nick.user_id:
                return
        cfg = AprilConfig.get_all(message.guild)
        ids_to_give = set(r.new_role_id for r in cfg)
        for role in message.author.roles:
            if role.id in ids_to_give:
                return
        ids_to_give = list(ids_to_give)
        picked_role = message.guild.get_role(
            ids_to_give[randint(0, len(ids_to_give) - 1)]
        )
        ctx = i18n.TranslationContext(
            guild_id=message.guild.id, user_id=message.author.id
        )
        answers = [
            _(ctx, "MODs are dead. Long live the {rolename}s.").format(
                rolename=picked_role.name
            ),
            _(ctx, "Hi, old mods are gone. Please help me to carry this server."),
            _(ctx, "What if I gave you a {rolename} role? JK, JK... Unless..?").format(
                rolename=picked_role.name
            ),
            _(ctx, "Ban them all pliz."),
            _(ctx, "You have much power here!"),
            _(ctx, "||Sorry...||"),
            _(ctx, "You just got a {rolename} role. Bad for you").format(
                rolename=picked_role.name
            ),
            _(
                ctx,
                "Hi, this is General MET and you have been drafted. Accept your '{rolename}'.",
            ).format(rolename=picked_role.name),
            _(ctx, "Literally 1984."),
            _(
                ctx,
                "Actually I don't know anymore. Just take the L ({rolename}) and leave.",
            ).format(rolename=picked_role.name),
            _(ctx, "I would not want to be you..."),
            _(ctx, "It is April the 1st, my dudes."),
            _(ctx, "The grumpy old MODs resigned. Please substitute them."),
            _(ctx, "Reject being a pleb, embrace {rolename}").format(
                rolename=picked_role.name
            ),
            _(
                ctx,
                "You have my sword, my bow and my banhammer. Actually no. The last one I will keep for myself.",
            ),
            _(
                ctx, "Congratulations! Your role is: {rolename}. Oh. My condolences."
            ).format(rolename=picked_role.name),
            _(ctx, "Are we happy?"),
            _(
                ctx,
                "The offensive was successful and the MET army took over FEKT and this server. Glory to the General MET. :generalMET:",
            ),
            _(ctx, "You too can become an ethical hacker."),
            _(ctx, "You cannot make mistake here."),
        ]
        picked_ans = answers[randint(0, len(answers) - 1)]
        await message.author.add_roles(
            picked_role,
        )
        await message.reply(picked_ans)


async def setup(bot) -> None:
    await bot.add_cog(April(bot))
