# Tradutor XML PT-BR
# Funciona em Pydroid 3 / Termux / Buildozer (Kivy)
# Instalar: pip install kivy deep-translator

import os
import re
import html
import xml.etree.ElementTree as ET
from pathlib import Path

try:
    from deep_translator import GoogleTranslator
except Exception:
    GoogleTranslator = None

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.progressbar import ProgressBar
from kivy.clock import Clock
from kivy.core.window import Window

Window.softinput_mode = "below_target"

# Tags que geralmente não devem ser traduzidas
IGNORAR_TAGS = {"script", "style", "meta", "manifest", "uses-permission"}

# Atributos que podem ter texto visível ao usuário
ATRIBUTOS_TRADUZIVEIS = {
    "text", "title", "summary", "label", "hint", "description", "contentDescription",
    "android:text", "android:title", "android:summary", "android:label", "android:hint",
    "android:description", "android:contentDescription"
}

PLACEHOLDER_RE = re.compile(r"(%\d*\$?[sdfox]|%[sdfox]|\{[^}]+\}|\\n|\\t|&[a-zA-Z#0-9]+;|<[^>]+>)")


def deve_traduzir(texto: str) -> bool:
    if not texto or not texto.strip():
        return False
    t = texto.strip()
    if t.startswith("@") or t.startswith("?") or t.startswith("#"):
        return False
    if re.fullmatch(r"[\d\W_]+", t):
        return False
    return True


def proteger_placeholders(texto: str):
    partes = []

    def repl(match):
        partes.append(match.group(0))
        return f"__P{len(partes)-1}__"

    protegido = PLACEHOLDER_RE.sub(repl, texto)
    return protegido, partes


def restaurar_placeholders(texto: str, partes):
    for i, valor in enumerate(partes):
        texto = texto.replace(f"__P{i}__", valor)
    return texto


class TradutorXML:
    def __init__(self, destino="pt"):
        if GoogleTranslator is None:
            raise RuntimeError("Biblioteca deep-translator não encontrada. Instale com: pip install deep-translator")
        self.tradutor = GoogleTranslator(source="auto", target=destino)
        self.cache = {}

    def traduzir_texto(self, texto: str) -> str:
        if not deve_traduzir(texto):
            return texto

        prefixo = texto[:len(texto) - len(texto.lstrip())]
        sufixo = texto[len(texto.rstrip()):]
        miolo = texto.strip()

        if miolo in self.cache:
            return prefixo + self.cache[miolo] + sufixo

        protegido, partes = proteger_placeholders(miolo)
        traduzido = self.tradutor.translate(protegido)
        traduzido = restaurar_placeholders(traduzido, partes)
        traduzido = html.unescape(traduzido)
        self.cache[miolo] = traduzido
        return prefixo + traduzido + sufixo

    def traduzir_arquivo(self, entrada: str, saida: str, traduzir_atributos=True):
        ET.register_namespace('android', 'http://schemas.android.com/apk/res/android')
        tree = ET.parse(entrada)
        root = tree.getroot()
        total = 0

        for elem in root.iter():
            tag_limpa = elem.tag.split('}')[-1]
            if tag_limpa in IGNORAR_TAGS:
                continue

            if deve_traduzir(elem.text):
                elem.text = self.traduzir_texto(elem.text)
                total += 1

            if deve_traduzir(elem.tail):
                elem.tail = self.traduzir_texto(elem.tail)
                total += 1

            if traduzir_atributos:
                for chave, valor in list(elem.attrib.items()):
                    chave_limpa = chave.split('}')[-1]
                    if chave in ATRIBUTOS_TRADUZIVEIS or chave_limpa in ATRIBUTOS_TRADUZIVEIS:
                        if deve_traduzir(valor):
                            elem.attrib[chave] = self.traduzir_texto(valor)
                            total += 1

        Path(saida).parent.mkdir(parents=True, exist_ok=True)
        tree.write(saida, encoding="utf-8", xml_declaration=True)
        return total


class Tela(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=12, spacing=8, **kwargs)

        self.add_widget(Label(text="Tradutor XML para Português", font_size=22, size_hint_y=None, height=45))

        self.entrada = TextInput(
            hint_text="Caminho do XML original. Ex: /storage/emulated/0/Download/strings.xml",
            multiline=False,
            size_hint_y=None,
            height=52,
        )
        self.add_widget(self.entrada)

        self.saida = TextInput(
            hint_text="Caminho para salvar. Ex: /storage/emulated/0/Download/strings_pt.xml",
            multiline=False,
            size_hint_y=None,
            height=52,
        )
        self.add_widget(self.saida)

        self.botao = Button(text="Traduzir para Português", size_hint_y=None, height=55)
        self.botao.bind(on_press=self.iniciar)
        self.add_widget(self.botao)

        self.barra = ProgressBar(max=100, value=0, size_hint_y=None, height=20)
        self.add_widget(self.barra)

        self.log = Label(text="Pronto.", size_hint_y=None, halign="left", valign="top")
        self.log.bind(texture_size=lambda inst, val: setattr(inst, 'height', val[1]))
        scroll = ScrollView()
        scroll.add_widget(self.log)
        self.add_widget(scroll)

    def escrever(self, texto):
        self.log.text += "\n" + texto

    def iniciar(self, *_):
        entrada = self.entrada.text.strip()
        saida = self.saida.text.strip()

        if not entrada:
            self.escrever("❌ Coloque o caminho do XML original.")
            return
        if not os.path.exists(entrada):
            self.escrever("❌ Arquivo não encontrado: " + entrada)
            return
        if not saida:
            base = Path(entrada)
            saida = str(base.with_name(base.stem + "_pt" + base.suffix))
            self.saida.text = saida

        self.botao.disabled = True
        self.barra.value = 10
        self.escrever("⏳ Traduzindo... precisa de internet.")
        Clock.schedule_once(lambda dt: self.traduzir(entrada, saida), 0.2)

    def traduzir(self, entrada, saida):
        try:
            tradutor = TradutorXML(destino="pt")
            qtd = tradutor.traduzir_arquivo(entrada, saida)
            self.barra.value = 100
            self.escrever(f"✅ Concluído. Textos traduzidos: {qtd}")
            self.escrever("📁 Salvo em: " + saida)
        except Exception as e:
            self.barra.value = 0
            self.escrever("❌ Erro: " + str(e))
        finally:
            self.botao.disabled = False


class TradutorXMLApp(App):
    def build(self):
        return Tela()


if __name__ == "__main__":
    TradutorXMLApp().run()
