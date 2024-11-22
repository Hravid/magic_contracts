from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from datetime import datetime
import os
import sys

from docxtpl import DocxTemplate
from kivy.properties import StringProperty

def resource_path(relative_path):
    """ Funkcja pomocnicza do znajdowania ścieżek zasobów """
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller tworzy folder tymczasowy i przechowuje ścieżkę w _MEIPASS
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class FormularzKlienta(BoxLayout):
    dzisiejsza_data = StringProperty('')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Upewnij się, że folder na wygenerowane pliki istnieje
        self.base_dir = os.path.join(os.path.expanduser('~'), 'GeneratorUmow')
        self.klienci_dir = os.path.join(self.base_dir, 'klienci')
        os.makedirs(self.klienci_dir, exist_ok=True)
        
        # Ustaw domyślną datę
        self.dzisiejsza_data = datetime.now().strftime('%d.%m.%Y')

    def generuj_dokumenty(self, instance):
        dane = {
            'imie_nazwisko_zleceniodawcy': self.ids.imie_nazwisko_zleceniodawcy.text,
            'pesel_zleceniodawcy': self.ids.pesel_zleceniodawcy.text,
            'adres': self.ids.ulica.text,
            'kod_pocztowy': self.ids.kod_pocztowy.text,
            'data_zawarcia_umowy': self.ids.data_zawarcia_umowy.text,
            'data_przyjecia_pacjenta': self.ids.data_przyjecia_pacjenta.text,
            'imie_nazwisko_pacjenta': self.ids.imie_nazwisko_pacjenta.text,
            'pesel_pacjenta': self.ids.pesel_pacjenta.text,
            'numer_konta_zleceniodawcy': self.ids.numer_konta_zleceniodawcy.text
        }

        if not all(dane.values()):
            self.ids.message_label.text = 'Wypełnij wszystkie pola!'
            self.ids.message_label.color = (1, 0, 0, 1)
            return

        nazwa_folderu = os.path.join(self.klienci_dir, dane['imie_nazwisko_zleceniodawcy'])
        os.makedirs(nazwa_folderu, exist_ok=True)

        try:
            # Użyj resource_path do znalezienia szablonu
            template_path = resource_path(os.path.join('assets', 'templates', 'umowa_template.docx'))
            doc = DocxTemplate(template_path)
            doc.render(dane)
            
            # Zapisz w folderze użytkownika
            output_path = os.path.join(nazwa_folderu, f"umowa_{dane['imie_nazwisko_zleceniodawcy']}.docx")
            doc.save(output_path)
            
            # Wyczyść formularz
            self.ids.imie_nazwisko_zleceniodawcy.text = ''
            self.ids.pesel_zleceniodawcy.text = ''
            self.ids.ulica.text = ''
            self.ids.kod_pocztowy.text = ''
            self.ids.data_zawarcia_umowy.text = datetime.now().strftime('%Y-%m-%d')
            self.ids.data_przyjecia_pacjenta.text = datetime.now().strftime('%Y-%m-%d')
            self.ids.imie_nazwisko_pacjenta.text = ''
            self.ids.pesel_pacjenta.text = ''
            self.ids.numer_konta_zleceniodawcy.text = ''
            
            self.ids.message_label.text = f'Dokumenty zostały zapisane w:\n{nazwa_folderu}'
            self.ids.message_label.color = (0, 0.7, 0, 1)
        except Exception as e:
            self.ids.message_label.text = f'Wystąpił błąd: {str(e)}'
            self.ids.message_label.color = (1, 0, 0, 1)

class FormularzApp(App):
    def build(self):
        return FormularzKlienta()

if __name__ == '__main__':
    FormularzApp().run()