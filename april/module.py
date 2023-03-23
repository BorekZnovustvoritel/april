import discord
from random import randint
from discord.ext import commands

from pie import check, i18n, logger, utils
from .database import AprilConfig, NewRoles, Nicknames

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
    async def april_add(self, ctx, role: discord.Role):
        AprilConfig.add(ctx.guild, role)
        await ctx.reply(_(ctx, "Yup."))

    @commands.guild_only()
    @check.acl2(check.ACLevel.MOD)
    @april.command(name="remove")
    async def april_add(self, ctx, role: discord.Role):
        AprilConfig.remove(ctx.guild, role)
        await ctx.reply(_(ctx, "Done that."))

    @commands.guild_only()
    @check.acl2(check.ACLevel.SUBMOD)
    @april.command(name="list")
    async def april_add(self, ctx):
        res = AprilConfig.get_all(ctx.guild)

        class Item:
            def __init__(self, role_name, role_id):
                self.role = role_name
                self.id = role_id
        active = _(ctx, "Yes") if Nicknames.get_all(ctx.guild) else _(ctx, "No")
        items = [Item(_(ctx, "Server"), active)]
        items.extend(Item(getattr(await ctx.guild.get_role(c.role_id), "name", c.role_id), c.role_id) for c in res)
        table = utils.text.create_table(items, header={"role": _(ctx, "Role"), "id": _(ctx, "ID")})
        for page in table:
            await ctx.send("```" + page + "```")

    @commands.guild_only()
    @check.acl2(check.ACLevel.MOD)
    @april.command(name="start")
    async def april_start(self, ctx):
        db_roles = NewRoles.get_all(ctx.guild)
        if len(db_roles) > 0:
            await ctx.reply(_(ctx, "Already running, bruh."))
            return
        res = AprilConfig.get_all(ctx.guild)
        roles = [ctx.guild.get_role(c.role_id) for c in res]
        for role in roles:
            for member in role.members:
                Nicknames.add(member, ctx.guild)
                try:
                    await member.edit(nick=f"Deleted user {April._generate_hex()}")
                except Exception:
                    ctx.reply(_(ctx, "Cannot edit {username}'s nickname.").format(username=member.display_name))
            new_role = await ctx.guild.create_role(name=f"BETTER {role.name}", color=role.color)
            NewRoles.add(ctx.guild, new_role)
        await ctx.reply(_(ctx, "Let's goo!"))

    @commands.guild_only()
    @check.acl2(check.ACLevel.MOD)
    @april.command(name="stop")
    async def april_stop(self, ctx):
        new_roles = [ctx.guild.get_role(r.id) for r in NewRoles.get_all(ctx.guild)]
        for role in new_roles:
            await role.delete()
        nicks = Nicknames.get_all(ctx.guild)
        for nick in nicks:
            member = await ctx.guild.fetch_member(nick.user_id)
            if not member:
                continue
            await member.edit(nick=nick.old_nickname)
        AprilConfig.deactivate(ctx.guild)
        NewRoles.nuke(ctx.guild)
        Nicknames.delete_all(ctx.guild)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        roles_to_give = NewRoles.get_all(message.guild)
        if not roles_to_give:
            return
        ids_to_give = set(r.role_id for r in roles_to_give)
        for role in message.author.roles:
            if role.id in ids_to_give:
                return
        ids_to_give = list(ids_to_give)
        ignored_users_conf = Nicknames.get_all(message.guild)
        ignored_users = set(message.guild.get_member(c.user_id) for c in ignored_users_conf)
        if message.author in ignored_users:
            return
        picked_role = message.guild.get_role(ids_to_give[randint(0, len(ids_to_give) - 1)])
        ctx = i18n.TranslationContext(guild_id=message.guild.id, user_id=message.author.id)
        answers = [_(ctx, "MODs are dead. Long live the {rolename}s.").format(rolename=picked_role.name),
                   _(ctx, "Hi, old mods are gone. Please help me to carry this server."),
                   _(ctx, "What if I gave you a {rolename} role? JK, JK... Unless..?").format(rolename=picked_role.name),
                   _(ctx, "Ban them all pliz."),
                   _(ctx, "You have much power here!"),
                   _(ctx, "||Sorry...||"),
                   _(ctx, "You just got a {rolename} role. Bad for you").format(rolename=picked_role.name),
                   _(ctx, "Hi, this is General MET and you have been drafted. Accept your '{rolename}'.").format(rolename=picked_role.name),
                   _(ctx, "Literally 1984."),
                   _(ctx, "Actually I don't know anymore. Just take the L ({rolename}) and leave.").format(rolename=picked_role.name),
                   _(ctx, "I would not want to be you..."),
                   _(ctx, "It is April the 1st, my dudes."),
                   _(ctx, "The grumpy old MODs resigned. Please substitute them."),
                   _(ctx, "Reject being a pleb, embrace {rolename}").format(rolename=picked_role.name),
                   _(ctx, "You have my sword, my bow and my banhammer. Actually no. The last one I will keep for myself."),
                   _(ctx, "Congratulations! Your role is: {rolename}. Oh. My condolences.").format(rolename=picked_role.name)]
        picked_ans = answers[randint(0, len(answers) - 1)]
        await message.author.add_roles(picked_role,)
        await message.reply(picked_ans)


