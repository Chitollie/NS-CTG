import discord
from discord.ui import Select, View
import datetime

class DateSelect(Select):
    def __init__(self):
        today = datetime.datetime.now()
        options = []
        
        for i in range(14):
            date = today + datetime.timedelta(days=i)
            label = date.strftime("%d/%m/%Y")
            description = date.strftime("%A").capitalize()
            options.append(discord.SelectOption(
                label=label,
                description=description,
                value=date.strftime("%Y-%m-%d")
            ))
            
        super().__init__(
            placeholder="📅 Sélectionnez une date...",
            options=options,
            row=0
        )

class HourSelect(Select):
    def __init__(self):
        options = []
        
        for hour in range(24):
            label = f"{hour:02d}:00"
            options.append(discord.SelectOption(
                label=label,
                value=str(hour)
            ))
            
        super().__init__(
            placeholder="🕐 Sélectionnez l'heure...",
            options=options,
            row=1
        )

class MinuteSelect(Select):
    def __init__(self):
        options = []
        
        for minute in range(0, 60, 5):
            label = f":{minute:02d}"
            options.append(discord.SelectOption(
                label=label,
                value=str(minute)
            ))
            
        super().__init__(
            placeholder="⏰ Sélectionnez les minutes...",
            options=options,
            row=2
        )

class DateTimeSelectView(View):
    def __init__(self):
        super().__init__(timeout=300)
        self.selected_date = None
        self.selected_hour = None
        self.selected_minute = None
        
        self.date_select = DateSelect()
        self.hour_select = HourSelect()
        self.minute_select = MinuteSelect()
        
        self.date_select.callback = self.date_callback
        self.hour_select.callback = self.hour_callback
        self.minute_select.callback = self.minute_callback
        
        self.add_item(self.date_select)
        self.add_item(self.hour_select)
        self.add_item(self.minute_select)
        
        self.confirm_button = discord.ui.Button(
            label="✅ Confirmer",
            style=discord.ButtonStyle.success,
            disabled=True,
            row=3
        )
        self.confirm_button.callback = self.confirm_callback
        self.add_item(self.confirm_button)

    async def date_callback(self, interaction: discord.Interaction):
        self.selected_date = interaction.data["values"][0]
        await self._update_confirmation_status(interaction)

    async def hour_callback(self, interaction: discord.Interaction):
        self.selected_hour = interaction.data["values"][0]
        await self._update_confirmation_status(interaction)

    async def minute_callback(self, interaction: discord.Interaction):
        self.selected_minute = interaction.data["values"][0]
        await self._update_confirmation_status(interaction)

    async def _update_confirmation_status(self, interaction: discord.Interaction):
        was_disabled = self.confirm_button.disabled
        self.confirm_button.disabled = not all([
            self.selected_date,
            self.selected_hour,
            self.selected_minute
        ])
        
        if was_disabled != self.confirm_button.disabled:
            await interaction.response.edit_message(view=self)
        else:
            await interaction.response.defer()

    async def confirm_callback(self, interaction: discord.Interaction):
        if not all([self.selected_date, self.selected_hour, self.selected_minute]):
            await interaction.response.send_message(
                "❌ Veuillez sélectionner une date et une heure complète.",
                ephemeral=True
            )
            return
            
        try:
            date_obj = datetime.datetime.strptime(
                f"{self.selected_date} {self.selected_hour}:{self.selected_minute}",
                "%Y-%m-%d %H:%M"
            )
            
            if date_obj < datetime.datetime.now():
                await interaction.response.send_message(
                    "❌ La date sélectionnée est dans le passé.",
                    ephemeral=True
                )
                return
                
            interaction.client.temp_storage = getattr(interaction.client, "temp_storage", {})
            interaction.client.temp_storage[interaction.user.id] = date_obj
            
            await interaction.response.send_message(
                f"✅ Date sélectionnée : {date_obj.strftime('%d/%m/%Y à %H:%M')}",
                ephemeral=True
            )
            self.stop()
            
        except ValueError:
            await interaction.response.send_message(
                "❌ Erreur lors de la création de la date.",
                ephemeral=True
            )
            return