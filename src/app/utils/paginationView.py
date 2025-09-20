import os
import discord
from discord.ui import View, Button

class PaginationView(View):
    def __init__(self, pages, image_files, author_id):
        super().__init__(timeout=60)
        self.pages = pages
        self.image_files = image_files
        self.current_page = 0
        self.author_id = author_id
        self.update_buttons()
    
    def update_buttons(self):
        # Clear existing buttons
        self.clear_items()
        
        # Add nav buttons
        if self.current_page > 0:
            prev_button = Button(label="Previous", style=discord.ButtonStyle.primary)
            prev_button.callback = self.prev_page
            self.add_item(prev_button)
        
        # Add page indicator button (disabled, just for display)
        page_indicator = Button(
            label=f"Page {self.current_page + 1}/{len(self.pages)}", 
            style=discord.ButtonStyle.secondary, 
            disabled=True
        )
        self.add_item(page_indicator)
        
        if self.current_page < len(self.pages) - 1:
            next_button = Button(label="Next", style=discord.ButtonStyle.primary)
            next_button.callback = self.next_page
            self.add_item(next_button)
    
    async def prev_page(self, interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("Only the command user can navigate pages.", ephemeral=True)
            return
            
        self.current_page -= 1
        self.update_buttons()
        embed = self.pages[self.current_page]

        # Testing to see if there are files for this page
        if self.current_page < len(self.image_files) and self.image_files[self.current_page]:
            image_path = self.image_files[self.current_page]
            file = discord.File(image_path, filename=os.path.basename(image_path))
            embed.set_image(url=f"attachment://{os.path.basename(image_path)}")
            await interaction.response.edit_message(embed=embed, view=self, attachments=[file])
        else:
            # No files? just update the embed
            await interaction.response.edit_message(embed=embed, view=self, attachments=[])
    
    # Make sure only the user who ran the command can navigate the pages
    async def next_page(self, interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("Only the command user can navigate pages.", ephemeral=True)
            return
            
        self.current_page += 1
        self.update_buttons()
        embed = self.pages[self.current_page]

        if self.current_page < len(self.image_files) and self.image_files[self.current_page]:
            image_path = self.image_files[self.current_page]
            file = discord.File(image_path, filename=os.path.basename(image_path))
            embed.set_image(url=f"attachment://{os.path.basename(image_path)}")
            await interaction.response.edit_message(embed=embed, view=self, attachments=[file])
        else:
            await interaction.response.edit_message(embed=embed, view=self, attachments=[])