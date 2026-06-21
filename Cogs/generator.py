import discord
from discord import app_commands
from discord.ext import commands
from utils import checks
import os
import database

class GeneratorView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        # Standard Link Button added in __init__
        self.add_item(discord.ui.Button(
            label="Free Generator", 
            style=discord.ButtonStyle.link, 
            url="https://discord.com/channels/1472126918416531610/1472555127054405774", 
            emoji="<:links:1473568567290232945>"
        ))

    @discord.ui.button(label="Scan Live Stock", style=discord.ButtonStyle.primary, custom_id="scan_stock", emoji="<a:stock2:1473339178652663959>")
    async def scan_stock(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.response.defer(ephemeral=True)
            
            # Re-implement counting logic here to avoid dependency issues during interaction
            stock_root = "stock_files"
            categories = {
                "free": {
                    "emoji": "<:plants:1473339664424501417>",
                    "item_emoji": "<:iron:1473339698746490972>",
                    "title": "Free Generator"
                },
                "premium": {
                    "emoji": "<a:1427689167638499448:1473339630995902718>",
                    "item_emoji": "<:diamonds:1473339493456023683>",
                    "title": "Premium Generator"
                }
            }

            embed = discord.Embed(
                title="<a:stock2:1473339178652663959> Live Stock Status",
                description="Current unit availability in the **Yet Cloud** system.",
                color=0x3498db # Nice blue
            )

            for cat_key, config in categories.items():
                dir_path = os.path.join(stock_root, cat_key)
                total_units = 0
                items_text = ""
                
                if os.path.exists(dir_path):
                    files = [f for f in os.listdir(dir_path) if f.endswith(".txt")]
                    for f in sorted(files):
                        file_path = os.path.join(dir_path, f)
                        try:
                            with open(file_path, "r", encoding="utf-8") as file:
                                # Count only non-empty lines
                                count = len([line.strip() for line in file.readlines() if line.strip()])
                            total_units += count
                            items_text += f"● {f.replace('.txt', '').capitalize()}: {count} units\n"
                        except:
                            items_text += f"● {f.replace('.txt', '').capitalize()}: Error\n"
                
                if not items_text:
                    items_text = "No stock available."

                # Matching the image indentation and style
                cat_value = f"**❯ Total:** {total_units} units\n{items_text}"
                
                embed.add_field(
                    name=f"{config['emoji']} {config['title']}",
                    value=cat_value,
                    inline=True
                )

            # Footer matching the branding
            footer_text = f"[🔹] Yet Cloud | #1 Generator Server"
            embed.set_footer(text=footer_text, icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            print(f"Error in scan_stock: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message(f"An error occurred while scanning stock: `{e}`", ephemeral=True)
            else:
                await interaction.followup.send(f"An error occurred while scanning stock: `{e}`", ephemeral=True)

class Generator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.restock_channel_id = 1472555118800142420
        self.stock_log_channel_id = 1472555176584810641
        self.stock_root = "stock_files"

    def get_stock_count(self, category):
        dir_path = os.path.join(self.stock_root, category)
        if not os.path.exists(dir_path):
            return {}, 0
        
        counts = {}
        total = 0
        for filename in os.listdir(dir_path):
            if filename.endswith(".txt"):
                file_path = os.path.join(dir_path, filename)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        lines = [l.strip() for l in f.readlines() if l.strip()]
                        count = len(lines)
                        counts[filename.replace(".txt", "").capitalize()] = count
                        total += count
                except:
                    pass
        return counts, total

    @app_commands.command(name="restock", description="Post a restock announcement to the designated channel")
    @app_commands.choices(category=[
        app_commands.Choice(name="Free", value="free"),
        app_commands.Choice(name="Premium", value="premium")
    ])
    @app_commands.describe(
        category="The category that was restocked", 
        service_name="The specific service that was restocked (e.g. Minecraft)",
        file="Optional .txt file to upload/update the stock for this service"
    )
    @checks.is_owner_or_admin()
    async def restock(self, interaction: discord.Interaction, category: str = None, service_name: str = None, file: discord.Attachment = None):
        await interaction.response.defer(ephemeral=True)
        
        channel = self.bot.get_channel(self.restock_channel_id)
        if not channel:
            return await interaction.followup.send(f"Error: Could not find restock channel with ID `{self.restock_channel_id}`.", ephemeral=True)

        # Handle File Upload if provided
        if file:
            if not category or not service_name:
                return await interaction.followup.send("Please specify both `category` and `service_name` when uploading a stock file!", ephemeral=True)
            
            if not file.filename.endswith(".txt"):
                return await interaction.followup.send("Please upload only `.txt` files!", ephemeral=True)
            
            target_dir = os.path.join(self.stock_root, category)
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
            
            # Sanitize service name for filename
            clean_name = "".join(c for c in service_name if c.isalnum() or c in (" ", "-", "_")).strip().lower()
            target_path = os.path.join(target_dir, f"{clean_name}.txt")
            
            try:
                await file.save(target_path)
                
                # Get item count and category total
                with open(target_path, "r", encoding="utf-8") as f:
                    added_count = len([l.strip() for l in f.readlines() if l.strip()])
                
                _, cat_total = self.get_stock_count(category)

                # Log the addition (Professional Design)
                log_channel = self.bot.get_channel(self.stock_log_channel_id)
                if log_channel:
                    log_embed = discord.Embed(
                        title="📥 Inventory Update: Stock Added",
                        description="A service's inventory has been replenished.",
                        color=0x2ecc71, # Emerald Green
                        timestamp=discord.utils.utcnow()
                    )
                    log_embed.add_field(name="<a:staff1:1473339328246321282> **Authorized By:**", value=interaction.user.mention, inline=True)
                    log_embed.add_field(name="<:folder1:1472852636603531274> **Service Identity:**", value=f"{service_name.capitalize()} ({category.capitalize()})", inline=True)
                    log_embed.add_field(
                        name="<:box1:1472855146957754388> **Inventory Data:**", 
                        value=f"❯ Items Added: `{added_count}`\n❯ New Category Total: `{cat_total}`", 
                        inline=False
                    )
                    log_embed.add_field(name="<a:file2:1473340156948529193> **Source Control:**", value=f"`{clean_name}.txt`", inline=False)
                    
                    if interaction.guild.icon:
                        log_embed.set_thumbnail(url=interaction.guild.icon.url)
                    log_embed.set_footer(text="[🔹] Yet Cloud | Security & Audit System")
                    
                    await log_channel.send(embed=log_embed)
            except Exception as e:
                return await interaction.followup.send(f"Failed to save stock file: `{e}`", ephemeral=True)

        await interaction.response.defer(ephemeral=True)

        free_stock, free_total = self.get_stock_count("free")
        premium_stock, premium_total = self.get_stock_count("premium")

        # Determine Restock Message
        restock_msg = "The Generator Has Been Restocked!!"
        if service_name:
            restock_msg = f"{service_name.capitalize()} Has Been Restocked!!"
        elif category:
            restock_msg = f"The {category.capitalize()} Generator Has Been Restocked!!"

        # Ping and Title per image
        ping_role_id = 1472554999052636474
        ping_content = f"<@&{ping_role_id}> | **{restock_msg}**"
        
        embed = discord.Embed(
            title=f"**| {restock_msg} ** <a:bell:1472906474643787786>",
            description=f"System fully restocked! Generate accounts quickly before they're gone! <a:star2:1473340889982930985>",
            color=0x00FFFF
        )

        # Emoji mapping for specific services (if any)
        service_emojis = {}

        # Free Generator Column
        free_value = f"<:arrmor2:1473339428675256320> **Total Units:** {free_total}\n"
        if free_stock:
            for name, count in free_stock.items():
                emoji = service_emojis.get(name, "<:iron:1473339698746490972>")
                free_value += f"{emoji} {name}: {count} units\n"
        else:
            free_value += "No stock available."

        embed.add_field(
            name="<:plants:1473339664424501417> Free Generator",
            value=free_value,
            inline=True
        )

        # Premium Generator Column
        premium_value = f"<:arrmor2:1473339428675256320> **Total Units:** {premium_total}\n"
        if premium_stock:
            for name, count in premium_stock.items():
                emoji = service_emojis.get(name, "<:diamonds:1473339493456023683>")
                premium_value += f"{emoji} {name}: {count} units\n"
        else:
            premium_value += "No stock available."

        embed.add_field(
            name="<a:1427689167638499448:1473339630995902718> Premium Generator",
            value=premium_value,
            inline=True
        )

        # Thumbnail and Footer
        if interaction.guild.icon:
            embed.set_thumbnail(url=interaction.guild.icon.url)
        
        embed.set_footer(
            text="[🔹] Yet Cloud | #1 Generator Server",
            icon_url=interaction.guild.icon.url if interaction.guild.icon else None
        )

        view = GeneratorView(self.bot)
        await channel.send(content=ping_content, embed=embed, view=view)
        
        await interaction.followup.send(f"Restock announcement sent to {channel.mention}!", ephemeral=True)

    @app_commands.command(name="remove_stock", description="Remove a specific service and its stock file from a category")
    @app_commands.choices(category=[
        app_commands.Choice(name="Free", value="free"),
        app_commands.Choice(name="Premium", value="premium")
    ])
    @app_commands.describe(
        category="The category to remove the stock from", 
        service_name="The name of the service to remove (e.g. Minecraft)"
    )
    @checks.is_owner_or_admin()
    async def remove_stock(self, interaction: discord.Interaction, category: str, service_name: str):
        # Sanitize service name for filename
        clean_name = "".join(c for c in service_name if c.isalnum() or c in (" ", "-", "_")).strip().lower()
        target_path = os.path.join(self.stock_root, category, f"{clean_name}.txt")
        
        if os.path.exists(target_path):
            try:
                os.remove(target_path)
                
                # Get remaining total
                _, remaining_total = self.get_stock_count(category)

                # Log the removal (Professional Design)
                log_channel = self.bot.get_channel(self.stock_log_channel_id)
                if log_channel:
                    log_embed = discord.Embed(
                        title="📤 Inventory Update: Service Removed",
                        description="A service has been permanently removed from the system.",
                        color=0xe74c3c, # Alizarin Red
                        timestamp=discord.utils.utcnow()
                    )
                    log_embed.add_field(name="<a:staff1:1473339328246321282> **Authorized By:**", value=interaction.user.mention, inline=True)
                    log_embed.add_field(name="<:folder1:1472852636603531274> **Service Identity:**", value=f"{service_name.capitalize()} ({category.capitalize()})", inline=True)
                    log_embed.add_field(
                        name="<:box1:1472855146957754388> **Inventory Impact:**", 
                        value=f"❯ Remaining Category Stock: `{remaining_total}` items", 
                        inline=False
                    )
                    
                    if interaction.guild.icon:
                        log_embed.set_thumbnail(url=interaction.guild.icon.url)
                    log_embed.set_footer(text="[🔹] Yet Cloud | Security & Audit System")
                    
                    await log_channel.send(embed=log_embed)

                embed = discord.Embed(
                    title="✅ Service Removed",
                    description=f"Successfully removed **{service_name.capitalize()}** from the **{category.capitalize()}** generator.",
                    color=0x00FF00
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
            except Exception as e:
                await interaction.response.send_message(f"Failed to remove stock file: `{e}`", ephemeral=True)
        else:
            await interaction.response.send_message(f"Could not find a service named `{service_name}` in the `{category}` category.", ephemeral=True)

    @app_commands.command(name="generator", description="Setup the professional generator interface")
    @checks.is_owner_or_admin()
    async def setup_generator(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="<a:star2:1473340889982930985> Welcome to Yet Cloud Generator <a:star2:1473340889982930985>",
            description=(
                "<a:arrow:1472906559024664750> **Unlock a World of Services!** <a:arrow:1472906559024664750>\n\n"
                "<a:gift:1472852654471512145> **Free Generator:** Access a variety of free accounts with ease! Perfect for casual users looking to explore.\n"
                "<:diamonds:1473339493456023683> **Premium Generator:** Dive into exclusive premium accounts for a top-tier experience.\n"
                "<a:stock2:1473339178652663959> **View Stock:** Check the current stock levels of free and premium services."
            ),
            color=0x00FFFF
        )
        
        embed.add_field(
            name="💡 How to Use:", 
            value="Select an option below to proceed. Ensure your DMs are enabled to receive credentials!", 
            inline=False
        )
        embed.add_field(
            name="📸 Vouch Reminder:", 
            value="Vouch in <#1472555127054405774> within 10 minutes to avoid a 1-hour ban!", 
            inline=False
        )
        
        if interaction.guild.icon:
            embed.set_thumbnail(url=interaction.guild.icon.url)
        
        embed.set_footer(
            text="[🔹] Yet Cloud | #1 Generator Server",
            icon_url=interaction.guild.icon.url if interaction.guild.icon else None
        )
        
        view = GeneratorSetupView(self.bot)
        await interaction.response.send_message(embed=embed, view=view)

class GeneratorSelect(discord.ui.Select):
    def __init__(self, bot):
        self.bot = bot
        options = [
            discord.SelectOption(
                label="Free Generator", 
                description="Access our collection of free services", 
                emoji="<a:gift:1472852654471512145>", 
                value="free"
            ),
            discord.SelectOption(
                label="Premium Generator", 
                description="Access exclusive high-tier accounts", 
                emoji="<:diamonds:1473339493456023683>", 
                value="premium"
            ),
            discord.SelectOption(
                label="View Stock", 
                description="Check current availability of all services", 
                emoji="<a:stock2:1473339178652663959>", 
                value="stock"
            )
        ]
        super().__init__(
            placeholder="💪 | Select Generator Type (Free: | Premium)", 
            min_values=1, 
            max_values=1, 
            options=options,
            custom_id="gen_select"
        )

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "stock":
            # Re-use existing scan stock logic
            await GeneratorView(self.bot).scan_stock(interaction, None)
        elif self.values[0] == "free":
            # Role Check
            supporter_role_id = 1472554985483931648
            get_role_channel_id = 1472555117369622620
            
            member = interaction.guild.get_member(interaction.user.id)
            if not member or not any(role.id == supporter_role_id for role in member.roles):
                embed = discord.Embed(
                    title="🚫 You need the Supporter role to use the free generator! 👑",
                    description=f"### Get It In <#{get_role_channel_id}>\n\n🚫 **Access Denied**",
                    color=0xFF0000
                )
                if interaction.guild.icon:
                    embed.set_author(name=f"{interaction.guild.name} Ultimate Generator", icon_url=interaction.guild.icon.url)
                
                embed.set_footer(
                    text="[🔹] Yet Cloud | #1 Generator Server",
                    icon_url=interaction.guild.icon.url if interaction.guild.icon else None
                )
                return await interaction.response.send_message(embed=embed, ephemeral=True)

            await interaction.response.defer(ephemeral=True)
            
            # Create the Free Selection Embed
            embed = discord.Embed(
                title="<a:gift:1472852654471512145> Free Service Selection",
                description=(
                    "<a:arrow:1472906559024664750> **Welcome to the Free Generator!** <a:arrow:1472906559024664750>\n\n"
                    "<a:gift:1472852654471512145> Select a service from the dropdown to receive your credentials!\n"
                    "👀 Your credentials will be sent via DM. Ensure your DMs are enabled!"
                ),
                color=0x00FFFF
            )
            
            embed.set_author(name=f"{interaction.guild.name} Ultimate Generator", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
            
            embed.add_field(
                name="💡 Tip:", 
                value="Vouch in <#1472555127054405774> within 10 minutes to avoid a 1-hour ban!", 
                inline=False
            )
            
            if interaction.guild.icon:
                embed.set_thumbnail(url=interaction.guild.icon.url)
            
            embed.set_footer(
                text="[🔹] Yet Cloud | #1 Generator Server",
                icon_url=interaction.guild.icon.url if interaction.guild.icon else None
            )
            
            view = FreeGeneratorView(self.bot)
            if not view.select_ready:
                return await interaction.followup.send("No free services are currently available. Please check back later!", ephemeral=True)
                
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
        elif self.values[0] == "premium":
            embed = discord.Embed(
                title="<:diamonds:1473339493456023683> Premium Generator Access",
                description=(
                    "You have selected the **Premium Network**. Access to these high-tier assets is restricted to authorized subscribers.\n\n"
                    "👑 **How to Access:**\n"
                    "1. Purchase a subscription in <#1472555117369622620>\n"
                    "2. Open a ticket to verify your transaction.\n"
                    "3. Enjoy unlimited premium generation!"
                ),
                color=0x00FFFF
            )
            embed.set_footer(text="[🔹] Yet Cloud | Elite Tier")
            await interaction.response.send_message(embed=embed, ephemeral=True)

class FreeGeneratorSelect(discord.ui.Select):
    def __init__(self, bot):
        self.bot = bot
        options = []
        
        # Dynamically load options from stock_files/free
        stock_dir = "stock_files/free"
        if os.path.exists(stock_dir):
            for filename in sorted(os.listdir(stock_dir)):
                if filename.endswith(".txt"):
                    name = filename.replace(".txt", "").capitalize()
                    # Check stock count
                    count = 0
                    try:
                        with open(os.path.join(stock_dir, filename), "r", encoding="utf-8") as f:
                            count = len([l.strip() for l in f.readlines() if l.strip()])
                    except:
                        pass
                    
                    options.append(discord.SelectOption(
                        label=name,
                        description=f"Available Units: {count}",
                        emoji="<a:gift:1472852654471512145>",
                        value=filename
                    ))
        
        if not options:
            options.append(discord.SelectOption(label="No services available", value="none"))
            self.disabled = True
            self.select_ready = False
        else:
            self.select_ready = True

        super().__init__(
            placeholder="🧤 | Select a Free Service",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="free_select"
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        filename = self.values[0]
        service_name = filename.replace(".txt", "").upper()
        stock_file = os.path.join("stock_files/free", filename)

        if not os.path.exists(stock_file):
            error_embed = discord.Embed(title="❌ Error", description=f"The service **{service_name}** is currently out of stock.", color=0xFF0000)
            return await interaction.followup.send(embed=error_embed, ephemeral=True)

        try:
            with open(stock_file, "r", encoding="utf-8") as f:
                lines = [l.strip() for l in f.readlines() if l.strip()]
            
            if not lines:
                error_embed = discord.Embed(title="❌ Error", description=f"The service **{service_name}** is currently out of stock.", color=0xFF0000)
                return await interaction.followup.send(embed=error_embed, ephemeral=True)

            account = lines.pop(0)
            
            # Update the stock file
            with open(stock_file, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))

            # Parse account
            if ":" in account:
                parts = account.split(":", 1)
                email = parts[0]
                password = parts[1]
            else:
                email = account
                password = "N/A"

            # Create Delivery Receipt Embed (Perfect Match to Reference Image)
            embed = discord.Embed(
                title="<a:star2:1473340889982930985> Yet Cloud Delivery Receipt",
                description=(
                    "✨ Thanks for using **Yet Cloud Free Services!** ✨\n\n"
                    f"Your **{service_name}** item has been generated successfully. 🥳\n"
                    "Below are your details:\n"
                    "**Account 1**"
                ),
                color=0x00FFFF,
                timestamp=discord.utils.utcnow()
            )
            
            # Format code block with exact spacing from image
            account_data = f"```\n[ Email    ] {email}\n[ Password ] {password}\n[ Full     ] {account}\n```"
            embed.add_field(name="\u200b", value=account_data, inline=False)
            
            vouch_channel_mention = "<#1472555127054405774>"
            embed.add_field(
                name="🏎️ Reminder",
                value=f"Please vouch in **Yet Cloud | #1 Generator Serv...** › <#1473339618035318784> · {vouch_channel_mention} within **10 minutes** or risk a **1-hour generator ban** 🚫",
                inline=False
            )
            
            embed.add_field(
                name="\u200b",
                value=f"🚨 If the account isn't working please use **/report** Command in the server",
                inline=False
            )

            if interaction.guild.icon:
                embed.set_thumbnail(url=interaction.guild.icon.url)
            
            embed.set_footer(
                text="[🔹] Yet Cloud | #1 Generator Server",
                icon_url=interaction.guild.icon.url if interaction.guild.icon else None
            )

            # Try to DM the user
            try:
                await interaction.user.send(embed=embed)
                # Log usage for leaderboard
                await database.log_generator_usage(interaction.user.id)
                # Public (ephemeral) confirmation
                success_embed = discord.Embed(title="✅ Delivery Successful", description="Your credentials have been securely transmitted to your DMs.", color=0x00FF00)
                await interaction.followup.send(embed=success_embed, ephemeral=True)
            except discord.Forbidden:
                # If DMs are closed, we should put the account back or handle it. 
                # To be safe, let's put it back at the top.
                lines.insert(0, account)
                with open(stock_file, "w", encoding="utf-8") as f:
                    f.write("\n".join(lines))
                error_embed = discord.Embed(
                    title="❌ Transmission Failed",
                    description="I couldn't send you a DM! Please enable your DMs in **User Settings > Privacy & Safety** and try again.",
                    color=0xFF0000
                )
                await interaction.followup.send(embed=error_embed, ephemeral=True)

        except Exception as e:
            print(f"Error in Free Generation callback: {e}")
            fail_embed = discord.Embed(title="❌ Critical System Error", description=f"An error occurred during account processing: `{e}`", color=0xFF0000)
            await interaction.followup.send(embed=fail_embed, ephemeral=True)

class FreeGeneratorView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        select = FreeGeneratorSelect(bot)
        self.add_item(select)
        self.select_ready = select.select_ready

class GeneratorSetupView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.add_item(GeneratorSelect(bot))

async def setup(bot):
    await bot.add_cog(Generator(bot))