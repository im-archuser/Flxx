import discord
from discord import app_commands
from discord.ext import commands
import os
from utils import checks

class Stock(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.stock_dir = "stock_files"

    @app_commands.command(name="stock", description="View all services currently available in the system")
    async def stock(self, interaction: discord.Interaction):
        if not os.path.exists(self.stock_dir):
            os.makedirs(self.stock_dir)
            return await interaction.response.send_message(f"the `{self.stock_dir}` directory was missing, so I created it! Please add your `.txt` stock files there.", ephemeral=True)

        files = [f for f in os.listdir(self.stock_dir) if f.endswith(".txt")]
        
        if not files:
            return await interaction.response.send_message(f"No stock files found in `{self.stock_dir}`. Please upload `.txt` files there.", ephemeral=True)

        embed = discord.Embed(
            title="<a:stock2:1473339178652663959> | YET Cloud Stock System",
            description="Available services and their current stock levels are listed below.",
            color=0x00FFFF
        )
        
        for filename in files:
            service_name = filename.replace(".txt", "").capitalize()
            file_path = os.path.join(self.stock_dir, filename)
            
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    # Filter out empty lines
                    lines = [line.strip() for line in f.readlines() if line.strip()]
                    count = len(lines)
                
                embed.add_field(
                    name=f"<:folder1:1472852636603531274> {service_name}",
                    value=f"<a:arrow:1472906559024664750> Total Stock: **{count}**",
                    inline=False
                )
            except Exception as e:
                embed.add_field(
                    name=f"❌ {service_name}",
                    value=f"Error reading file: `{e}`",
                    inline=False
                )

        embed.set_footer(text="YET Cloud Management", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="add_stock", description="Upload a .txt file to the stock inventory")
    @app_commands.describe(file="The .txt file to upload", service_name="Name for the service")
    @checks.is_owner_or_admin()
    async def add_stock(self, interaction: discord.Interaction, file: discord.Attachment, service_name: str = None):
        if not file.filename.endswith(".txt"):
            return await interaction.response.send_message("Please upload only `.txt` files!", ephemeral=True)
        
        if not os.path.exists(self.stock_dir):
            os.makedirs(self.stock_dir)
            
        final_name = service_name if service_name else file.filename.replace(".txt", "")
        # Sanitize name to prevent path traversal
        final_name = "".join(c for c in final_name if c.isalnum() or c in (" ", "-", "_")).strip()
        file_path = os.path.join(self.stock_dir, f"{final_name}.txt")
        
        try:
            await file.save(file_path)
            
            # Count lines for immediate feedback
            with open(file_path, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]
            count = len(lines)
            
            # Log the addition (Professional Design)
            log_channel_id = 1472555176584810641
            log_channel = self.bot.get_channel(log_channel_id)
            if log_channel:
                log_embed = discord.Embed(
                    title="📥 Inventory Update: Stock Added (General)",
                    description="A service's inventory has been replenished in the general stock folder.",
                    color=0x2ecc71, # Emerald Green
                    timestamp=discord.utils.utcnow()
                )
                log_embed.add_field(name="<a:staff1:1473339328246321282> **Authorized By:**", value=interaction.user.mention, inline=True)
                log_embed.add_field(name="<:folder1:1472852636603531274> **Service Identity:**", value=f"{final_name.capitalize()} (General)", inline=True)
                log_embed.add_field(
                    name="<:box1:1472855146957754388> **Inventory Data:**", 
                    value=f"❯ Items Added: `{count}`", 
                    inline=False
                )
                log_embed.add_field(name="<a:file2:1473340156948529193> **Source Control:**", value=f"`{final_name}.txt`", inline=False)
                
                if interaction.guild.icon:
                    log_embed.set_thumbnail(url=interaction.guild.icon.url)
                log_embed.set_footer(text="[🔹] YET Cloud | Security & Audit System")
                await log_channel.send(embed=log_embed)

            embed = discord.Embed(
                title="<:add:1473267423854592103> Stock Uploaded Successfully",
                description=f"Stock for **{final_name.capitalize()}** has been updated.",
                color=0x00FF00
            )
            embed.add_field(name="<:folder1:1472852636603531274> Service", value=f"`{final_name}.txt`", inline=True)
            embed.add_field(name="<:box1:1472855146957754388> Total Items", value=str(count), inline=True)
            embed.set_footer(text="YET Cloud Management")
            
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred while saving the file: `{e}`", ephemeral=True)

    @app_commands.command(name="create", description="Initialize a new service category")
    @app_commands.describe(name="The name of the service (e.g. netflix)")
    @checks.is_owner_or_admin()
    async def create_service(self, interaction: discord.Interaction, name: str):
        path = os.path.join(self.stock_dir, f"{name.lower()}.txt")
        if os.path.exists(path):
            embed = discord.Embed(title="❌ Error", description=f"The service category `{name}` already exists.", color=0xFF0000)
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        
        with open(path, "w") as f:
            pass # Create empty file
        
        embed = discord.Embed(
            title="<:folder1:1472852636603531274> Service Category Created",
            description=f"Successfully initialized the `{name.upper()}` service category.",
            color=0x00FFFF
        )
        embed.add_field(name="<:setting3:1473340356505083995> Location", value=f"`{path}`", inline=True)
        embed.set_footer(text="[🔹] Yet Cloud | Inventory Management")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="delete", description="Permanently remove a service category")
    @app_commands.describe(name="The name of the service to delete")
    @checks.is_owner_or_admin()
    async def delete_service(self, interaction: discord.Interaction, name: str):
        path = os.path.join(self.stock_dir, f"{name.lower()}.txt")
        if not os.path.exists(path):
            embed = discord.Embed(title="❌ Error", description=f"The service category `{name}` does not exist.", color=0xFF0000)
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        
        os.remove(path)
        embed = discord.Embed(
            title="<a:broom1:1473340809221472306> Service Category Deleted",
            description=f"The `{name.upper()}` category has been permanently purged from the system.",
            color=0x00FFFF
        )
        embed.set_footer(text="[🔹] Yet Cloud | Inventory Management")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="clear_stock", description="Wipe all accounts from a specific category")
    @app_commands.describe(category="The category to clear")
    @checks.is_owner_or_admin()
    async def clear_stock(self, interaction: discord.Interaction, category: str):
        path = os.path.join(self.stock_dir, f"{category.lower()}.txt")
        if not os.path.exists(path):
            embed = discord.Embed(title="❌ Error", description=f"Category `{category}` not found.", color=0xFF0000)
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        
        with open(path, "w") as f:
            pass # Truncate file
            
        embed = discord.Embed(
            title="<:remove:1473267385615122535> Stock Wiped",
            description=f"All inventory for `{category.upper()}` has been cleared.",
            color=0x00FFFF
        )
        embed.set_footer(text="[🔹] Yet Cloud | Maintenance")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="give", description="Issue specific accounts directly to a user")
    @app_commands.describe(user="Receiver", service="Service category", amount="Number of accounts")
    @checks.is_owner_or_admin()
    async def gift_accounts(self, interaction: discord.Interaction, user: discord.Member, service: str, amount: int):
        await interaction.response.defer(ephemeral=True)
        path = os.path.join(self.stock_dir, f"{service.lower()}.txt")
        
        if not os.path.exists(path):
            embed = discord.Embed(title="❌ Error", description=f"Service `{service}` not found.", color=0xFF0000)
            return await interaction.followup.send(embed=embed, ephemeral=True)
            
        with open(path, "r") as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]
            
        if len(lines) < amount:
            embed = discord.Embed(title="❌ Insufficient Stock", description=f"Only `{len(lines)}` accounts available.", color=0xFF0000)
            return await interaction.followup.send(embed=embed, ephemeral=True)
            
        gifted = lines[:amount]
        remaining = lines[amount:]
        
        with open(path, "w") as f:
            f.write("\n".join(remaining))
            
        # Send accounts to user DM
        try:
            gift_embed = discord.Embed(
                title="<:gift:1472852654471512145> YET Cloud — Direct Delivery",
                description=f"Admin {interaction.user.mention} has sent you `{amount}` accounts for **{service.upper()}**!",
                color=0x00FFFF
            )
            accounts_str = "\n".join(gifted)
            gift_embed.add_field(name="<a:note2:1473340536768004128> Credentials", value=f"```\n{accounts_str}\n```")
            gift_embed.set_footer(text="[🔹] Yet Cloud | Premium Network")
            await user.send(embed=gift_embed)
            
            # Confirmation to admin
            success_embed = discord.Embed(title="✅ Gifting Successful", description=f"Successfully sent `{amount}` units of `{service}` to {user.mention}.", color=0x00FF00)
            await interaction.followup.send(embed=success_embed, ephemeral=True)
        except:
            # Put back in stock if DM fails
            with open(path, "w") as f:
                f.write("\n".join(gifted + remaining))
            await interaction.followup.send("❌ **Error:** User has DMs closed. Transaction aborted and stock restored.", ephemeral=True)

    @app_commands.command(name="bupload_stock", description="Perform a bulk stock file upload")
    @checks.is_owner_or_admin()
    async def bulk_upload(self, interaction: discord.Interaction):
        await interaction.response.send_message("<a:file2:1473340156948529193> **Bulk Upload:** Starting multiple file ingestion process... (Stub)", ephemeral=True)

    @app_commands.command(name="bstock", description="View detailed bulk inventory statistics")
    @checks.is_owner_or_admin()
    async def bulk_stock(self, interaction: discord.Interaction):
        await interaction.response.send_message("<:box1:1472855146957754388> **Bulk Inventory:** Currently scanning all recursive directories... (Stub)", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Stock(bot))
