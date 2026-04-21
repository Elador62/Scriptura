"""
Scriptura v1.11.1
Application de gestion et suivi d'écriture de roman.
Généré avec Claude AI
Corrigé par Jules AI (branches vx.xx.1)

Corrections v1.11.1 (depuis v1.10.2) :
  - BUG-01 : Mode Liste — ordre DnD persisté dans pm.tree_roots après sync
  - BUG-02 : Mode Liste — ciblage sidebar corrigé (écriture dans l'objet canonique pm.items)
  - BUG-03 : Mode Carte — rafraîchissement des cartes en direct après modif sidebar
  - BUG-04 : Mode composite — récursif (tous les sous-niveaux affichés, avec indentation)
  - BUG-05 : Accueil — superposition dates corrigée (widget entièrement remplacé)
  - UI-01  : Mode Liste — surbrillance uniforme (chevron + contenu ligne)
  - UI-02  : Mode Carte — fantôme semi-transparent pendant le drag & drop
  - UI-03  : Mode Carte — bordure de sélection effacée sur l'ancienne carte
  - UI-04  : Toolbar — bouton du mode actif reste visuellement mis en évidence
"""
import sys, os, json, re, uuid as _uuid_mod, subprocess
from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QListWidget, QListWidgetItem,
    QTreeWidget, QTreeWidgetItem, QVBoxLayout, QHBoxLayout,
    QWidget, QLabel, QPushButton, QDialog,
    QComboBox, QFrame, QToolBar, QFontComboBox,
    QSpinBox, QStackedWidget, QScrollArea, QGridLayout,
    QLineEdit, QColorDialog, QSizePolicy, QMenu, QFileDialog,
    QMessageBox, QProgressBar, QSplitter,
    QTabWidget, QCheckBox, QGroupBox, QFormLayout,
    QToolButton, QPlainTextEdit, QDateEdit, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QButtonGroup,
    QRadioButton, QInputDialog, QSplashScreen
)
from PyQt6.QtGui import (
    QFont, QAction, QTextCharFormat, QTextCursor,
    QColor, QTextTableFormat, QTextListFormat, QIcon,
    QKeySequence, QPalette, QPixmap, QBrush, QPainter, QPen,
    QActionGroup
)
from PyQt6.QtCore import Qt, QPoint, QTimer, QDate, QSize, QMimeData, QByteArray, QRect, QRectF
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtPrintSupport import QPrintDialog, QPrinter

BASEDIR   = os.path.dirname(os.path.abspath(__file__))
ICON_PATH = os.path.join(BASEDIR, "icons")

# ─────────────────────────────────────────────────────────────────────────────
#  CONSTANTES
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_STATUSES = ["Brouillon", "En cours", "Terminé", "Révisé", "À réviser"]
DEFAULT_TYPES    = ["Acte", "Partie", "Chapitre", "Scène", "Prologue", "Épilogue", "Interlude"]
DEFAULT_LABELS   = [
    {"name":"Aucune","color":"#888888"},{"name":"Rouge","color":"#E53935"},
    {"name":"Orange","color":"#FB8C00"},{"name":"Jaune","color":"#FDD835"},
    {"name":"Vert","color":"#43A047"},{"name":"Bleu","color":"#1E88E5"},
    {"name":"Violet","color":"#8E24AA"},{"name":"Rose","color":"#E91E8C"},
    {"name":"Gris","color":"#757575"},
]
GENRES = [
    "Roman","Science-Fiction","Fantasy","Fantasy urbaine","Fantastique",
    "Horreur","Thriller","Policier / Noir","Romance","Romance historique",
    "Historique","Aventure","Jeunesse","Young Adult","Dystopie",
    "Biographie / Autobiographie","Essai","Humour","Érotique","Autre"
]

RECENT_PROJECTS_FILE = Path.home() / ".scriptura_recent.json"

# ─────────────────────────────────────────────────────────────────────────────
#  LOGO SVG (généré inline — pas besoin de fichier externe)
# ─────────────────────────────────────────────────────────────────────────────

LOGO_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#312C51"/>
      <stop offset="100%" style="stop-color:#48426D"/>
    </linearGradient>
    <linearGradient id="pen" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#F0C38E"/>
      <stop offset="100%" style="stop-color:#F1AA9B"/>
    </linearGradient>
  </defs>
  <!-- Fond arrondi -->
  <rect width="200" height="200" rx="36" fill="url(#bg)"/>
  <!-- Livre ouvert -->
  <path d="M30 60 Q30 50 40 50 L98 58 L98 155 L40 148 Q30 148 30 138 Z" fill="#FFFFFF" opacity="0.12"/>
  <path d="M170 60 Q170 50 160 50 L102 58 L102 155 L160 148 Q170 148 170 138 Z" fill="#FFFFFF" opacity="0.18"/>
  <line x1="100" y1="58" x2="100" y2="155" stroke="#F0C38E" stroke-width="2" opacity="0.6"/>
  <!-- Lignes de texte gauche -->
  <line x1="45" y1="78" x2="90" y2="76" stroke="white" stroke-width="3" stroke-linecap="round" opacity="0.55"/>
  <line x1="45" y1="90" x2="88" y2="88" stroke="white" stroke-width="2.5" stroke-linecap="round" opacity="0.4"/>
  <line x1="45" y1="101" x2="91" y2="99" stroke="white" stroke-width="2.5" stroke-linecap="round" opacity="0.4"/>
  <line x1="45" y1="112" x2="86" y2="110" stroke="white" stroke-width="2.5" stroke-linecap="round" opacity="0.4"/>
  <line x1="45" y1="123" x2="89" y2="121" stroke="white" stroke-width="2.5" stroke-linecap="round" opacity="0.3"/>
  <!-- Plume calligraphique -->
  <path d="M125 45 C145 30 170 35 168 65 C166 80 155 90 145 100 L118 130 C116 132 114 130 116 128 L135 98 C120 105 108 98 108 82 C108 65 118 55 125 45 Z" fill="url(#pen)"/>
  <path d="M116 128 C108 150 102 160 96 168" stroke="#F0C38E" stroke-width="2" fill="none" stroke-linecap="round"/>
  <!-- Éclat -->
  <circle cx="148" cy="52" r="6" fill="white" opacity="0.25"/>
</svg>"""

def label_text_color(hex_color):
    """Retourne 'white' ou 'black' selon la luminosité du fond."""
    c = QColor(hex_color)
    lum = 0.299*c.red() + 0.587*c.green() + 0.114*c.blue()
    return "white" if lum < 160 else "black"

def build_global_stylesheet(accent: str, sidebar: str, editor_bg: str, text: str) -> str:
    """QSS global : survol boutons, mode actif toolbar, ascenseurs modernes."""
    sb_light  = label_text_color(sidebar) == "black"
    hover_bg  = "rgba(0,0,0,0.10)" if sb_light else "rgba(255,255,255,0.15)"
    hover_bg2 = "rgba(0,0,0,0.06)" if label_text_color(editor_bg)=="black" else "rgba(255,255,255,0.10)"
    sc_bg     = "#d0d0d0" if label_text_color(editor_bg)=="black" else "#404040"
    return f"""
    /* ── Boutons généraux : survol ── */
    QPushButton {{
        border-radius: 4px;
        padding: 3px 8px;
    }}
    QPushButton:hover {{
        background: {hover_bg2};
        border: 1px solid {accent};
    }}
    QPushButton:pressed {{
        background: {accent}44;
    }}
    /* ── Toolbar buttons : survol + mode actif ── */
    QToolBar QToolButton {{
        border-radius: 5px;
        padding: 4px 8px;
        margin: 2px;
        color: {label_text_color(sidebar)};
    }}
    QToolBar QToolButton:hover {{
        background: {hover_bg};
        border: 1px solid {accent};
    }}
    QToolBar QToolButton:checked,
    QToolBar QToolButton:pressed {{
        background: {hover_bg};
        border: 1px solid {accent};
    }}
    /* ── Boutons bas sidebar ── */
    QPushButton#sidebar_bottom_btn {{
        color: white;
        font-weight: bold;
        font-size: 16px;
        border: none;
    }}
    QPushButton#sidebar_bottom_btn:hover {{
        background: {hover_bg};
        border: 1px solid {accent};
    }}
    /* ── Ascenseurs modernes (web-like) ── */
    QScrollBar:vertical {{
        width: 8px; background: transparent; margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: {accent}99; border-radius: 4px; min-height: 20px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {accent};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    QScrollBar:horizontal {{
        height: 8px; background: transparent; margin: 0;
    }}
    QScrollBar::handle:horizontal {{
        background: {accent}99; border-radius: 4px; min-width: 20px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background: {accent};
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}
    /* ── ComboBox ── */
    QComboBox:hover {{
        border: 1px solid {accent};
        border-radius: 3px;
    }}
    """

# ─────────────────────────────────────────────────────────────────────────────
#  MODÈLE DE DONNÉES
# ─────────────────────────────────────────────────────────────────────────────

class ItemData:
    """Élément de l'arborescence Manuscrit."""
    def __init__(self, name="", type_item="Scène", uid=None):
        self.uid        = uid or str(_uuid_mod.uuid4())[:8]
        self.name       = name
        self.type_item  = type_item
        self.synopsis   = ""
        self.notes      = ""
        self.content    = ""
        self.status     = "Brouillon"
        self.word_goal  = 0
        self.char_goal  = 0
        self.goal_unit  = "mots"
        self.tags       = []
        self.label      = "Aucune"
        self.children   = []
        self.created_at = datetime.now().isoformat()
        self.modified_at= datetime.now().isoformat()
        self.include_in_compile = True
        self.keywords   = []
        self.versions   = []
        self.comments   = []
        self.attachments= []
        self.content_plain = ""   # texte brut pour stats (content est HTML)
        # Pour la corbeille : garder l'uid du parent d'origine et le groupe
        self._origin_parent_uid = None
        self._origin_group      = "Manuscrit"

    def to_dict(self):
        return {
            "uid":self.uid,"name":self.name,"type_item":self.type_item,
            "synopsis":self.synopsis,"notes":self.notes,"status":self.status,
            "word_goal":self.word_goal,"char_goal":self.char_goal,"goal_unit":self.goal_unit,
            "tags":self.tags,"label":self.label,"children":self.children,
            "created_at":self.created_at,"modified_at":self.modified_at,
            "include_in_compile":self.include_in_compile,
            "keywords":self.keywords,"versions":self.versions,
            "comments":self.comments,"attachments":self.attachments,
            "_origin_parent_uid":self._origin_parent_uid,
            "_origin_group":self._origin_group,
        }

    @classmethod
    def from_dict(cls, d):
        obj = cls(d.get("name",""),d.get("type_item","Scène"),d.get("uid"))
        for attr in ("synopsis","notes","status","word_goal","char_goal","goal_unit",
                     "tags","label","children","created_at","modified_at",
                     "include_in_compile","keywords","versions","comments","attachments",
                     "_origin_parent_uid","_origin_group"):
            if attr in d: setattr(obj,attr,d[attr])
        return obj


class SimpleCardData:
    """Données génériques pour Personnages, Lieux, Notes, Idées, Références."""
    ICON_MAP = {
        "Personnage": "👤", "Lieu": "📍",
        "Note": "📝", "Recherche": "🔍",
        "Idée": "💡", "Référence": "📚",
    }
    def __init__(self, name="", kind="Note", uid=None):
        self.uid      = uid or str(_uuid_mod.uuid4())[:8]
        self.name     = name
        self.kind     = kind   # Personnage | Lieu | Note | Recherche | Idée | Référence
        self.fields   = {}     # champ → valeur texte
        self.content  = ""     # contenu libre (éditeur)
        self.rating   = 0      # 0–5 étoiles (pour Idées)
        self.created_at = datetime.now().isoformat()
        self.modified_at= datetime.now().isoformat()
        self.tags     = []
        self.children = []
        self._is_folder = False
        self._origin_parent_uid = None
        self._origin_group      = kind+"s"
        # Shared with ItemData for inspector compatibility
        self.attachments = []
        self.versions    = []
        self.comments    = []
        self.keywords    = []
        self.synopsis    = ""
        self.notes       = ""
        self.status      = "Brouillon"
        self.type_item   = kind
        self.include_in_compile = True
        self.label       = "Aucune"

    def to_dict(self):
        return {k:v for k,v in self.__dict__.items()}

    @classmethod
    def from_dict(cls, d):
        obj = cls(d.get("name",""),d.get("kind","Note"),d.get("uid"))
        for k,v in d.items():
            setattr(obj,k,v)
        return obj

    @property
    def icon(self):
        if self._is_folder: return "📁"
        return self.ICON_MAP.get(self.kind,"📄")


class ProjectData:
    def __init__(self):
        self.title="Mon Roman"; self.author=""; self.genre=""
        self.description=""; self.word_goal=80000
        self.created_at=datetime.now().isoformat()
        self.modified_at=datetime.now().isoformat()
        self.cover_image=""; self.status="En cours"; self.deadline=""

    def to_dict(self): return self.__dict__

    @classmethod
    def from_dict(cls,d):
        p=cls()
        for k,v in d.items(): setattr(p,k,v)
        return p


# ─────────────────────────────────────────────────────────────────────────────
#  GESTIONNAIRE DE PERSISTANCE
# ─────────────────────────────────────────────────────────────────────────────

class ProjectManager:
    GROUPS = ["Manuscrit","Personnages","Lieux","Notes","Recherches","Idées","Références"]

    def __init__(self):
        self.project_dir  = None
        self.project_data = ProjectData()
        self.items        = {}   # uid → ItemData (manuscrit)
        self.cards        = {}   # uid → SimpleCardData (tous les autres modules)
        self.tree_roots   = {g:[] for g in self.GROUPS}
        self.trash_items  = []   # uid d'items dans la corbeille
        self.sessions     = []   # liste de dicts séance
        self.config       = self._default_config()

    @staticmethod
    def _default_config():
        return {
            "theme":"Scriptura","font_family":"Georgia","font_size":13,
            "autosave_interval":60,"cloud_path":"","typewriter_mode":False,
            "show_word_count":True,"paragraph_spacing":1.5,"line_spacing":1.2,
            "editor_width":700,
            "statuses":list(DEFAULT_STATUSES),
            "item_types":list(DEFAULT_TYPES),
            "labels":list(DEFAULT_LABELS),
            "session_locations":["Bureau","Train","Canapé","Café","Bibliothèque","Autre"],
        }

    def new_project(self, directory, title="Mon Roman", author=""):
        self.project_dir = Path(directory)
        self.project_dir.mkdir(parents=True, exist_ok=True)
        for sub in ["manuscrit","personnages","lieux","notes","recherches","idees","references"]:
            (self.project_dir/sub).mkdir(exist_ok=True)
        self.project_data = ProjectData()
        self.project_data.title = title; self.project_data.author = author
        self.items = {}; self.cards = {}
        self.tree_roots = {g:[] for g in self.GROUPS}
        self.trash_items = []
        self.sessions = []
        self.save_project()

    def save_project(self):
        if not self.project_dir: return False
        self.project_data.modified_at = datetime.now().isoformat()
        pf = {
            "project":    self.project_data.to_dict(),
            "config":     self.config,
            "tree_roots": self.tree_roots,
            "trash_items": self.trash_items,
            "sessions":    self.sessions,
            "items":      {uid:d.to_dict() for uid,d in self.items.items()},
            "cards":      {uid:d.to_dict() for uid,d in self.cards.items()},
        }
        with open(self.project_dir/"project.json","w",encoding="utf-8") as f:
            json.dump(pf,f,ensure_ascii=False,indent=2)
        # Fichiers .md pour items manuscrit
        ms_dir = self.project_dir/"manuscrit"
        for uid,item in self.items.items():
            with open(ms_dir/f"{uid}.md","w",encoding="utf-8") as f:
                f.write(f"# {item.name}\n\n")
                if item.synopsis: f.write(f"**Synopsis :** {item.synopsis}\n\n")
                f.write("---\n\n"); f.write(item.content or "")
        # Fichiers .md pour cards
        subdir_map = {
            "Personnage":"personnages","Lieu":"lieux","Note":"notes",
            "Recherche":"recherches","Idée":"idees","Référence":"references"
        }
        for uid,card in self.cards.items():
            sub = subdir_map.get(card.kind,"notes")
            md_dir = self.project_dir/sub
            md_dir.mkdir(exist_ok=True)
            with open(md_dir/f"{uid}.md","w",encoding="utf-8") as f:
                f.write(f"# {card.name}\n\n")
                for k,v in card.fields.items(): f.write(f"## {k}\n{v}\n\n")
                if card.content: f.write("---\n\n"); f.write(card.content)
        return True

    def load_project(self, project_dir):
        self.project_dir = Path(project_dir)
        pf = self.project_dir/"project.json"
        if not pf.exists(): return False
        with open(pf,"r",encoding="utf-8") as f: data = json.load(f)
        self.project_data = ProjectData.from_dict(data.get("project",{}))
        self.config       = {**self._default_config(),**data.get("config",{})}
        self.tree_roots   = data.get("tree_roots",{g:[] for g in self.GROUPS})
        self.trash_items  = data.get("trash_items",[])
        self.sessions     = data.get("sessions",[])
        # Items manuscrit
        self.items = {}
        ms_dir = self.project_dir/"manuscrit"
        for uid,d in data.get("items",{}).items():
            item = ItemData.from_dict(d)
            md_path = ms_dir/f"{uid}.md"
            if md_path.exists():
                raw = md_path.read_text(encoding="utf-8")
                parts = raw.split("---\n\n",1)
                item.content = parts[1] if len(parts)>1 else raw
            self.items[uid] = item
        # Cards
        self.cards = {}
        for uid,d in data.get("cards",{}).items():
            card = SimpleCardData.from_dict(d)
            # Charger le contenu md
            sub = {"Personnage":"personnages","Lieu":"lieux","Note":"notes",
                   "Recherche":"recherches","Idée":"idees","Référence":"references"}.get(card.kind,"notes")
            md_path = self.project_dir/sub/f"{uid}.md"
            if md_path.exists() and not card._is_folder:
                raw = md_path.read_text(encoding="utf-8")
                parts = raw.split("---\n\n",1)
                card.content = parts[1] if len(parts)>1 else ""
            self.cards[uid] = card
        return True

    def total_words(self):
        return sum(len(getattr(it,"content_plain",it.content or "").split())
                   for it in self.items.values() if it.content)

    def get_labels(self):   return self.config.get("labels",list(DEFAULT_LABELS))
    def get_statuses(self): return self.config.get("statuses",list(DEFAULT_STATUSES))
    def get_item_types(self): return self.config.get("item_types",list(DEFAULT_TYPES))
    def get_session_locations(self): return self.config.get("session_locations",["Bureau","Train","Canapé","Café","Bibliothèque","Autre"])

    # ── Projets récents ────────────────────────────────────────────────────
    @staticmethod
    def load_recent():
        try:
            if RECENT_PROJECTS_FILE.exists():
                return json.loads(RECENT_PROJECTS_FILE.read_text(encoding="utf-8"))
        except: pass
        return []

    @staticmethod
    def add_recent(path):
        recent = ProjectManager.load_recent()
        path = str(path)
        if path in recent: recent.remove(path)
        recent.insert(0,path)
        recent = recent[:10]
        RECENT_PROJECTS_FILE.write_text(json.dumps(recent),encoding="utf-8")

    def get_stats_snapshot(self):
        """Stats rapides pour la fenêtre des projets récents."""
        pd = self.project_data
        words    = self.total_words()
        goal     = max(pd.word_goal,1)
        pct      = min(int(words/goal*100),100)
        chapters = sum(1 for it in self.items.values() if it.type_item in ("Chapitre","Acte","Partie"))
        scenes   = sum(1 for it in self.items.values() if it.type_item in ("Scène","Page","Prologue","Épilogue","Interlude"))
        chars    = sum(1 for c in self.cards.values() if c.kind=="Personnage" and not c._is_folder)
        return {
            "title":pd.title,"author":pd.author,"genre":pd.genre,
            "status":pd.status,"description":pd.description,
            "word_goal":pd.word_goal,"words":words,"pct":pct,
            "chapters":chapters,"scenes":scenes,"characters":chars,
            "created_at":pd.created_at[:10],"modified_at":pd.modified_at[:10],
        }


# ─────────────────────────────────────────────────────────────────────────────
#  SPLASH SCREEN
# ─────────────────────────────────────────────────────────────────────────────

class SplashScreen(QDialog):
    def __init__(self):
        super().__init__(None, Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setFixedSize(480,300)
        self.setStyleSheet("background:#1E1B2E; border-radius:16px;")
        v = QVBoxLayout(self); v.setContentsMargins(32,32,32,32); v.setSpacing(16)
        # Ligne logo + titre
        row = QHBoxLayout(); row.setSpacing(20)
        # Logo SVG inline via QLabel avec SVG rendu dans un pixmap
        logo_lbl = QLabel(); logo_lbl.setFixedSize(90,90)
        pix = self._svg_to_pixmap(LOGO_SVG, 90, 90)
        logo_lbl.setPixmap(pix)
        row.addWidget(logo_lbl)
        right = QVBoxLayout()
        name_lbl = QLabel("Scriptura")
        name_lbl.setStyleSheet("color:#F0C38E;font-size:42px;font-weight:900;letter-spacing:2px;")
        tagline = QLabel("Votre atelier d'écriture")
        tagline.setStyleSheet("color:#9B8EC4;font-size:14px;")
        right.addStretch(); right.addWidget(name_lbl); right.addWidget(tagline); right.addStretch()
        row.addLayout(right)
        v.addLayout(row)
        # Barre de chargement
        self.progress = QProgressBar()
        self.progress.setRange(0,100); self.progress.setValue(0)
        self.progress.setFixedHeight(6)
        self.progress.setStyleSheet("""
            QProgressBar{border:none;background:#312C51;border-radius:3px;}
            QProgressBar::chunk{background:#F0C38E;border-radius:3px;}
        """)
        v.addStretch(); v.addWidget(self.progress)
        status_lbl = QLabel("Chargement…")
        status_lbl.setStyleSheet("color:#666;font-size:11px;")
        status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v.addWidget(status_lbl)
        self.status_lbl = status_lbl
        # Timer animation
        self._val = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(25)

    def _tick(self):
        self._val += 3
        self.progress.setValue(min(self._val,100))
        msgs = {20:"Interface…",50:"Modules…",75:"Finalisation…",95:"Prêt !"}
        for k,v in msgs.items():
            if self._val >= k: self.status_lbl.setText(v)
        if self._val >= 100:
            self._timer.stop()
            QTimer.singleShot(300, self.accept)

    @staticmethod
    def _svg_to_pixmap(svg_str, w, h):
        """Convertit une chaîne SVG en QPixmap via QPainter."""
        from PyQt6.QtSvg import QSvgRenderer
        pix = QPixmap(w,h); pix.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pix)
        renderer = QSvgRenderer(svg_str.encode())
        # Utilisation de QRectF au lieu de QRect
        renderer.render(painter, QRectF(0, 0, w, h)) 
        painter.end()
        return pix


# ─────────────────────────────────────────────────────────────────────────────
#  FENÊTRE PROJETS RÉCENTS
# ─────────────────────────────────────────────────────────────────────────────

class RecentProjectsDialog(QDialog):
    """Affiche les derniers projets avec stats ; retourne le chemin choisi."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Scriptura — Ouvrir un projet")
        self.setMinimumSize(860, 560)
        self.chosen_path = None
        self._build()

    def _build(self):
        v = QVBoxLayout(self)
        # Entête
        hdr = QHBoxLayout()
        logo_pix = SplashScreen._svg_to_pixmap(LOGO_SVG, 48, 48)
        logo_lbl = QLabel(); logo_lbl.setPixmap(logo_pix)
        title_lbl = QLabel("Bienvenue dans Scriptura")
        title_lbl.setStyleSheet("font-size:22px;font-weight:bold;")
        hdr.addWidget(logo_lbl); hdr.addWidget(title_lbl); hdr.addStretch()
        v.addLayout(hdr)

        main_row = QHBoxLayout(); main_row.setSpacing(16)

        # ── Colonne gauche : liste des projets récents ─────────────────────
        left = QWidget(); left.setFixedWidth(260)
        lv = QVBoxLayout(left); lv.setContentsMargins(0,0,0,0)
        lv.addWidget(QLabel("<b>Projets récents</b>"))
        self.recent_list = QListWidget()
        self.recent_list.currentItemChanged.connect(self._on_select)
        self.recent_list.itemDoubleClicked.connect(self._open_selected)
        lv.addWidget(self.recent_list,1)
        btn_browse = QPushButton("📂 Parcourir…"); btn_browse.clicked.connect(self._browse)
        btn_new    = QPushButton("＋ Nouveau projet"); btn_new.clicked.connect(self._new_project)
        lv.addWidget(btn_browse); lv.addWidget(btn_new)
        main_row.addWidget(left)

        # ── Colonne droite : stats du projet sélectionné ──────────────────
        self.detail_widget = QScrollArea()
        self.detail_widget.setWidgetResizable(True)
        self.detail_widget.setFrameShape(QFrame.Shape.NoFrame)
        self._detail_inner = QWidget()
        self._detail_v = QVBoxLayout(self._detail_inner)
        self._detail_v.setContentsMargins(12,12,12,12)
        self.detail_widget.setWidget(self._detail_inner)
        # _detail_inner remplacé entièrement à chaque sélection (BUG-05)
        main_row.addWidget(self.detail_widget,1)
        v.addLayout(main_row,1)

        # Boutons bas
        btns = QHBoxLayout()
        self.btn_open = QPushButton("Ouvrir"); self.btn_open.setEnabled(False)
        self.btn_open.clicked.connect(self._open_selected)
        btn_close = QPushButton("Fermer"); btn_close.clicked.connect(self.reject)
        btns.addStretch(); btns.addWidget(btn_close); btns.addWidget(self.btn_open)
        v.addLayout(btns)

        self._load_recent_list()

    def _load_recent_list(self):
        self.recent_list.clear()
        for path in ProjectManager.load_recent():
            item = QListWidgetItem(os.path.basename(path))
            item.setToolTip(path)
            item.setData(Qt.ItemDataRole.UserRole, path)
            self.recent_list.addItem(item)

    def _on_select(self, item):
        if not item: return
        path = item.data(Qt.ItemDataRole.UserRole)
        self.btn_open.setEnabled(True)
        self._show_stats(path)

    def _show_stats(self, path):
        # BUG-05: Remplacer l'ancien widget entièrement pour éviter la superposition
        if self._detail_inner is not None:
            self._detail_inner.deleteLater()
        self._detail_inner = QWidget()
        self._detail_v = QVBoxLayout(self._detail_inner)
        self._detail_v.setContentsMargins(12,12,12,12)
        self.detail_widget.setWidget(self._detail_inner)

        pm = ProjectManager()
        if not pm.load_project(path):
            self._detail_v.addWidget(QLabel("<i>Impossible de lire ce projet.</i>"))
            return
        s = pm.get_stats_snapshot()

        self._detail_v.addWidget(QLabel(f"<b style='font-size:18px'>{s['title']}</b>"))
        if s['author']: self._detail_v.addWidget(QLabel(f"par {s['author']}"))

        # Cartes stats
        cards_row = QHBoxLayout(); cards_row.setSpacing(8)
        for label, val in [
            ("Mots écrits", f"{s['words']:,}".replace(","," ")),
            ("Objectif",    f"{s['word_goal']:,}".replace(","," ")),
            ("Progression", f"{s['pct']} %"),
            ("Chapitres",   str(s['chapters'])),
            ("Scènes",      str(s['scenes'])),
            ("Personnages", str(s['characters'])),
        ]:
            card = QFrame(); card.setFrameShape(QFrame.Shape.StyledPanel)
            card.setStyleSheet("border-radius:8px;padding:4px;")
            cl = QVBoxLayout(card)
            vl = QLabel(val); vl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            vl.setStyleSheet("font-size:18px;font-weight:bold;")
            ll = QLabel(label); ll.setAlignment(Qt.AlignmentFlag.AlignCenter)
            ll.setStyleSheet("font-size:10px;")
            cl.addWidget(vl); cl.addWidget(ll)
            cards_row.addWidget(card)
        w = QWidget(); w.setLayout(cards_row)
        self._detail_v.addWidget(w)

        # Barre progression
        pb = QProgressBar(); pb.setRange(0,100); pb.setValue(s['pct']); pb.setFixedHeight(14)
        self._detail_v.addWidget(pb)

        # Infos (dates clairement séparées)
        form = QFormLayout(); form.setVerticalSpacing(4)
        form.addRow("Genre :",      QLabel(s['genre'] or "—"))
        form.addRow("Statut :",     QLabel(s['status']))
        form.addRow("Créé le :",    QLabel(s['created_at']))
        form.addRow("Modifié le :", QLabel(s['modified_at']))
        self._detail_v.addLayout(form)

        # Synopsis
        if s['description']:
            self._detail_v.addWidget(QLabel("<b>Synopsis</b>"))
            desc = QLabel(s['description']); desc.setWordWrap(True)
            self._detail_v.addWidget(desc)
        self._detail_v.addStretch()

    def _browse(self):
        folder = QFileDialog.getExistingDirectory(self,"Ouvrir un projet Scriptura")
        if folder:
            self.chosen_path = folder; self.accept()

    def _new_project(self):
        self.chosen_path = "NEW"; self.accept()

    def _open_selected(self, *args):
        item = self.recent_list.currentItem()
        if item:
            self.chosen_path = item.data(Qt.ItemDataRole.UserRole)
            self.accept()


# ─────────────────────────────────────────────────────────────────────────────
#  ARBRE AVEC DRAG & DROP
# ─────────────────────────────────────────────────────────────────────────────

class DnDTreeWidget(QTreeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setDragEnabled(True); self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

    def dropEvent(self, event):
        target = self.itemAt(event.position().toPoint())
        if target:
            role = target.data(0,Qt.ItemDataRole.UserRole)
            if role=="ROOT_GROUP" and "Corbeille" in target.text(0):
                event.ignore(); return
        super().dropEvent(event)
        # Notify parent app
        p = self.parent()
        while p:
            if hasattr(p, "on_tree_structure_changed"):
                p.on_tree_structure_changed()
                break
            p = p.parent()



# ─────────────────────────────────────────────────────────────────────────────
#  ÉDITEUR RICH TEXT (inspiré de wordprocessor.py, porté en PyQt6)
# ─────────────────────────────────────────────────────────────────────────────

IMAGE_EXTENSIONS = ['.jpg','.jpeg','.png','.bmp','.gif']

class RichTextEdit(QTextEdit):
    """QTextEdit étendu pour le glisser-déposer d'images."""

    def canInsertFromMimeData(self, source):
        if source.hasImage(): return True
        return super().canInsertFromMimeData(source)

    def insertFromMimeData(self, source):
        cursor = self.textCursor()
        document = self.document()
        if source.hasUrls():
            for u in source.urls():
                ext = os.path.splitext(str(u.toLocalFile()))[1].lower()
                if u.isLocalFile() and ext in IMAGE_EXTENSIONS:
                    image = QPixmap(u.toLocalFile())
                    if not image.isNull():
                        document.addResource(
                            QTextDocument.ResourceType.ImageResource,
                            u, image
                        )
                        cursor.insertImage(u.toLocalFile())
                else:
                    break
            else:
                return
        elif source.hasImage():
            image = source.imageData()
            uid = str(_uuid_mod.uuid4().hex)
            document.addResource(QTextDocument.ResourceType.ImageResource, uid, image)
            cursor.insertImage(uid)
            return
        super().insertFromMimeData(source)

# ─────────────────────────────────────────────────────────────────────────────
#  INSPECTEUR MULTI-VUES
# ─────────────────────────────────────────────────────────────────────────────

class InspectorPanel(QWidget):
    TABS = [("📝","Notes"),("📎","Signets"),
            ("🏷","Métadonnées"),("🕐","Versions"),("💬","Commentaires")]

    def __init__(self, pm: ProjectManager, parent=None):
        super().__init__(parent)
        self.pm = pm
        self.current_item_data = None
        self._build()

    def _build(self):
        v = QVBoxLayout(self); v.setContentsMargins(0,0,0,0); v.setSpacing(0)
        icon_bar = QWidget(); icon_bar.setFixedHeight(36); icon_bar.setObjectName("inspector_icon_bar")
        ib = QHBoxLayout(icon_bar); ib.setContentsMargins(4,2,4,2); ib.setSpacing(2)
        self.tab_buttons = []
        for i,(icon,tip) in enumerate(self.TABS):
            btn = QPushButton(icon); btn.setFixedSize(36,28); btn.setToolTip(tip)
            btn.setCheckable(True); btn.setObjectName("inspector_tab_btn")
            btn.clicked.connect(lambda _,idx=i: self._switch_tab(idx))
            ib.addWidget(btn); self.tab_buttons.append(btn)
        ib.addStretch(); v.addWidget(icon_bar)
        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine); v.addWidget(sep)
        self.stack = QStackedWidget(); v.addWidget(self.stack,1)
        self._build_notes_tab()
        self._build_attachments_tab()
        self._build_metadata_tab()
        self._build_versions_tab()
        self._build_comments_tab()
        self._switch_tab(0)

    def _switch_tab(self, idx):
        self.stack.setCurrentIndex(idx)
        for i,btn in enumerate(self.tab_buttons): btn.setChecked(i==idx)

    # ── Tab 0 : Notes/Synopsis (+ champ Nom pour toujours avoir ins_name accessible) ──
    def _build_notes_tab(self):
        w = QWidget(); v = QVBoxLayout(w); v.setContentsMargins(8,8,8,8); v.setSpacing(6)
        # Champ Nom (affiché ici maintenant)
        v.addWidget(QLabel("<b>Nom</b>"))
        self.ins_name = QLineEdit(); self.ins_name.setPlaceholderText("Titre…")
        v.addWidget(self.ins_name)
        # Widgets type/status (définis ici pour collect_properties, cachés ici, visibles dans Métadonnées)
        self.ins_type   = QComboBox()
        self.ins_status = QComboBox()
        v.addWidget(QLabel("<b>Synopsis</b>"))
        self.ins_synopsis = QTextEdit(); self.ins_synopsis.setPlaceholderText("Résumé…")
        v.addWidget(self.ins_synopsis,2)
        v.addWidget(QLabel("<b>Notes internes</b>"))
        self.ins_notes = QTextEdit(); self.ins_notes.setPlaceholderText("Notes de travail…")
        v.addWidget(self.ins_notes,2)
        self.stack.addWidget(w)

    # ── Tab 2 : Signets ──────────────────────────────────────────────────
    def _build_attachments_tab(self):
        w = QWidget(); v = QVBoxLayout(w); v.setContentsMargins(8,8,8,8); v.setSpacing(6)
        v.addWidget(QLabel("<b>📎 Documents joints</b>"))
        self.attach_list = QListWidget(); v.addWidget(self.attach_list,1)
        btns = QHBoxLayout()
        btn_add  = QPushButton("＋ Ajouter…"); btn_add.clicked.connect(self._add_attachment)
        btn_open = QPushButton("Ouvrir");      btn_open.clicked.connect(self._open_attachment)
        btn_del  = QPushButton("🗑");          btn_del.clicked.connect(self._del_attachment); btn_del.setFixedWidth(32)
        btns.addWidget(btn_add,1); btns.addWidget(btn_open); btns.addWidget(btn_del)
        v.addLayout(btns)
        self.stack.addWidget(w)

    def _add_attachment(self):
        if not self.current_item_data: return
        paths,_ = QFileDialog.getOpenFileNames(self,"Joindre des fichiers")
        for p in paths:
            if p not in self.current_item_data.attachments:
                self.current_item_data.attachments.append(p)
        self._refresh_attachments()

    def _del_attachment(self):
        if not self.current_item_data: return
        row = self.attach_list.currentRow()
        if row<0: return
        del self.current_item_data.attachments[row]
        self._refresh_attachments()

    def _open_attachment(self):
        row = self.attach_list.currentRow()
        if row<0 or not self.current_item_data: return
        path = self.current_item_data.attachments[row]
        try:
            if sys.platform.startswith("linux"): subprocess.Popen(["xdg-open",path])
            elif sys.platform=="darwin": subprocess.Popen(["open",path])
            else: os.startfile(path)
        except Exception as e: QMessageBox.warning(self,"Erreur",str(e))

    def _refresh_attachments(self):
        self.attach_list.clear()
        if not self.current_item_data: return
        for p in self.current_item_data.attachments:
            self.attach_list.addItem(os.path.basename(p))

    # ── Tab 2 : Métadonnées (Type, Statut, Étiquette, Dates, Compilation, Mots-clefs) ──
    def _build_metadata_tab(self):
        w = QScrollArea(); w.setWidgetResizable(True); w.setFrameShape(QFrame.Shape.NoFrame)
        inner = QWidget(); v = QVBoxLayout(inner); v.setContentsMargins(8,8,8,8); v.setSpacing(8)
        w.setWidget(inner)
        # Type et Statut — éditables
        v.addWidget(QLabel("<b>Type</b>"))
        self.meta_type_combo = QComboBox()
        v.addWidget(self.meta_type_combo)
        v.addWidget(QLabel("<b>Statut</b>"))
        self.meta_status_combo = QComboBox()
        v.addWidget(self.meta_status_combo)
        # Étiquette avec carré couleur
        v.addWidget(QLabel("<b>Étiquette</b>"))
        self.meta_label = QComboBox()
        v.addWidget(self.meta_label)
        # Alias labels pour compatibilité
        self.meta_type_lbl   = QLabel()
        self.meta_status_lbl = QLabel()
        # Dates
        self.meta_created  = QLabel("—"); self.meta_modified = QLabel("—")
        v.addWidget(QLabel("<b>Dates</b>"))
        f = QFormLayout()
        f.addRow("Créé le :",    self.meta_created)
        f.addRow("Modifié le :", self.meta_modified)
        v.addLayout(f)
        v.addWidget(QLabel("<b>Compilation</b>"))
        self.meta_compile = QCheckBox("Inclure dans la compilation"); v.addWidget(self.meta_compile)
        v.addWidget(QLabel("<b>Mots-clefs</b>"))
        self.meta_keywords_edit = QLineEdit()
        self.meta_keywords_edit.setPlaceholderText("Ajouter un mot-clef…")
        btn_add_kw = QPushButton("＋"); btn_add_kw.setFixedWidth(28)
        btn_add_kw.clicked.connect(self._add_keyword)
        self.meta_keywords_edit.returnPressed.connect(self._add_keyword)
        kw_row = QHBoxLayout()
        kw_row.addWidget(self.meta_keywords_edit,1); kw_row.addWidget(btn_add_kw)
        v.addLayout(kw_row)
        self.meta_kw_container = QWidget()
        self.meta_kw_layout = QHBoxLayout(self.meta_kw_container)
        self.meta_kw_layout.setContentsMargins(0,0,0,0); self.meta_kw_layout.setSpacing(4)
        self.meta_kw_layout.addStretch()
        v.addWidget(self.meta_kw_container)

        btn_save = QPushButton("💾 Appliquer"); btn_save.clicked.connect(self._save_metadata)
        v.addWidget(btn_save); v.addStretch()
        self.stack.addWidget(w)
        self._meta_keywords = []

    def _add_keyword(self):
        kw = self.meta_keywords_edit.text().strip()
        if not kw or kw in self._meta_keywords: return
        self._meta_keywords.append(kw)
        self.meta_keywords_edit.clear()
        self._refresh_keyword_tags()

    def _refresh_keyword_tags(self):
        while self.meta_kw_layout.count()>1:
            item = self.meta_kw_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        for kw in self._meta_keywords:
            chip = QPushButton(f"✕ {kw}")
            chip.setStyleSheet("background:#48426D;color:white;border-radius:10px;padding:2px 8px;font-size:11px;border:none;")
            chip.clicked.connect(lambda _,k=kw: self._remove_keyword(k))
            self.meta_kw_layout.insertWidget(self.meta_kw_layout.count()-1, chip)

    def _remove_keyword(self, kw):
        if kw in self._meta_keywords: self._meta_keywords.remove(kw)
        self._refresh_keyword_tags()

    def _save_metadata(self):
        d = self.current_item_data
        if not d: return
        d.include_in_compile = self.meta_compile.isChecked()
        d.keywords = list(self._meta_keywords)
        lbl_data = self.meta_label.currentData(Qt.ItemDataRole.UserRole)
        d.label = lbl_data if lbl_data else self.meta_label.currentText()
        # Save type and status from editable combos
        if hasattr(d,"type_item"): d.type_item = self.meta_type_combo.currentText()
        if hasattr(d,"status"):    d.status    = self.meta_status_combo.currentText()
        # Sync to hidden ins_type/ins_status for collect_properties
        self.ins_type.blockSignals(True); self.ins_type.setCurrentText(d.type_item if hasattr(d,"type_item") else ""); self.ins_type.blockSignals(False)
        self.ins_status.blockSignals(True); self.ins_status.setCurrentText(d.status if hasattr(d,"status") else ""); self.ins_status.blockSignals(False)

        # Notify parent to refresh views (BUG-03)
        p = self.parent()
        while p:
            if hasattr(p, "save_inspector"):
                p.save_inspector()
                break
            p = p.parent()

    # ── Tab 4 : Versions ─────────────────────────────────────────────────
    def _build_versions_tab(self):
        w = QWidget(); v = QVBoxLayout(w); v.setContentsMargins(8,8,8,8); v.setSpacing(6)
        v.addWidget(QLabel("<b>🕐 Versions figées</b>"))
        v.addWidget(QLabel("<small>Figez un instantané pour pouvoir le restaurer.\n◀ = version active (contenu identique).</small>"))
        self.ver_list = QListWidget(); self.ver_list.setWordWrap(True); v.addWidget(self.ver_list,1)
        btns = QHBoxLayout()
        btn_f = QPushButton("❄ Figer");     btn_f.clicked.connect(self._freeze_version)
        btn_r = QPushButton("♻ Restaurer"); btn_r.clicked.connect(self._restore_version)
        btn_d = QPushButton("🗑");          btn_d.clicked.connect(self._del_version); btn_d.setFixedWidth(32)
        btns.addWidget(btn_f,1); btns.addWidget(btn_r); btns.addWidget(btn_d)
        v.addLayout(btns)
        self.stack.addWidget(w)

    def _freeze_version(self):
        d = self.current_item_data
        if not d: return
        title,ok = QInputDialog.getText(self,"Figer une version","Titre de la version :")
        if not ok or not title: return
        d.versions.append({
            "date":datetime.now().strftime("%Y-%m-%d %H:%M"),
            "title":title,"content":d.content,"synopsis":d.synopsis,
        })
        self._refresh_versions()

    def _restore_version(self):
        d = self.current_item_data
        if not d: return
        row = self.ver_list.currentRow()
        if row<0: return
        true_idx = len(d.versions)-1-row
        ver = d.versions[true_idx]
        reply = QMessageBox.question(self,"Restaurer",f"Restaurer la version « {ver['title']} » ?")
        if reply==QMessageBox.StandardButton.Yes:
            d.content  = ver["content"]
            d.synopsis = ver["synopsis"]
            # Rafraîchir la liste des versions immédiatement
            self._refresh_versions()
            # Mettre à jour synopsis dans l'onglet Notes
            self.ins_synopsis.blockSignals(True)
            self.ins_synopsis.setPlainText(d.synopsis)
            self.ins_synopsis.blockSignals(False)
            # Recharger l'éditeur
            p = self.parent()
            while p:
                if hasattr(p,"reload_current_item"): p.reload_current_item(); break
                p = p.parent()

    def _del_version(self):
        d = self.current_item_data
        if not d: return
        row = self.ver_list.currentRow()
        if row<0: return
        true_idx = len(d.versions)-1-row
        del d.versions[true_idx]
        self._refresh_versions()

    def _refresh_versions(self):
        self.ver_list.clear()
        if not self.current_item_data: return
        d = self.current_item_data
        current_content = d.content
        for idx, ver in enumerate(reversed(d.versions)):
            words = len(ver.get("content","").split())
            chars = len(ver.get("content",""))
            is_current = (ver.get("content","") == current_content)
            marker = "  ◀ active" if is_current else ""
            # 2-line display: date+title on line 1, stats on line 2
            line1 = f"[{ver['date']}]  {ver['title']}{marker}"
            line2 = f"   {words} mots · {chars} car."
            item = QListWidgetItem(f"{line1}\n{line2}")
            if is_current:
                item.setForeground(QBrush(QColor("#F0C38E")))
                font = item.font(); font.setBold(True); item.setFont(font)
            self.ver_list.addItem(item)

    # ── Tab 5 : Commentaires ─────────────────────────────────────────────
    def _build_comments_tab(self):
        w = QWidget(); v = QVBoxLayout(w); v.setContentsMargins(8,8,8,8); v.setSpacing(6)
        v.addWidget(QLabel("<b>💬 Commentaires</b>"))
        self.comm_list = QListWidget(); self.comm_list.setWordWrap(True); v.addWidget(self.comm_list,1)
        self.comm_edit = QTextEdit(); self.comm_edit.setFixedHeight(70)
        self.comm_edit.setPlaceholderText("Ajouter un commentaire…"); v.addWidget(self.comm_edit)
        btns = QHBoxLayout()
        btn_a = QPushButton("＋ Ajouter"); btn_a.clicked.connect(self._add_comment)
        btn_d = QPushButton("🗑");         btn_d.clicked.connect(self._del_comment); btn_d.setFixedWidth(32)
        btns.addWidget(btn_a,1); btns.addWidget(btn_d); v.addLayout(btns)
        self.stack.addWidget(w)

    def _add_comment(self):
        d = self.current_item_data
        if not d: return
        txt = self.comm_edit.toPlainText().strip()
        if not txt: return
        d.comments.append({"date":datetime.now().strftime("%Y-%m-%d %H:%M"),"text":txt})
        self.comm_edit.clear(); self._refresh_comments()

    def _del_comment(self):
        d = self.current_item_data
        if not d: return
        row = self.comm_list.currentRow()
        if row<0: return
        del d.comments[row]; self._refresh_comments()

    def _refresh_comments(self):
        self.comm_list.clear()
        if not self.current_item_data: return
        for c in self.current_item_data.comments:
            self.comm_list.addItem(f"[{c['date']}]\n{c['text']}")

    def _populate_label_combo(self, current_label, pm):
        """Remplit la combobox étiquette avec carré couleur + nom."""
        self.meta_label.clear()
        for lbl in pm.get_labels():
            name = lbl["name"]; c = lbl["color"]
            # Créer icône carré couleur
            pix = QPixmap(14,14); pix.fill(QColor(c))
            self.meta_label.addItem(QIcon(pix), name)
            idx = self.meta_label.count()-1
            self.meta_label.setItemData(idx, name, Qt.ItemDataRole.UserRole)
        self.meta_label.setCurrentText(current_label)

    # ── API publique ──────────────────────────────────────────────────────
    def load_data(self, item_data, pm: ProjectManager):
        self.current_item_data = item_data
        self.pm = pm
        # Champ Nom (tab Notes)
        self.ins_name.blockSignals(True); self.ins_name.setText(item_data.name); self.ins_name.blockSignals(False)
        # Type/Statut (widgets cachés, utilisés pour collect_properties)
        self.ins_type.blockSignals(True)
        self.ins_type.clear(); self.ins_type.addItems(pm.get_item_types())
        if hasattr(item_data,"type_item"): self.ins_type.setCurrentText(item_data.type_item)
        self.ins_type.blockSignals(False)
        self.ins_status.blockSignals(True)
        self.ins_status.clear(); self.ins_status.addItems(pm.get_statuses())
        if hasattr(item_data,"status"): self.ins_status.setCurrentText(item_data.status)
        self.ins_status.blockSignals(False)
        # Type/Statut éditables dans Métadonnées
        self.meta_type_combo.blockSignals(True)
        self.meta_type_combo.clear(); self.meta_type_combo.addItems(pm.get_item_types())
        self.meta_type_combo.setCurrentText(getattr(item_data,"type_item","—"))
        self.meta_type_combo.blockSignals(False)
        self.meta_status_combo.blockSignals(True)
        self.meta_status_combo.clear(); self.meta_status_combo.addItems(pm.get_statuses())
        self.meta_status_combo.setCurrentText(getattr(item_data,"status","—"))
        self.meta_status_combo.blockSignals(False)
        synopsis = getattr(item_data,"synopsis","")
        notes    = getattr(item_data,"notes","")
        self.ins_synopsis.blockSignals(True); self.ins_synopsis.setPlainText(synopsis); self.ins_synopsis.blockSignals(False)
        self.ins_notes.setPlainText(notes)
        self._refresh_attachments()
        self.meta_created.setText(getattr(item_data,"created_at","")[:10])
        self.meta_modified.setText(getattr(item_data,"modified_at","")[:10])
        self.meta_compile.setChecked(getattr(item_data,"include_in_compile",True))
        self._meta_keywords = list(getattr(item_data,"keywords",[]))
        self._refresh_keyword_tags()
        self._populate_label_combo(getattr(item_data,"label","Aucune"), pm)
        self._refresh_versions()
        self._refresh_comments()

    def collect_properties(self):
        """Returns (name, type_item, status, synopsis, notes)."""
        return (
            self.ins_name.text(),
            self.ins_type.currentText(),
            self.ins_status.currentText(),
            self.ins_synopsis.toPlainText(),
            self.ins_notes.toPlainText(),
        )

    def apply_styles(self, accent_color):
        self.setStyleSheet(f"""
            QWidget#inspector_icon_bar{{background:#2a2a2a;}}
            QPushButton#inspector_tab_btn{{border:none;border-radius:4px;color:#aaa;font-size:14px;}}
            QPushButton#inspector_tab_btn:checked{{background:{accent_color};color:white;}}
            QPushButton#inspector_tab_btn:hover{{background:rgba(255,255,255,0.1);}}
        """)


# ─────────────────────────────────────────────────────────────────────────────
#  ÉDITEUR GÉNÉRIQUE POUR CARTES (personnage, lieu, note, idée, référence)
# ─────────────────────────────────────────────────────────────────────────────

CARD_FIELDS = {
    "Personnage": ["Surnom","Rôle","Âge","Genre","Apparence physique","Personnalité",
                   "Histoire","Motivations","Arc narratif","Relations","Secrets","Citations clés","Notes"],
    "Lieu":       ["Type","Pays / Région","Description physique","Ambiance / Atmosphère",
                   "Histoire du lieu","Habitants / Fréquentation","Rôle dans l'histoire","Scènes associées","Notes"],
    "Note":       ["Résumé"],
    "Recherche":  ["Source","Résumé","Lien URL"],
    "Idée":       ["Résumé"],
    "Référence":  ["Auteur","Source","Type","Résumé","URL"],
}
LONG_FIELDS = {"Histoire","Personnalité","Arc narratif","Relations","Secrets","Notes",
               "Description physique","Ambiance / Atmosphère","Histoire du lieu",
               "Résumé","Inhabitants","Fréquentation"}


class CardEditorPanel(QWidget):
    """Panneau d'édition pour un SimpleCardData."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_card = None
        self._build()

    def _build(self):
        v = QVBoxLayout(self); v.setContentsMargins(0,0,0,0)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.inner = QWidget()
        self.inner_v = QVBoxLayout(self.inner); self.inner_v.setContentsMargins(32,24,32,24)
        self.inner_v.setSpacing(10)
        scroll.setWidget(self.inner)
        v.addWidget(scroll)
        self._title_label = None

    def load_card(self, card: SimpleCardData):
        self.current_card = card
        while self.inner_v.count():
            item = self.inner_v.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        if not card: return
        if card._is_folder:
            self._title_label = None
            self.inner_v.addWidget(QLabel(f"<b style='font-size:18px'>📁 {card.name}</b>"))
            self.inner_v.addStretch(); return
        # Titre
        self._title_label = QLabel(f"<b style='font-size:18px'>{card.icon} {card.name}</b>")
        self.inner_v.addWidget(self._title_label)
        # Étoiles pour Idées
        if card.kind == "Idée":
            star_row = QHBoxLayout()
            star_row.addWidget(QLabel("Note :"))
            self._star_btns = []
            for i in range(1,6):
                sb = QPushButton("★" if i<=card.rating else "☆")
                sb.setFixedSize(28,28)
                sb.setStyleSheet(f"color:{'#F0C38E' if i<=card.rating else '#888'};font-size:18px;border:none;background:transparent;")
                sb.clicked.connect(lambda _,r=i,c=card: self._set_rating(c,r))
                star_row.addWidget(sb); self._star_btns.append(sb)
            star_row.addStretch()
            star_w = QWidget(); star_w.setLayout(star_row)
            self.inner_v.addWidget(star_w)
        # Champs
        fields = CARD_FIELDS.get(card.kind, ["Titre","Contenu"])
        self.field_editors = {}
        for field in fields:
            lbl = QLabel(field)
            if field in LONG_FIELDS:
                ed = QTextEdit(); ed.setPlainText(card.fields.get(field,"")); ed.setFixedHeight(90)
            else:
                ed = QLineEdit(); ed.setText(card.fields.get(field,""))
            self.field_editors[field] = ed
            self.inner_v.addWidget(lbl); self.inner_v.addWidget(ed)
        # Contenu libre
        self.inner_v.addWidget(QLabel("<b>Contenu / Notes libres</b>"))
        self.content_edit = QTextEdit(); self.content_edit.setPlainText(card.content or "")
        self.content_edit.setMinimumHeight(120)
        self.inner_v.addWidget(self.content_edit)
        btn_save = QPushButton("💾 Sauvegarder")
        btn_save.clicked.connect(self._save)
        self.inner_v.addWidget(btn_save)
        self.inner_v.addStretch()

    def refresh_title(self, card: "SimpleCardData"):
        """Met à jour le label titre sans recharger toute la fiche."""
        if not hasattr(self,"_title_label") or not self._title_label: return
        self._title_label.setText(f"<b style='font-size:18px'>{card.icon} {card.name}</b>")

    def _set_rating(self, card, r):
        card.rating = r
        # Refresh stars
        if hasattr(self,"_star_btns"):
            for i,sb in enumerate(self._star_btns):
                sb.setText("★" if i<r else "☆")
                sb.setStyleSheet(f"color:{'#F0C38E' if i<r else '#888'};font-size:18px;border:none;background:transparent;")

    def _save(self):
        if not self.current_card or self.current_card._is_folder: return
        for field, ed in self.field_editors.items():
            self.current_card.fields[field] = ed.toPlainText() if isinstance(ed,QTextEdit) else ed.text()
        self.current_card.content = self.content_edit.toPlainText()
        self.current_card.modified_at = datetime.now().isoformat()
        # Notifier le parent pour rafraîchir l'arbre si le nom a changé
        p = self.parent()
        while p:
            if hasattr(p,"refresh_card_tree_node"):
                p.refresh_card_tree_node(self.current_card)
                break
            p = p.parent()


# ─────────────────────────────────────────────────────────────────────────────
#  VUE LISTE — arborescence avec colonnes (Titre, Étiquette, Statut, Type)
# ─────────────────────────────────────────────────────────────────────────────

class ListViewTree(QTreeWidget):
    def dropEvent(self, event):
        super().dropEvent(event)
        # Find the ListViewWidget container to trigger sync
        p = self.parentWidget()
        while p:
            if hasattr(p, "_on_rows_moved"):
                p._on_rows_moved()
                break
            p = p.parentWidget()

class ListViewWidget(QWidget):
    """Vue Liste : arborescence déroulable avec colonnes de métadonnées inline."""

    HEADERS = ["Titre / Synopsis", "Étiquette", "Statut", "Type"]

    def __init__(self, pm: ProjectManager, parent=None):
        super().__init__(parent)
        self.pm = pm
        self._uid_to_node   = {}   # uid → QTreeWidgetItem dans la liste
        self._uid_to_data   = {}   # uid → ItemData (ref directe pour éviter corruption)
        self._app_node_cache= {}   # uid → nœud arbre principal
        self._build()

    def _build(self):
        v = QVBoxLayout(self); v.setContentsMargins(0,0,0,0)
        self.tree = ListViewTree()
        self.tree.setHeaderLabels(self.HEADERS)
        self.tree.setColumnCount(4)
        hdr = self.tree.header()
        # Toutes les colonnes redimensionnables par l'utilisateur
        for col in range(4):
            hdr.setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive)
        # Proportions initiales (Titre large, Type petit)
        self.tree.setColumnWidth(0, 420)
        self.tree.setColumnWidth(1, 130)
        self.tree.setColumnWidth(2, 120)
        self.tree.setColumnWidth(3, 100)
        hdr.setStretchLastSection(False)
        self.tree.setRootIsDecorated(True)
        self.tree.setAlternatingRowColors(True)
        self.tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tree.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tree.setUniformRowHeights(False)
        # UI-01: surbrillance uniforme (couvre aussi le chevron)
        self.tree.setStyleSheet("""
            QTreeView::branch { background: transparent; }
            QTreeView::item:selected { background: palette(highlight); color: palette(highlighted-text); }
            QTreeView::branch:selected { background: palette(highlight); }
        """)
        # Drag & drop pour réordonner
        self.tree.setDragEnabled(True)
        self.tree.setAcceptDrops(True)
        self.tree.setDropIndicatorShown(True)
        self.tree.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.tree.itemClicked.connect(self._on_item_click)
        self.tree.itemDoubleClicked.connect(self._on_item_dbl)
        self.tree.model().rowsMoved.connect(self._on_rows_moved)
        v.addWidget(self.tree)

    def _get_numbering(self, app_node):
        """Calcule la numérotation X.Y.Z depuis le nœud de l'arbre principal."""
        p = app_node.parent()
        if p is None: return ""
        idx = p.indexOfChild(app_node)+1
        par = self._get_numbering(p)
        return f"{par}{idx}." if par else f"{idx}."

    def _make_label_widget(self, data, pm):
        lc = QComboBox()
        for lbl in pm.get_labels():
            pix = QPixmap(14,14); pix.fill(QColor(lbl["color"]))
            lc.addItem(QIcon(pix), lbl["name"])
            lc.setItemData(lc.count()-1, lbl["name"], Qt.ItemDataRole.UserRole)
        lc.setCurrentText(data.label)
        uid = data.uid
        def on_label(txt):
            d = self._uid_to_data.get(uid)
            if d: d.label = txt; self._refresh_item_colors(d)
        lc.currentTextChanged.connect(on_label)
        return lc

    def _make_status_widget(self, data, pm):
        sc = QComboBox(); sc.addItems(pm.get_statuses()); sc.setCurrentText(data.status)
        uid = data.uid
        sc.currentTextChanged.connect(lambda txt: setattr(self._uid_to_data.get(uid, data),"status",txt) if self._uid_to_data.get(uid) else None)
        return sc

    def _make_type_widget(self, data, pm):
        tc = QComboBox(); tc.addItems(pm.get_item_types()); tc.setCurrentText(data.type_item)
        uid = data.uid
        tc.currentTextChanged.connect(lambda txt: setattr(self._uid_to_data.get(uid, data),"type_item",txt) if self._uid_to_data.get(uid) else None)
        return tc

    def _refresh_item_colors(self, data):
        item = self._uid_to_node.get(data.uid)
        if not item: return
        tc = getattr(self, "_theme_text_color", "#222222")
        item.setForeground(0, QBrush(QColor(tc)))

    def _add_tree_item(self, parent_widget, app_node, pm, prefix=""):
        """Ajoute récursivement un nœud depuis l'arbre principal dans la vue liste."""
        data = app_node.data(0, Qt.ItemDataRole.UserRole)
        if not isinstance(data, ItemData): return None
        num = self._get_numbering(app_node).rstrip(".")
        icon = app_node.text(0).split()[0] if app_node.text(0) else "📄"
        title = f"{num}  {icon} {data.name}" if num else f"{icon} {data.name}"
        syn = (data.synopsis[:100]+"…") if len(data.synopsis)>100 else data.synopsis

        list_item = QTreeWidgetItem(parent_widget)
        # Col 0 : titre + synopsis, sans icône couleur
        list_item.setText(0, title + ("\n" + syn if syn else ""))
        list_item.setData(0, Qt.ItemDataRole.UserRole, data.uid)
        # Stocker les références directes pour éviter confusion parent/enfant
        self._uid_to_node[data.uid]   = list_item
        self._uid_to_data[data.uid]   = data
        self._app_node_cache[data.uid]= app_node
        tc = getattr(self, "_theme_text_color", "#222222")
        list_item.setForeground(0, QBrush(QColor(tc)))

        # Widgets inline cols 1-3 alignés en haut dans un conteneur
        uid = data.uid
        for col_idx, widget in enumerate([
            self._make_label_widget(data, pm),
            self._make_status_widget(data, pm),
            self._make_type_widget(data, pm),
        ], start=1):
            widget.setFixedHeight(26)
            container = QWidget()
            cl = QVBoxLayout(container)
            cl.setContentsMargins(2, 2, 2, 2); cl.setSpacing(0)
            cl.addWidget(widget); cl.addStretch()
            self.tree.setItemWidget(list_item, col_idx, container)

        # Enfants récursifs
        for i in range(app_node.childCount()):
            self._add_tree_item(list_item, app_node.child(i), pm)
        list_item.setExpanded(True)
        return list_item

    def set_theme_text_color(self, color):
        self._theme_text_color = color

    def refresh(self, parent_node, pm):
        self.pm = pm
        self._uid_to_node   = {}
        self._uid_to_data   = {}
        self._app_node_cache= {}
        self.tree.clear()
        if not parent_node: return
        for i in range(parent_node.childCount()):
            self._add_tree_item(self.tree.invisibleRootItem(), parent_node.child(i), pm)

    def refresh_row_from_inspector(self, data: ItemData):
        """Met à jour le texte col0 et les combos d'une ligne."""
        item = self._uid_to_node.get(data.uid)
        if not item: return
        # Update _uid_to_data with latest data
        self._uid_to_data[data.uid] = data
        # Col 0
        app_node = self._app_node_cache.get(data.uid)
        num = self._get_numbering(app_node).rstrip(".") if app_node else ""
        icon_txt = app_node.text(0).split()[0] if app_node and app_node.text(0) else "📄"
        title = f"{num}  {icon_txt} {data.name}" if num else f"{icon_txt} {data.name}"
        syn = (data.synopsis[:100]+"…") if len(data.synopsis)>100 else data.synopsis
        item.setText(0, title + ("\n" + syn if syn else ""))
        # Combos dans containers (col widget → QWidget → QComboBox)
        for col_idx, val in [(1,data.label),(2,data.status),(3,data.type_item)]:
            container = self.tree.itemWidget(item, col_idx)
            if container:
                for child in container.findChildren(QComboBox):
                    child.blockSignals(True); child.setCurrentText(val); child.blockSignals(False)
        self._refresh_item_colors(data)

    def _notify_app(self, attr, node):
        p = self.parent()
        while p:
            if hasattr(p, attr): getattr(p, attr)(node); break
            p = p.parent()

    def _on_rows_moved(self, *args):
        """Propage le réordonnancement ET les changements de parenté vers l'arbre principal."""
        # Reconstruire l'ordre complet en lisant la listview tree
        p = self.parent()
        while p:
            if hasattr(p, "sync_tree_order_from_listview"):
                p.sync_tree_order_from_listview(self)
                break
            p = p.parent()

    def _get_app_node_for_uid(self, uid):
        """Retrouve le nœud de l'arbre principal depuis un uid."""
        p = self.parent()
        while p:
            if hasattr(p, "_find_tree_node_by_uid"):
                return p._find_tree_node_by_uid(uid)
            p = p.parent()
        return None

    def _on_item_click(self, list_item, col):
        uid = list_item.data(0, Qt.ItemDataRole.UserRole)
        if not uid: return
        app_node = self._app_node_cache.get(uid) or self._get_app_node_for_uid(uid)
        if app_node:
            # Ensure the app node carries the CORRECT data object (not a stale one)
            correct_data = self._uid_to_data.get(uid)
            if correct_data: app_node.setData(0, Qt.ItemDataRole.UserRole, correct_data)
            self._notify_app("update_inspector_only", app_node)

    def _on_item_dbl(self, list_item, col):
        uid = list_item.data(0, Qt.ItemDataRole.UserRole)
        if not uid: return
        app_node = getattr(self,"_app_node_cache",{}).get(uid) or self._get_app_node_for_uid(uid)
        if app_node: self._notify_app("open_item_in_editor", app_node)


# ─────────────────────────────────────────────────────────────────────────────
#  DIALOGUES
# ─────────────────────────────────────────────────────────────────────────────

class NewProjectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nouveau Projet"); self.setFixedSize(480,300)
        layout = QVBoxLayout(self); layout.setSpacing(12)
        layout.addWidget(QLabel("<b style='font-size:16px'>Créer un nouveau projet</b>"))
        form = QFormLayout()
        self.title_edit  = QLineEdit("Mon Roman")
        self.author_edit = QLineEdit()
        self.goal_spin   = QSpinBox(); self.goal_spin.setRange(100,5000000); self.goal_spin.setValue(80000)
        form.addRow("Titre :",self.title_edit); form.addRow("Auteur :",self.author_edit)
        form.addRow("Objectif (mots) :",self.goal_spin)
        layout.addLayout(form)
        dir_row = QHBoxLayout()
        self.dir_edit = QLineEdit(str(Path.home()/"Documents"))
        btn_b = QPushButton("Parcourir…"); btn_b.clicked.connect(self._browse)
        dir_row.addWidget(QLabel("Dossier :")); dir_row.addWidget(self.dir_edit); dir_row.addWidget(btn_b)
        layout.addLayout(dir_row); layout.addStretch()
        btns = QHBoxLayout()
        ok = QPushButton("Créer"); ok.clicked.connect(self.accept)
        cancel = QPushButton("Annuler"); cancel.clicked.connect(self.reject)
        btns.addStretch(); btns.addWidget(cancel); btns.addWidget(ok)
        layout.addLayout(btns)

    def _browse(self):
        d = QFileDialog.getExistingDirectory(self,"Choisir le dossier parent")
        if d: self.dir_edit.setText(d)

    def get_values(self):
        base = Path(self.dir_edit.text())
        folder = base/self.title_edit.text().replace(" ","_")
        return str(folder),self.title_edit.text(),self.author_edit.text(),self.goal_spin.value()


class GoalDialog(QDialog):
    def __init__(self, item_data: ItemData, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Objectif — {item_data.name}"); self.setFixedSize(360,200)
        v = QVBoxLayout(self)
        v.addWidget(QLabel(f"<b>Objectif pour : {item_data.name}</b>"))
        self.unit_combo = QComboBox(); self.unit_combo.addItems(["mots","caractères"])
        self.unit_combo.setCurrentText(item_data.goal_unit)
        self.val_spin = QSpinBox(); self.val_spin.setRange(0,1000000)
        self.val_spin.setValue(item_data.word_goal if item_data.goal_unit=="mots" else item_data.char_goal)
        form = QFormLayout()
        form.addRow("Unité :",self.unit_combo); form.addRow("Valeur (0=aucun) :",self.val_spin)
        v.addLayout(form)
        btns = QHBoxLayout()
        ok = QPushButton("OK"); ok.clicked.connect(self.accept)
        cancel = QPushButton("Annuler"); cancel.clicked.connect(self.reject)
        btns.addStretch(); btns.addWidget(cancel); btns.addWidget(ok); v.addLayout(btns)

    def get_values(self): return self.unit_combo.currentText(), self.val_spin.value()


class ListManagementDialog(QDialog):
    def __init__(self, pm: ProjectManager, parent=None):
        super().__init__(parent)
        self.pm = pm; self.setWindowTitle("Paramétrage des listes"); self.setMinimumSize(600,500)
        v = QVBoxLayout(self)
        tabs = QTabWidget()
        tabs.addTab(self._make_simple_tab("statuses","Statuts",pm.get_statuses()),"Statuts")
        tabs.addTab(self._make_simple_tab("item_types","Types",pm.get_item_types()),"Types")
        tabs.addTab(self._make_label_tab(),"Étiquettes")
        v.addWidget(tabs)
        btn = QPushButton("Fermer"); btn.clicked.connect(self.accept)
        btns = QHBoxLayout(); btns.addStretch(); btns.addWidget(btn); v.addLayout(btns)

    def _make_simple_tab(self, key, title, items):
        w = QWidget(); v = QVBoxLayout(w)
        v.addWidget(QLabel(f"<b>{title}</b>"))
        lst = QListWidget()
        for it in items: lst.addItem(it)
        v.addWidget(lst)
        row = QHBoxLayout()
        edit = QLineEdit(); edit.setPlaceholderText("Nouveau…")
        btn_add = QPushButton("＋"); btn_del = QPushButton("🗑")
        row.addWidget(edit,1); row.addWidget(btn_add); row.addWidget(btn_del)
        v.addLayout(row)
        def add():
            txt=edit.text().strip()
            if txt and txt not in [lst.item(i).text() for i in range(lst.count())]:
                lst.addItem(txt); edit.clear()
                self.pm.config[key]=[lst.item(i).text() for i in range(lst.count())]
        def rem():
            r=lst.currentRow()
            if r>=0:
                lst.takeItem(r)
                self.pm.config[key]=[lst.item(i).text() for i in range(lst.count())]
        btn_add.clicked.connect(add); btn_del.clicked.connect(rem)
        return w

    def _make_label_tab(self):
        w = QWidget(); v = QVBoxLayout(w)
        v.addWidget(QLabel("<b>Étiquettes couleur</b>"))
        self.label_list = QListWidget(); self._refresh_label_list()
        v.addWidget(self.label_list)
        row = QHBoxLayout()
        self.lbl_name = QLineEdit(); self.lbl_name.setPlaceholderText("Nom de l'étiquette…")
        self.lbl_color_btn = QPushButton("🎨 Couleur")
        self.lbl_color_btn.setProperty("color","#888888")
        self.lbl_color_btn.clicked.connect(self._pick_color)
        btn_add = QPushButton("＋ Ajouter"); btn_add.clicked.connect(self._add_label)
        btn_del = QPushButton("🗑"); btn_del.clicked.connect(self._del_label); btn_del.setFixedWidth(32)
        row.addWidget(self.lbl_name,1); row.addWidget(self.lbl_color_btn); row.addWidget(btn_add); row.addWidget(btn_del)
        v.addLayout(row)
        return w

    def _pick_color(self):
        c = QColorDialog.getColor(QColor(self.lbl_color_btn.property("color")))
        if c.isValid():
            self.lbl_color_btn.setProperty("color",c.name())
            fg = label_text_color(c.name())
            self.lbl_color_btn.setStyleSheet(f"background:{c.name()};color:{fg};")

    def _add_label(self):
        name = self.lbl_name.text().strip()
        if not name: return
        color = self.lbl_color_btn.property("color") or "#888888"
        labels = self.pm.config.get("labels",list(DEFAULT_LABELS))
        labels.append({"name":name,"color":color})
        self.pm.config["labels"] = labels
        self._refresh_label_list(); self.lbl_name.clear()

    def _del_label(self):
        row = self.label_list.currentRow()
        if row<0: return
        labels = self.pm.config.get("labels",list(DEFAULT_LABELS))
        if row<len(labels): del labels[row]
        self.pm.config["labels"]=labels; self._refresh_label_list()

    def _refresh_label_list(self):
        self.label_list.clear()
        for lbl in self.pm.get_labels():
            c = lbl["color"]
            pix = QPixmap(16,16); pix.fill(QColor(c))
            item = QListWidgetItem(QIcon(pix), lbl["name"])
            self.label_list.addItem(item)


class ConfigDialog(QDialog):
    def __init__(self, parent, start_tab=0):
        super().__init__(parent)
        self.app = parent; self.setWindowTitle("Configuration — Scriptura"); self.setMinimumSize(750,550)
        self.main_vbox = QVBoxLayout(self)
        
        content_layout = QHBoxLayout()
        self.nav = QListWidget(); self.nav.setFixedWidth(175)
        self.nav.addItems(["🎨  Thème","🔤  Éditeur","📁  Projet","📋  Listes","☁️  Synchronisation","⌨️  Raccourcis","🌲  Arborescence"])
        self.nav.currentRowChanged.connect(lambda i: self.stack.setCurrentIndex(i))
        self.stack = QStackedWidget()
        content_layout.addWidget(self.nav); content_layout.addWidget(self.stack)
        self.main_vbox.addLayout(content_layout)
        
        # Buttons area
        self._build_bottom_buttons()
        
        self._build_theme_panel(); self._build_editor_panel(); self._build_project_panel()
        self._build_lists_panel(); self._build_cloud_panel()
        self._build_shortcuts_panel(); self._build_tree_panel()
        self.nav.setCurrentRow(start_tab)

    def _build_bottom_buttons(self):
        btn_box = QHBoxLayout()
        self.btn_ok = QPushButton("OK"); self.btn_ok.clicked.connect(self._on_ok)
        self.btn_cancel = QPushButton("Annuler"); self.btn_cancel.clicked.connect(self.reject)
        self.btn_apply = QPushButton("Appliquer"); self.btn_apply.clicked.connect(self._on_apply)
        btn_box.addStretch()
        btn_box.addWidget(self.btn_ok); btn_box.addWidget(self.btn_cancel); btn_box.addWidget(self.btn_apply)
        self.main_vbox.addLayout(btn_box)

    def _on_ok(self):
        self._on_apply()
        self.accept()

    def _on_apply(self):
        # Trigger all apply methods
        self._apply_editor()
        self._apply_project()
        self._apply_cloud()
        self._apply_tree()
        # Theme is applied in real-time but we ensure it's saved
        self.app.pm.config["theme"] = self.app.current_theme

    def _wrap_tab(self, layout):
        container = QGroupBox()
        container.setLayout(layout)
        # Use a border style similar to the tabs
        container.setStyleSheet("QGroupBox { border: 1px solid #ccc; border-radius: 5px; margin-top: 10px; padding: 10px; }")
        outer_v = QVBoxLayout()
        outer_v.addWidget(container)
        w = QWidget()
        w.setLayout(outer_v)
        return w

    def _build_theme_panel(self):
        v = QVBoxLayout()
        v.addWidget(QLabel("<b>Thèmes visuels</b>"))
        v.addWidget(QLabel("<small>Un seul thème actif à la fois.</small>"))
        self._tbg = QButtonGroup(self); self._tbg.setExclusive(True)
        for name,colors in self.app.themes.items():
            rw = QWidget(); r = QHBoxLayout(rw); r.setContentsMargins(0,2,0,2)
            for key in ["sidebar","editor_bg","highlight"]:
                dot = QFrame(); dot.setFixedSize(18,18)
                dot.setStyleSheet(f"background:{colors[key]};border-radius:9px;border:1px solid #555;")
                r.addWidget(dot)
            btn = QRadioButton(f"  {name}"); btn.setChecked(name==self.app.current_theme)
            btn.toggled.connect(lambda checked,n=name: self.app.apply_theme(n) if checked else None)
            self._tbg.addButton(btn); r.addWidget(btn,1); v.addWidget(rw)
        v.addStretch()
        self.stack.addWidget(self._wrap_tab(v))

    def _build_editor_panel(self):
        v = QVBoxLayout(); v.addWidget(QLabel("<b>Éditeur</b>"))
        form = QFormLayout(); cfg = self.app.pm.config
        self.cfg_font = QFontComboBox(); self.cfg_font.setCurrentFont(QFont(cfg.get("font_family","Georgia")))
        self.cfg_size = QSpinBox(); self.cfg_size.setRange(8,30); self.cfg_size.setValue(cfg.get("font_size",13))
        self.cfg_para = QComboBox(); self.cfg_para.addItems(["1.0","1.2","1.5","2.0"]); self.cfg_para.setCurrentText(str(cfg.get("paragraph_spacing",1.5)))
        self.cfg_width= QSpinBox(); self.cfg_width.setRange(400,2000); self.cfg_width.setValue(cfg.get("editor_width",700)); self.cfg_width.setSuffix(" px")
        self.cfg_tw   = QCheckBox("Mode machine à écrire"); self.cfg_tw.setChecked(cfg.get("typewriter_mode",False))
        self.cfg_wc   = QCheckBox("Afficher le compteur de mots"); self.cfg_wc.setChecked(cfg.get("show_word_count",True))
        form.addRow("Police :",self.cfg_font); form.addRow("Taille :",self.cfg_size)
        form.addRow("Interligne :",self.cfg_para); form.addRow("Largeur max :",self.cfg_width)
        v.addLayout(form); v.addWidget(self.cfg_tw); v.addWidget(self.cfg_wc)
        v.addStretch()
        self.stack.addWidget(self._wrap_tab(v))

    def _apply_editor(self):
        cfg=self.app.pm.config
        cfg["font_family"]=self.cfg_font.currentFont().family()
        cfg["font_size"]=self.cfg_size.value()
        cfg["paragraph_spacing"]=float(self.cfg_para.currentText())
        cfg["editor_width"]=self.cfg_width.value()
        cfg["typewriter_mode"]=self.cfg_tw.isChecked()
        cfg["show_word_count"]=self.cfg_wc.isChecked()
        self.app.apply_editor_config()

    def _build_project_panel(self):
        v=QVBoxLayout(); v.addWidget(QLabel("<b>Métadonnées du projet</b>"))
        pd=self.app.pm.project_data; form=QFormLayout()
        self.cfg_title=QLineEdit(pd.title); self.cfg_author=QLineEdit(pd.author)
        self.cfg_genre=QComboBox(); self.cfg_genre.setEditable(True); self.cfg_genre.addItems(GENRES)
        self.cfg_genre.setCurrentText(pd.genre or GENRES[0])
        self.cfg_goal=QSpinBox(); self.cfg_goal.setRange(100,5000000); self.cfg_goal.setValue(pd.word_goal); self.cfg_goal.setSuffix(" mots")
        self.cfg_status=QComboBox(); self.cfg_status.addItems(["En cours","Terminé","En révision","Abandonné"]); self.cfg_status.setCurrentText(pd.status)
        self.cfg_desc=QTextEdit(pd.description); self.cfg_desc.setFixedHeight(80)
        self.cfg_autosave=QSpinBox(); self.cfg_autosave.setRange(0,600); self.cfg_autosave.setValue(self.app.pm.config.get("autosave_interval",60)); self.cfg_autosave.setSuffix(" s (0=désactivé)")
        for lbl,w2 in [("Titre :",self.cfg_title),("Auteur :",self.cfg_author),("Genre :",self.cfg_genre),("Objectif :",self.cfg_goal),("Statut :",self.cfg_status),("Description :",self.cfg_desc),("Sauvegarde auto :",self.cfg_autosave)]:
            form.addRow(lbl,w2)
        v.addLayout(form)
        v.addStretch()
        self.stack.addWidget(self._wrap_tab(v))

    def _apply_project(self):
        pd=self.app.pm.project_data
        pd.title=self.cfg_title.text(); pd.author=self.cfg_author.text()
        pd.genre=self.cfg_genre.currentText(); pd.word_goal=self.cfg_goal.value()
        pd.status=self.cfg_status.currentText(); pd.description=self.cfg_desc.toPlainText()
        self.app.pm.config["autosave_interval"]=self.cfg_autosave.value()
        self.app.setup_autosave(); self.app.refresh_project_page()

    def _build_lists_panel(self):
        """Listes directement intégrées sans bouton intermédiaire."""
        v = QVBoxLayout()
        v.addWidget(QLabel("<b>📋 Paramétrage des listes</b>"))
        tabs = QTabWidget()
        # Statuts
        tabs.addTab(self._make_editable_list_tab("statuses","Statuts",
            self.app.pm.get_statuses()), "Statuts")
        # Types
        tabs.addTab(self._make_editable_list_tab("item_types","Types",
            self.app.pm.get_item_types()), "Types")
        # Étiquettes
        tabs.addTab(self._make_label_inline_tab(), "Étiquettes")
        # Lieux de séance
        tabs.addTab(self._make_editable_list_tab("session_locations","Lieux de séance",
            self.app.pm.get_session_locations()), "Lieux séance")
        v.addWidget(tabs, 1)
        self.stack.addWidget(self._wrap_tab(v))

    def _make_editable_list_tab(self, cfg_key, title, items):
        w = QWidget(); v = QVBoxLayout(w); v.setSpacing(4)
        lst = QListWidget()
        for it in items: lst.addItem(it)
        v.addWidget(lst, 1)
        row = QHBoxLayout()
        edit = QLineEdit(); edit.setPlaceholderText(f"Nouveau…")
        btn_add = QPushButton("＋"); btn_add.setFixedWidth(32)
        btn_del = QPushButton("🗑"); btn_del.setFixedWidth(32)
        btn_up  = QPushButton("▲"); btn_up.setFixedWidth(32)
        btn_dn  = QPushButton("▼"); btn_dn.setFixedWidth(32)
        row.addWidget(edit,1); row.addWidget(btn_add); row.addWidget(btn_del)
        row.addWidget(btn_up); row.addWidget(btn_dn)
        v.addLayout(row)
        def _save(): self.app.pm.config[cfg_key]=[lst.item(i).text() for i in range(lst.count())]
        def add():
            txt=edit.text().strip()
            if txt and txt not in [lst.item(i).text() for i in range(lst.count())]:
                lst.addItem(txt); edit.clear(); _save()
        def rem():
            r=lst.currentRow()
            if r>=0: lst.takeItem(r); _save()
        def move_up():
            r=lst.currentRow()
            if r>0:
                item=lst.takeItem(r); lst.insertItem(r-1,item)
                lst.setCurrentRow(r-1); _save()
        def move_dn():
            r=lst.currentRow()
            if r<lst.count()-1:
                item=lst.takeItem(r); lst.insertItem(r+1,item)
                lst.setCurrentRow(r+1); _save()
        btn_add.clicked.connect(add); btn_del.clicked.connect(rem)
        btn_up.clicked.connect(move_up); btn_dn.clicked.connect(move_dn)
        edit.returnPressed.connect(add)
        return w

    def _make_label_inline_tab(self):
        w = QWidget(); v = QVBoxLayout(w); v.setSpacing(4)
        self._lbl_list = QListWidget()
        self._refresh_inline_label_list()
        v.addWidget(self._lbl_list, 1)
        row = QHBoxLayout()
        self._lbl_name_edit = QLineEdit(); self._lbl_name_edit.setPlaceholderText("Nom…")
        self._lbl_color_val = "#888888"
        self._lbl_color_btn = QPushButton("🎨"); self._lbl_color_btn.setFixedWidth(36)
        self._lbl_color_btn.clicked.connect(self._pick_inline_label_color)
        btn_add = QPushButton("＋ Ajouter"); btn_add.clicked.connect(self._add_inline_label)
        btn_del = QPushButton("🗑"); btn_del.setFixedWidth(32); btn_del.clicked.connect(self._del_inline_label)
        row.addWidget(self._lbl_name_edit,1); row.addWidget(self._lbl_color_btn)
        row.addWidget(btn_add); row.addWidget(btn_del)
        v.addLayout(row)
        return w

    def _pick_inline_label_color(self):
        c = QColorDialog.getColor(QColor(self._lbl_color_val), self)
        if c.isValid():
            self._lbl_color_val = c.name()
            fg = label_text_color(c.name())
            self._lbl_color_btn.setStyleSheet(f"background:{c.name()};color:{fg};")

    def _add_inline_label(self):
        name = self._lbl_name_edit.text().strip()
        if not name: return
        lbls = self.app.pm.config.get("labels", list(DEFAULT_LABELS))
        lbls.append({"name": name, "color": self._lbl_color_val})
        self.app.pm.config["labels"] = lbls
        self._refresh_inline_label_list(); self._lbl_name_edit.clear()

    def _del_inline_label(self):
        row = self._lbl_list.currentRow()
        if row < 0: return
        lbls = self.app.pm.config.get("labels", list(DEFAULT_LABELS))
        if row < len(lbls): del lbls[row]
        self.app.pm.config["labels"] = lbls; self._refresh_inline_label_list()

    def _refresh_inline_label_list(self):
        self._lbl_list.clear()
        for lbl in self.app.pm.get_labels():
            c = lbl["color"]
            pix = QPixmap(16,16); pix.fill(QColor(c))
            item = QListWidgetItem(QIcon(pix), lbl["name"])
            self._lbl_list.addItem(item)

    def _build_cloud_panel(self):
        v=QVBoxLayout(); v.addWidget(QLabel("<b>☁️ Synchronisation Cloud</b>"))
        v.addWidget(QLabel("Placez votre dossier projet dans le dossier de votre client cloud.\n"))
        row=QHBoxLayout()
        self.cfg_cloud=QLineEdit(self.app.pm.config.get("cloud_path",""))
        btn_b=QPushButton("Parcourir…"); btn_b.clicked.connect(self._browse_cloud)
        row.addWidget(self.cfg_cloud); row.addWidget(btn_b); v.addLayout(row)
        v.addWidget(QLabel("• Dropbox: ~/Dropbox/\n• Google Drive: ~/Google Drive/\n• KDrive: ~/kdrive/\n• OneDrive: ~/OneDrive/"))
        v.addStretch()
        self.stack.addWidget(self._wrap_tab(v))

    def _browse_cloud(self):
        d=QFileDialog.getExistingDirectory(self,"Choisir le dossier cloud")
        if d: self.cfg_cloud.setText(d)

    def _apply_cloud(self):
        self.app.pm.config["cloud_path"]=self.cfg_cloud.text()
        QMessageBox.information(self,"Cloud","Chemin cloud enregistré.")

    def _build_shortcuts_panel(self):
        v=QVBoxLayout(); v.addWidget(QLabel("<b>Raccourcis clavier</b>"))
        shortcuts=[("Sauvegarder","Ctrl+S"),("Nouveau projet","Ctrl+Shift+N"),("Ouvrir projet","Ctrl+O"),
                   ("Mode Zen","F11"),("Vue Texte","Ctrl+1"),("Vue Cartes","Ctrl+2"),("Vue Liste","Ctrl+3"),
                   ("Annuler","Ctrl+Z"),("Rétablir","Ctrl+Y"),("Gras","Ctrl+B"),("Italique","Ctrl+I")]
        form=QFormLayout()
        for lbl,key in shortcuts: form.addRow(lbl,QLabel(f"<code>{key}</code>"))
        v.addLayout(form); v.addStretch()
        self.stack.addWidget(self._wrap_tab(v))

    def _build_tree_panel(self):
        v=QVBoxLayout(); v.addWidget(QLabel("<b>Arborescence</b>"))
        cfg = self.app.pm.config
        self.cfg_icons=QCheckBox("Afficher les icônes"); self.cfg_icons.setChecked(cfg.get("show_tree_icons", True))
        self.cfg_status=QCheckBox("Afficher le statut"); self.cfg_status.setChecked(cfg.get("show_tree_status", True))
        v.addWidget(self.cfg_icons); v.addWidget(self.cfg_status); v.addStretch()
        self.stack.addWidget(self._wrap_tab(v))

    def _apply_tree(self):
        cfg = self.app.pm.config
        cfg["show_tree_icons"] = self.cfg_icons.isChecked()
        cfg["show_tree_status"] = self.cfg_status.isChecked()
        self.app._rebuild_tree_from_pm()


# ─────────────────────────────────────────────────────────────────────────────
#  PAGE PROJET
# ─────────────────────────────────────────────────────────────────────────────

class ProjectPage(QWidget):
    def __init__(self, pm: ProjectManager, parent=None):
        super().__init__(parent); self.pm=pm; self._build()

    def _build(self):
        scroll=QScrollArea(self); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.Shape.NoFrame)
        inner=QWidget(); v=QVBoxLayout(inner); v.setContentsMargins(60,40,60,40); v.setSpacing(24)
        scroll.setWidget(inner)
        layout=QVBoxLayout(self); layout.setContentsMargins(0,0,0,0); layout.addWidget(scroll)
        self.lbl_title=QLabel(); self.lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_title.setStyleSheet("font-size:32px;font-weight:bold;margin-bottom:4px;")
        v.addWidget(self.lbl_title)
        self.lbl_author=QLabel(); self.lbl_author.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_author.setStyleSheet("font-size:15px;"); v.addWidget(self.lbl_author)
        stats_row=QHBoxLayout(); stats_row.setSpacing(16)
        self.card_words=self._stat_card("Mots écrits","0"); self.card_goal=self._stat_card("Objectif","80 000")
        self.card_pct=self._stat_card("Progression","0 %"); self.card_chapters=self._stat_card("Chapitres","0")
        self.card_scenes=self._stat_card("Scènes","0"); self.card_chars=self._stat_card("Personnages","0")
        for c in [self.card_words,self.card_goal,self.card_pct,self.card_chapters,self.card_scenes,self.card_chars]:
            stats_row.addWidget(c)
        v.addLayout(stats_row)
        v.addWidget(QLabel("<b>Progression vers l'objectif</b>"))
        self.progress_bar=QProgressBar(); self.progress_bar.setRange(0,100); self.progress_bar.setFixedHeight(22)
        v.addWidget(self.progress_bar)
        v.addWidget(QLabel("<b>Description / Synopsis</b>"))
        self.desc_label=QLabel(); self.desc_label.setWordWrap(True); self.desc_label.setStyleSheet("font-size:13px;")
        v.addWidget(self.desc_label)
        info_row=QHBoxLayout(); info_row.setSpacing(20)
        self.lbl_genre=QLabel(); self.lbl_status=QLabel(); self.lbl_date=QLabel()
        for lbl in [self.lbl_genre,self.lbl_status,self.lbl_date]:
            lbl.setStyleSheet("padding:6px 12px;border-radius:4px;font-size:12px;"); info_row.addWidget(lbl)
        info_row.addStretch(); v.addLayout(info_row); v.addStretch()

    def _stat_card(self, label, value):
        frame=QFrame(); frame.setFrameShape(QFrame.Shape.StyledPanel)
        frame.setStyleSheet("border-radius:10px;padding:8px;")
        fl=QVBoxLayout(frame)
        vl=QLabel(value); vl.setAlignment(Qt.AlignmentFlag.AlignCenter); vl.setStyleSheet("font-size:22px;font-weight:bold;")
        ll=QLabel(label); ll.setAlignment(Qt.AlignmentFlag.AlignCenter); ll.setStyleSheet("font-size:11px;")
        fl.addWidget(vl); fl.addWidget(ll); frame._val=vl; return frame

    def refresh(self):
        pd=self.pm.project_data; words=self.pm.total_words(); goal=max(pd.word_goal,1)
        pct=min(int(words/goal*100),100)
        chapters=sum(1 for it in self.pm.items.values() if it.type_item in ("Chapitre","Acte","Partie"))
        scenes=sum(1 for it in self.pm.items.values() if it.type_item in ("Scène","Page","Prologue","Épilogue","Interlude"))
        chars=sum(1 for c in self.pm.cards.values() if c.kind=="Personnage" and not c._is_folder)
        self.lbl_title.setText(pd.title)
        self.lbl_author.setText(f"par {pd.author}" if pd.author else "")
        self.card_words._val.setText(f"{words:,}".replace(","," "))
        self.card_goal._val.setText(f"{goal:,}".replace(","," "))
        self.card_pct._val.setText(f"{pct} %")
        self.card_chapters._val.setText(str(chapters))
        self.card_scenes._val.setText(str(scenes))
        self.card_chars._val.setText(str(chars))
        self.progress_bar.setValue(pct)
        self.desc_label.setText(pd.description or "<i>Aucune description.</i>")
        self.lbl_genre.setText(f"Genre : {pd.genre or '—'}")
        self.lbl_status.setText(f"Statut : {pd.status}")
        self.lbl_date.setText(f"Modifié : {pd.modified_at[:10]}")



class SessionStartDialog(QDialog):
    """Dialogue de démarrage de séance : lieu + scène associée."""
    def __init__(self, pm: "ProjectManager", current_item=None, parent=None):
        super().__init__(parent)
        self.pm = pm
        self.setWindowTitle("Démarrer une séance"); self.setFixedSize(400, 240)
        v = QVBoxLayout(self)
        v.addWidget(QLabel("<b>📊 Démarrer une séance d'écriture</b>"))
        form = QFormLayout()
        # Lieu
        self.loc_combo = QComboBox(); self.loc_combo.setEditable(True)
        self.loc_combo.addItems(pm.get_session_locations())
        form.addRow("Lieu :", self.loc_combo)
        # Scène associée
        self.scene_combo = QComboBox()
        self.scene_combo.addItem("— Aucune —", None)
        # Remplir avec les scènes/chapitres du manuscrit
        def fill_items(pm_items, uids, depth=0):
            for uid in uids:
                d = pm_items.get(uid)
                if not d: continue
                prefix = "  " * depth
                self.scene_combo.addItem(f"{prefix}{d.name}", uid)
                fill_items(pm_items, d.children, depth+1)
        fill_items(pm.items, pm.tree_roots.get("Manuscrit",[]))
        # Pré-sélectionner la scène active
        if current_item:
            cur_data = current_item.data(0, Qt.ItemDataRole.UserRole) if hasattr(current_item,"data") else None
            if hasattr(cur_data,"uid"):
                for i in range(self.scene_combo.count()):
                    if self.scene_combo.itemData(i) == cur_data.uid:
                        self.scene_combo.setCurrentIndex(i); break
        form.addRow("Scène :", self.scene_combo)
        v.addLayout(form)
        v.addStretch()
        btns = QHBoxLayout()
        ok = QPushButton("Démarrer"); ok.clicked.connect(self.accept)
        cancel = QPushButton("Annuler"); cancel.clicked.connect(self.reject)
        btns.addStretch(); btns.addWidget(cancel); btns.addWidget(ok)
        v.addLayout(btns)

    def get_values(self):
        return self.loc_combo.currentText(), self.scene_combo.currentData()


# ─────────────────────────────────────────────────────────────────────────────
#  MODULE SÉANCES D'ÉCRITURE
# ─────────────────────────────────────────────────────────────────────────────

class SessionTracker:
    """Gère le suivi des séances d'écriture."""
    def __init__(self, pm: "ProjectManager"):
        self.pm = pm
        self._start_time  = None
        self._start_words = 0
        self._start_chars = 0
        self._active      = False
        self._scene_uid   = None
        self._location    = ""

    def start(self, words: int, chars: int, scene_uid: str = "", location: str = ""):
        import time
        self._start_time  = time.time()
        self._start_words = words
        self._start_chars = chars
        self._active      = True
        self._scene_uid   = scene_uid
        self._location    = location

    def stop(self, words: int, chars: int) -> dict:
        import time
        if not self._active: return {}
        elapsed = int(time.time() - self._start_time)
        session = {
            "date":       datetime.now().strftime("%Y-%m-%d"),
            "start":      datetime.fromtimestamp(self._start_time).strftime("%H:%M"),
            "end":        datetime.now().strftime("%H:%M"),
            "duration_s": elapsed,
            "words_added": max(0, words - self._start_words),
            "chars_added": max(0, chars - self._start_chars),
            "scene_uid":  self._scene_uid,
            "location":   self._location,
        }
        self._active = False
        self.pm.sessions.append(session)
        return session

    @property
    def active(self): return self._active

    def elapsed_str(self) -> str:
        import time
        if not self._active: return "00:00"
        s = int(time.time() - self._start_time)
        return f"{s//3600:02d}:{(s%3600)//60:02d}:{s%60:02d}" if s>=3600 else f"{s//60:02d}:{s%60:02d}"


class SessionsPanel(QWidget):
    """Panneau d'affichage et de gestion des séances."""

    def __init__(self, pm: "ProjectManager", parent=None):
        super().__init__(parent)
        self.pm = pm
        self._build()

    def _build(self):
        v = QVBoxLayout(self); v.setContentsMargins(24, 16, 24, 16); v.setSpacing(16)

        # Titre
        title = QLabel("<b style='font-size:20px'>📊 Séances d'écriture</b>")
        v.addWidget(title)

        # Filtres
        flt_row = QHBoxLayout()
        self.period_combo = QComboBox()
        self.period_combo.addItems(["7 derniers jours","30 derniers jours","3 mois","6 mois","1 an","Tout"])
        self.period_combo.currentIndexChanged.connect(self._refresh)
        flt_row.addWidget(QLabel("Période :"))
        flt_row.addWidget(self.period_combo)
        flt_row.addStretch()
        v.addLayout(flt_row)

        # Stats rapides
        stats_row = QHBoxLayout(); stats_row.setSpacing(12)
        self._stat_total_sessions = self._stat_card("Séances","0")
        self._stat_total_words    = self._stat_card("Mots écrits","0")
        self._stat_total_time     = self._stat_card("Temps total","0 h")
        self._stat_avg_words      = self._stat_card("Mots/séance","0")
        for c in [self._stat_total_sessions,self._stat_total_words,self._stat_total_time,self._stat_avg_words]:
            stats_row.addWidget(c)
        v.addLayout(stats_row)

        # Graphique (ASCII/SVG simple, pas de dépendance externe)
        self.chart_widget = SessionChartWidget()
        self.chart_widget.setMinimumHeight(180)
        v.addWidget(self.chart_widget)

        # Tableau des séances
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Date","Début","Fin","Durée","Mots","Lieu"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        v.addWidget(self.table, 1)

    def _stat_card(self, label, value):
        f = QFrame(); f.setFrameShape(QFrame.Shape.StyledPanel)
        f.setStyleSheet("border-radius:8px;padding:6px;")
        fl = QVBoxLayout(f)
        vl = QLabel(value); vl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vl.setStyleSheet("font-size:20px;font-weight:bold;")
        ll = QLabel(label); ll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ll.setStyleSheet("font-size:10px;")
        fl.addWidget(vl); fl.addWidget(ll)
        f._val = vl; return f

    def _get_filtered_sessions(self):
        from datetime import date, timedelta
        period_map = {0:7, 1:30, 2:90, 3:180, 4:365, 5:99999}
        days = period_map.get(self.period_combo.currentIndex(), 30)
        cutoff = (date.today() - timedelta(days=days)).isoformat()
        return [s for s in self.pm.sessions if s.get("date","") >= cutoff]

    def _refresh(self):
        sessions = self._get_filtered_sessions()
        total_words = sum(s.get("words_added",0) for s in sessions)
        total_secs  = sum(s.get("duration_s",0) for s in sessions)
        avg_words   = (total_words // len(sessions)) if sessions else 0
        hours = total_secs // 3600; mins = (total_secs % 3600) // 60
        time_str = f"{hours}h{mins:02d}" if hours else f"{mins}min"
        self._stat_total_sessions._val.setText(str(len(sessions)))
        self._stat_total_words._val.setText(f"{total_words:,}".replace(",", " "))
        self._stat_total_time._val.setText(time_str)
        self._stat_avg_words._val.setText(str(avg_words))
        self.chart_widget.update_data(sessions)
        # Tableau
        self.table.setRowCount(0)
        for s in reversed(sessions):
            row = self.table.rowCount(); self.table.insertRow(row)
            dur_s = s.get("duration_s",0)
            dur_str = f"{dur_s//3600}h{(dur_s%3600)//60:02d}" if dur_s>=3600 else f"{dur_s//60}min{dur_s%60:02d}s"
            for col, val in enumerate([
                s.get("date",""), s.get("start",""), s.get("end",""),
                dur_str, str(s.get("words_added",0)), s.get("location",""),
            ]):
                self.table.setItem(row, col, QTableWidgetItem(val))

    def showEvent(self, e):
        super().showEvent(e)
        self._refresh()


class SessionChartWidget(QWidget):
    """Graphique en barres des mots par jour, dessiné en QPainter."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._sessions = []

    def update_data(self, sessions):
        self._sessions = sessions
        self.update()

    def paintEvent(self, event):
        from collections import defaultdict
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        W, H = self.width(), self.height()
        bg = self.palette().color(QPalette.ColorRole.Base)
        painter.fillRect(0, 0, W, H, bg)

        if not self._sessions:
            painter.drawText(QRect(0,0,W,H), Qt.AlignmentFlag.AlignCenter, "Aucune séance pour cette période")
            return

        # Agréger par jour
        by_day = defaultdict(int)
        for s in self._sessions:
            by_day[s.get("date","")] += s.get("words_added",0)
        days = sorted(by_day.keys())
        if not days: return
        max_val = max(by_day.values()) or 1

        margin = 40; bar_area_w = W - 2*margin; bar_area_h = H - 2*margin
        n = len(days)
        bar_w = max(4, bar_area_w // n - 2)

        accent = QColor("#4A7FA5")
        painter.setPen(QPen(QColor("#888"), 1))
        # Axe Y
        painter.drawLine(margin, margin, margin, H-margin)
        painter.drawLine(margin, H-margin, W-margin, H-margin)

        for i, day in enumerate(days):
            val = by_day[day]
            bh = int(bar_area_h * val / max_val)
            x = margin + i * (bar_area_w // n)
            y = H - margin - bh
            painter.fillRect(x, y, bar_w, bh, accent)
            if n <= 14:
                painter.drawText(x, H-margin+14, day[-5:])

        # Axe Y labels
        painter.drawText(2, margin+8, str(max_val))
        painter.drawText(2, H-margin, "0")
        painter.end()

# ─────────────────────────────────────────────────────────────────────────────
#  APPLICATION PRINCIPALE
# ─────────────────────────────────────────────────────────────────────────────

class ScripturaApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Scriptura v1.11.1 - Jules AI"); self.setGeometry(50,50,1400,900)
        self.pm = ProjectManager()
        self.current_item = None
        self._current_view_index = 1   # mémorise la vue active
        self._composite_mode = False   # True si affichage sous-éléments concaténés
        self._composite_children = []
        self._composite_editors  = {}
        self._composite_scroll   = None
        self._selected_card_uid  = None
        self._selected_card_frame = None  # UI-03
        self._session_tracker    = SessionTracker(self.pm)
        self._session_timer      = QTimer(self); self._session_timer.timeout.connect(self._session_tick)
        self.autosave_timer = QTimer(self); self.autosave_timer.timeout.connect(self._autosave)
        self.themes = {
            "Manuscrit":{"sidebar":"#D8DDE2","editor_bg":"#F5F6F7","text":"#2B2B2B","accent":"#4A7FA5","highlight":"#6BA3C4","card_bg":"#FFFFFF"},
            "Ocean":    {"sidebar":"#1A3A5F","editor_bg":"#0D1B2A","text":"#E0E1DD","accent":"#8ECAE6","highlight":"#219EBC","card_bg":"#1B263B"},
            "Scriptura":{"sidebar":"#312C51","editor_bg":"#FDF6E3","text":"#48426D","accent":"#F0C38E","highlight":"#F1AA9B","card_bg":"#FFFFFF"},
            "Lagon":    {"sidebar":"#387693","editor_bg":"#0A1921","text":"#E0F2F1","accent":"#5EB1BF","highlight":"#74C69D","card_bg":"#142E3B"},
            "Néon":     {"sidebar":"#5D2AAB","editor_bg":"#120721","text":"#FDE0FF","accent":"#B000FF","highlight":"#FF00E4","card_bg":"#240E42"},
            "Volcan":   {"sidebar":"#4E3434","editor_bg":"#1A1111","text":"#F9EBEA","accent":"#D6343E","highlight":"#F05D3B","card_bg":"#2B1D1D"},
            "Solaire":  {"sidebar":"#95A313","editor_bg":"#FDFCF0","text":"#2D3106","accent":"#FFBF00","highlight":"#FF8C00","card_bg":"#FFFFFF"},
            "Aube":     {"sidebar":"#9A5B6F","editor_bg":"#FFF4F2","text":"#3D242C","accent":"#D47479","highlight":"#FFA07A","card_bg":"#FFFFFF"},
        }
        self.current_theme="Scriptura"; self.is_zen_mode=False
        self.editor = RichTextEdit()
        self.init_ui()
        self.apply_theme(self.current_theme)

    # ─── UI ──────────────────────────────────────────────────────────────────
    def init_ui(self):
        self.showMaximized()
        self.create_menus(); self.create_main_toolbar()
        container=QWidget(); self.setCentralWidget(container)
        self.main_layout=QVBoxLayout(container); self.main_layout.setContentsMargins(0,0,0,0); self.main_layout.setSpacing(0)
        self.middle_area = QSplitter(Qt.Orientation.Horizontal)
        self.middle_area.setHandleWidth(1)
        self.middle_area.setChildrenCollapsible(False)

        # ── Sidebar gauche ─────────────────────────────────────────────────
        self.left_sidebar=QWidget(); self.left_sidebar.setMinimumWidth(150); self.left_sidebar.setMaximumWidth(450)
        lv=QVBoxLayout(self.left_sidebar); lv.setContentsMargins(4,4,4,4)
        self.sidebar_label=QLabel("EXPLORATEUR")
        self.tree=DnDTreeWidget()
        self.tree.setHeaderHidden(True); self.tree.setIndentation(15)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.open_context_menu)
        self.tree.itemClicked.connect(self.on_tree_item_clicked)
        self.tree.setStyleSheet("QTreeWidget::item:selected{background:#415A77;color:white;border-radius:3px;}")
        self.init_tree_structure()
        lv.addWidget(self.sidebar_label); lv.addWidget(self.tree)

        # ── Zone centrale (stack) ──────────────────────────────────────────
        self.central_stack=QStackedWidget()

        # 0 : Projet
        self.project_page=ProjectPage(self.pm); self.central_stack.addWidget(self.project_page)

        # 1 : Éditeur texte
        self.text_editor_container=QWidget()
        tv_l=QVBoxLayout(self.text_editor_container); tv_l.setContentsMargins(0,0,0,0)
        self.format_toolbar=QToolBar(); self.setup_format_toolbar()
        tv_l.addWidget(self.format_toolbar)
        self.editor=RichTextEdit()
        self.editor.setAutoFormatting(QTextEdit.AutoFormattingFlag.AutoAll)
        self.editor.textChanged.connect(self.save_text_session)
        self.editor.textChanged.connect(self.update_stats)
        self.editor.cursorPositionChanged.connect(self._typewriter_tick)
        self.editor.selectionChanged.connect(self.sync_format_toolbar)
        tv_l.addWidget(self.editor)
        self.central_stack.addWidget(self.text_editor_container)

        # 2 : Cartes
        self.card_scroll=QScrollArea(); self.card_scroll.setWidgetResizable(True)
        self.card_container=QWidget(); self.card_grid=QGridLayout(self.card_container)
        self.card_scroll.setWidget(self.card_container)
        self.central_stack.addWidget(self.card_scroll)

        # 3–8 : Éditeurs de cartes (un par module)
        self.card_editors = {}
        for module in ["Personnages","Lieux","Notes","Recherches","Idées","Références"]:
            panel = CardEditorPanel(); self.central_stack.addWidget(panel)
            self.card_editors[module] = panel

        # 9 : Vue Liste
        self.list_view=ListViewWidget(self.pm); self.central_stack.addWidget(self.list_view)

        # 10 : Séances
        self.sessions_panel = SessionsPanel(self.pm)
        self.central_stack.addWidget(self.sessions_panel)

        # Index fixes
        self.STACK = {
            "Projet":0,"Texte":1,"Cartes":2,
            "Personnages":3,"Lieux":4,"Notes":5,"Recherches":6,"Idées":7,"Références":8,
            "Liste":9,"Séances":10
        }

        # ── Sidebar droite (inspecteur) ────────────────────────────────────
        self.inspector=InspectorPanel(self.pm); self.inspector.setMinimumWidth(200); self.inspector.setMaximumWidth(500)
        self.inspector.ins_name.textChanged.connect(self.sync_name)
        self.inspector.ins_synopsis.textChanged.connect(self.save_inspector)
        self.inspector.ins_status.currentTextChanged.connect(self.save_inspector)

        self.middle_area.addWidget(self.left_sidebar)
        self.middle_area.addWidget(self.central_stack)
        self.middle_area.addWidget(self.inspector)
        self.middle_area.setStretchFactor(1, 1) # Central stack takes remaining space
        self.middle_area.setSizes([250, 875, 275])
        self.main_layout.addWidget(self.middle_area)

        # ── Barre de statut ────────────────────────────────────────────────
        self.status_bar=QWidget(); self.status_bar.setFixedHeight(45)
        sl=QHBoxLayout(self.status_bar); sl.setContentsMargins(4,0,8,0)

        self.status_left=QWidget(); self.status_left.setFixedWidth(250)
        sll=QHBoxLayout(self.status_left)
        self.btn_page=QPushButton("📄+"); self.btn_page.setFixedWidth(50); self.btn_page.setObjectName("sidebar_bottom_btn")
        self.btn_folder=QPushButton("📁+"); self.btn_folder.setFixedWidth(50); self.btn_folder.setObjectName("sidebar_bottom_btn")
        self.btn_cfg=QPushButton("⚙"); self.btn_cfg.setFixedWidth(50); self.btn_cfg.setObjectName("sidebar_bottom_btn")
        for b in [self.btn_page,self.btn_folder,self.btn_cfg]:
            sll.addWidget(b)
        self.btn_page.clicked.connect(self.add_page)
        self.btn_folder.clicked.connect(self.add_folder)
        self.btn_cfg.clicked.connect(lambda: self.open_config(0))

        self.status_center=QWidget(); sc=QHBoxLayout(self.status_center); sc.setContentsMargins(0,0,0,0)
        self.autosave_lbl=QLabel(""); self.autosave_lbl.setStyleSheet("font-size:10px;")
        self.stats_label=QLabel("Mots : 0  |  Caractères : 0"); self.stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.goal_btn=QPushButton("🎯"); self.goal_btn.setFixedWidth(32); self.goal_btn.setFlat(True)
        self.goal_btn.setToolTip("Définir un objectif pour cet élément")
        self.goal_btn.clicked.connect(self.open_goal_dialog)
        self.goal_btn.setVisible(False)
        # Barre de progression objectif — hauteur augmentée
        self.goal_progress=QProgressBar(); self.goal_progress.setFixedWidth(180); self.goal_progress.setFixedHeight(24)
        self.goal_progress.setRange(0,100); self.goal_progress.setVisible(False)
        self.goal_progress.setStyleSheet("""
            QProgressBar{border:1px solid #666;border-radius:6px;background:#333;
                         color:white;font-size:11px;font-weight:bold;text-align:center;}
            QProgressBar::chunk{background:#F0C38E;border-radius:5px;}
        """)
        sc.addStretch(); sc.addWidget(self.autosave_lbl); sc.addWidget(self.stats_label)
        sc.addWidget(self.goal_btn); sc.addWidget(self.goal_progress); sc.addStretch()

        self.status_right=QWidget(); sr=QHBoxLayout(self.status_right)
        # Session chrono
        self._session_btn = QPushButton("⏱ Démarrer séance")
        self._session_btn.setFlat(True)
        self._session_btn.setStyleSheet("font-size:11px;")
        self._session_btn.clicked.connect(self._toggle_session)
        self._session_chrono = QLabel("")
        self._session_chrono.setStyleSheet("font-size:11px;font-weight:bold;")
        sr.addWidget(self._session_btn)
        sr.addWidget(self._session_chrono)
        sr.addWidget(QLabel("  "))
        self.zoom_combo=QComboBox(); self.zoom_combo.addItems(["75%","100%","125%","150%","200%"])
        self.zoom_combo.setCurrentText("100%"); self.zoom_combo.currentTextChanged.connect(self.apply_zoom)
        sr.addWidget(self.zoom_combo)

        sl.addWidget(self.status_left); sl.addWidget(self.status_center,1); sl.addWidget(self.status_right)
        self.main_layout.addWidget(self.status_bar)

        # Bouton sortie Zen
        self.zen_exit_btn=QPushButton("✕ Quitter le mode Zen")
        self.zen_exit_btn.setParent(self); self.zen_exit_btn.setFixedSize(200,36)
        self.zen_exit_btn.clicked.connect(self.toggle_zen); self.zen_exit_btn.setVisible(False)
        self.zen_exit_btn.setStyleSheet("background:rgba(50,50,50,0.85);color:white;border-radius:18px;font-size:12px;border:none;")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        
        # On vérifie si le widget Zen existe pour le redimensionner aussi
        if hasattr(self, 'zen_widget'):
            self.zen_widget.resize(self.size())
            
        # On vérifie si le bouton existe avant de tenter de le déplacer
        if hasattr(self, 'zen_exit_btn'):
            # Centrer le bouton de sortie Zen en bas
            self.zen_exit_btn.move((self.width() - self.zen_exit_btn.width()) // 2, self.height() - 70)

    # ─── Arborescence ────────────────────────────────────────────────────────
    def init_tree_structure(self):
        self.tree.clear()
        groups=[("Projet","🏠"),("Manuscrit","📖"),("Personnages","👥"),("Lieux","🌍"),
                ("Notes","📝"),("Recherches","🔍"),("Idées","💡"),("Références","📚"),("Corbeille","🗑️")]
        self.roots={}
        for name,icon in groups:
            root=QTreeWidgetItem(self.tree,[f"{icon} {name}"])
            root.setData(0,Qt.ItemDataRole.UserRole,"ROOT_GROUP")
            self.roots[name]=root

    def _get_ms_icon(self, d):
        """Choisit l'icône correcte pour un ItemData selon son type."""
        folder_types = ("Chapitre","Acte","Partie","Dossier","Prologue","Épilogue","Interlude")
        return "📁" if d.type_item in folder_types else "📄"

    def _rebuild_tree_from_pm(self):
        cfg = self.pm.config
        show_icons = cfg.get("show_tree_icons", True)
        show_status = cfg.get("show_tree_status", True)

        # Manuscrit
        ms_root=self.roots["Manuscrit"]; ms_root.takeChildren()
        def add_ms(parent_widget,uid):
            d=self.pm.items.get(uid)
            if not d: return
            icon=self._get_ms_icon(d) if show_icons else ""
            status = f" [{d.status}]" if show_status else ""
            text = f"{icon} {d.name}{status}".strip()
            node=QTreeWidgetItem(parent_widget,[text])
            node.setData(0,Qt.ItemDataRole.UserRole,d)
            for cuid in d.children: add_ms(node,cuid)
        for uid in self.pm.tree_roots.get("Manuscrit",[]): add_ms(ms_root,uid)

        # Modules cards
        module_map = {"Personnages":"Personnage","Lieux":"Lieu","Notes":"Note",
                      "Recherches":"Recherche","Idées":"Idée","Références":"Référence"}
        for group,kind in module_map.items():
            root=self.roots[group]; root.takeChildren()
            def add_card(parent_widget,uid):
                c=self.pm.cards.get(uid)
                if not c: return
                # Garantir le bon icon selon _is_folder
                icon = ("📁" if c._is_folder else SimpleCardData.ICON_MAP.get(c.kind,"📄")) if show_icons else ""
                status = f" [{c.status}]" if show_status else ""
                text = f"{icon} {c.name}{status}".strip()
                node=QTreeWidgetItem(parent_widget,[text])
                node.setData(0,Qt.ItemDataRole.UserRole,c)
                for cuid in c.children: add_card(node,cuid)
            for uid in self.pm.tree_roots.get(group,[]): add_card(root,uid)

        # Corbeille
        trash_root=self.roots["Corbeille"]; trash_root.takeChildren()
        for uid in self.pm.trash_items:
            item_data = self.pm.items.get(uid) or self.pm.cards.get(uid)
            if item_data:
                node=QTreeWidgetItem(trash_root,[f"🗑 {item_data.name}"])
                node.setData(0,Qt.ItemDataRole.UserRole,item_data)

    def _collect_tree_structure(self):
        """Sync tree → pm.tree_roots et pm.items.children"""
        def collect_ms(node):
            d=node.data(0,Qt.ItemDataRole.UserRole)
            if isinstance(d,ItemData):
                d.children=[]
                for i in range(node.childCount()):
                    ch=node.child(i); cd=ch.data(0,Qt.ItemDataRole.UserRole)
                    if isinstance(cd,ItemData): d.children.append(cd.uid)
                    collect_ms(ch)
        ms_root=self.roots["Manuscrit"]
        ms_uids=[]
        for i in range(ms_root.childCount()):
            node=ms_root.child(i)
            d=node.data(0,Qt.ItemDataRole.UserRole)
            if isinstance(d,ItemData): ms_uids.append(d.uid)
            collect_ms(node)
        self.pm.tree_roots["Manuscrit"]=ms_uids

        module_map={"Personnages":"Personnage","Lieux":"Lieu","Notes":"Note",
                    "Recherches":"Recherche","Idées":"Idée","Références":"Référence"}
        for group in module_map:
            root=self.roots[group]; guids=[]
            for i in range(root.childCount()):
                node=root.child(i); d=node.data(0,Qt.ItemDataRole.UserRole)
                if isinstance(d,SimpleCardData):
                    guids.append(d.uid); d.children=[]
                    for j in range(node.childCount()):
                        ch=node.child(j); cd=ch.data(0,Qt.ItemDataRole.UserRole)
                        if isinstance(cd,SimpleCardData): d.children.append(cd.uid)
            self.pm.tree_roots[group]=guids

    # ─── Clic sur l'arbre ────────────────────────────────────────────────────
    def on_tree_item_clicked(self, item, col):
        role = item.data(0,Qt.ItemDataRole.UserRole)
        text = item.text(0)

        if role=="ROOT_GROUP":
            if "Projet" in text:
                self.central_stack.setCurrentIndex(self.STACK["Projet"]); self.refresh_project_page()
            elif "Manuscrit" in text:
                self.central_stack.setCurrentIndex(self._current_view_index)
                if self._current_view_index == self.STACK["Texte"]:
                    self._load_composite(self.roots["Manuscrit"], None)
                # Auto-refresh des vues
                elif self._current_view_index==self.STACK["Liste"]:
                    self.show_list_view()
                elif self._current_view_index==self.STACK["Cartes"]:
                    self.show_card_view()
            elif "Corbeille" in text: pass
            else:
                for module in ["Personnages","Lieux","Notes","Recherches","Idées","Références"]:
                    if module in text:
                        self.central_stack.setCurrentIndex(self.STACK[module])
                        self.goal_btn.setVisible(False); self.goal_progress.setVisible(False)
                        break
            return

        if isinstance(role,ItemData):
            self.current_item=item
            # Charger l'inspecteur
            self.inspector.load_data(role,self.pm)
            # Si on est dans une vue Manuscrit → conserver la vue actuelle
            if self.central_stack.currentIndex() in (self.STACK["Texte"],self.STACK["Cartes"],self.STACK["Liste"]):
                self._current_view_index = self.central_stack.currentIndex()
                if self.central_stack.currentIndex()==self.STACK["Texte"]:
                    self._load_item_in_editor(item, role)
                    self.update_stats()
                elif self.central_stack.currentIndex()==self.STACK["Cartes"]:
                    self.show_card_view()
                elif self.central_stack.currentIndex()==self.STACK["Liste"]:
                    self.show_list_view()
            else:
                # Première fois ou revient depuis un module non-manuscrit
                self.central_stack.setCurrentIndex(self.STACK["Texte"])
                self._current_view_index=self.STACK["Texte"]
                self._load_item_in_editor(item, role)
                self.update_stats()
            self.goal_btn.setVisible(True)
            self._refresh_goal_progress(role)
            return

        if isinstance(role,SimpleCardData):
            self.current_item=item
            # Trouver le bon module
            for module,kind in {"Personnages":"Personnage","Lieux":"Lieu","Notes":"Note",
                                 "Recherches":"Recherche","Idées":"Idée","Références":"Référence"}.items():
                if role.kind==kind:
                    self.central_stack.setCurrentIndex(self.STACK[module])
                    self.card_editors[module].load_card(role)
                    self.inspector.load_data(role,self.pm)
                    self.goal_btn.setVisible(False); self.goal_progress.setVisible(False)
                    break

    def _find_tree_node_by_uid(self, uid):
        """Cherche un nœud dans l'arbre principal par uid."""
        def search(node):
            d = node.data(0, Qt.ItemDataRole.UserRole)
            if hasattr(d,"uid") and d.uid == uid: return node
            for i in range(node.childCount()):
                found = search(node.child(i))
                if found: return found
            return None
        return search(self.tree.invisibleRootItem())

    def on_tree_structure_changed(self):
        """Called when drag & drop happens in the main tree."""
        self._collect_tree_structure()
        # If List View is active, refresh it
        if self.central_stack.currentIndex() == self.STACK["Liste"]:
            self.show_list_view()
        # If Card View is active, refresh it
        elif self.central_stack.currentIndex() == self.STACK["Cartes"]:
            self.show_card_view()

    def sync_tree_order_from_listview(self, lv: "ListViewWidget"):
        """Resynchronise l'arbre principal depuis l'ordre ET la hiérarchie de la Vue Liste."""
        # Parcourir récursivement la listview et reconstruire l'arbre principal
        def sync_children(lv_parent_item, app_parent_node):
            """Réordonne et reparente les enfants dans l'arbre principal."""
            n = lv_parent_item.childCount()
            for i in range(n):
                lv_child = lv_parent_item.child(i)
                uid = lv_child.data(0, Qt.ItemDataRole.UserRole)
                if not uid: continue
                app_node = self._find_tree_node_by_uid(uid)
                if not app_node: continue
                current_parent = app_node.parent() or self.tree.invisibleRootItem()
                # Reparenter si nécessaire
                if current_parent is not app_parent_node:
                    current_parent.removeChild(app_node)
                    app_parent_node.addChild(app_node)
                    current_parent = app_parent_node
                # Réordonner
                cur_idx = current_parent.indexOfChild(app_node)
                if cur_idx != i:
                    current_parent.takeChild(cur_idx)
                    current_parent.insertChild(i, app_node)
                # Récursion sur les enfants
                sync_children(lv_child, app_node)

        parent_node = getattr(self, "_list_view_current_parent", self.roots["Manuscrit"])
        sync_children(lv.tree.invisibleRootItem(), parent_node)
        # Persist the new order to pm.tree_roots / pm.items.children immediately
        self._collect_tree_structure()

    def update_inspector_only(self, node):
        """Appelé depuis ListViewWidget (simple clic) — charge l'inspecteur sans changer de vue."""
        data=node.data(0,Qt.ItemDataRole.UserRole)
        if not isinstance(data,ItemData): return
        # Chercher le nœud canonique dans l'arbre principal pour que current_item pointe toujours
        # vers l'arbre principal (évite que save_inspector écrive dans le mauvais objet)
        canonical = self._find_tree_node_by_uid(data.uid)
        if canonical:
            canonical_data = canonical.data(0, Qt.ItemDataRole.UserRole)
            if isinstance(canonical_data, ItemData):
                data = canonical_data       # utiliser la ref canonique
                self.current_item = canonical   # important : current_item = nœud arbre principal
        self.inspector.load_data(data, self.pm)

    def open_item_in_editor(self, node):
        """Appelé depuis ListViewWidget (double clic)."""
        data=node.data(0,Qt.ItemDataRole.UserRole)
        if isinstance(data,ItemData):
            self.current_item=node
            self.central_stack.setCurrentIndex(self.STACK["Texte"])
            self._current_view_index=self.STACK["Texte"]
            self._load_item_in_editor(node, data)
            self.inspector.load_data(data,self.pm)
            self.goal_btn.setVisible(True); self._refresh_goal_progress(data)
            self.tree.setCurrentItem(node)

    def reload_current_item(self):
        if self.current_item:
            data=self.current_item.data(0,Qt.ItemDataRole.UserRole)
            if isinstance(data,ItemData):
                self._load_item_in_editor(self.current_item, data)
                self.inspector.ins_synopsis.blockSignals(True)
                self.inspector.ins_synopsis.setPlainText(data.synopsis)
                self.inspector.ins_synopsis.blockSignals(False)
                # Refresh versions display in inspector
                self.inspector._refresh_versions()

    # ─── Toolbar principale ──────────────────────────────────────────────────
    def create_main_toolbar(self):
        self.main_toolbar=QToolBar(); self.addToolBar(Qt.ToolBarArea.TopToolBarArea,self.main_toolbar)
        self.main_toolbar.setMovable(False)
        self.main_toolbar.setIconSize(QSize(32,32))
        self.main_toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)

        def make_action(emoji, label, parent):
            """Crée une QAction avec emoji comme icône et label en dessous."""
            a = QAction(label, parent)
            # Créer un pixmap emoji
            pix = QPixmap(32,32); pix.fill(Qt.GlobalColor.transparent)
            p = QPainter(pix)
            p.setFont(QFont("Segoe UI Emoji", 18))
            p.drawText(QRect(0,0,32,32), Qt.AlignmentFlag.AlignCenter, emoji)
            p.end()
            a.setIcon(QIcon(pix))
            return a

        act_save = make_action("💾","Sauvegarder",self); act_save.triggered.connect(self.save_project); act_save.setShortcut(QKeySequence("Ctrl+S"))
        act_undo = make_action("↩","Annuler",self);      act_undo.triggered.connect(lambda: self.editor.undo()); act_undo.setShortcut(QKeySequence("Ctrl+Z"))
        act_redo = make_action("↪","Rétablir",self);     act_redo.triggered.connect(lambda: self.editor.redo()); act_redo.setShortcut(QKeySequence("Ctrl+Y"))
        self.act_text  = make_action("📝","Texte",self);  self.act_text.triggered.connect(self._switch_to_text);  self.act_text.setCheckable(True)
        self.act_cards = make_action("🗂","Cartes",self);  self.act_cards.triggered.connect(self.show_card_view);  self.act_cards.setCheckable(True)
        self.act_list  = make_action("☰","Liste",self);   self.act_list.triggered.connect(self.show_list_view);   self.act_list.setCheckable(True)
        self.act_zen   = make_action("🧘","Zen",self);    self.act_zen.triggered.connect(self.toggle_zen)
        # Les 3 modes sont exclusifs (UI-04)
        self._view_act_group = QActionGroup(self)
        self._view_act_group.setExclusive(True)
        for a in [self.act_text, self.act_cards, self.act_list]:
            self._view_act_group.addAction(a)
        self.act_text.setChecked(True)  # Texte actif par défaut

        # Left: Sauvegarder, Annuler, Rétablir
        for act in [act_save, act_undo, act_redo]:
            self.main_toolbar.addAction(act)
        # Spacer centre-gauche
        sp_cl = QWidget(); sp_cl.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Preferred)
        self.main_toolbar.addWidget(sp_cl)
        # Centre: Texte, Cartes, Liste, Séances
        self.act_sessions = make_action("📊","Séances",self)
        self.act_sessions.setCheckable(True)
        self.act_sessions.triggered.connect(lambda: (
            self.central_stack.setCurrentIndex(self.STACK["Séances"]),
            self.sessions_panel._refresh(),
            setattr(self, "_current_view_index", self.STACK["Séances"])
        ))

        for act in [self.act_text, self.act_cards, self.act_list, self.act_sessions]:
            self.main_toolbar.addAction(act)
            self._view_act_group.addAction(act)

        # Spacer centre-droit
        sp_cr = QWidget(); sp_cr.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Preferred)
        self.main_toolbar.addWidget(sp_cr)
        # Right: Zen
        self.main_toolbar.addAction(self.act_zen)

    def _load_item_in_editor(self, tree_node, data: ItemData):
        """Charge un item dans l'éditeur. Si il a des enfants, mode composite."""
        has_child_items = False
        for i in range(tree_node.childCount()):
            ch = tree_node.child(i)
            cd = ch.data(0, Qt.ItemDataRole.UserRole)
            if isinstance(cd, ItemData):
                has_child_items = True
                break

        if has_child_items:
            self._load_composite(tree_node, data)
        else:
            self._exit_composite_mode()
            self.editor.blockSignals(True)
            # Reset format to avoid "bleeding" from previous item
            self.editor.setCurrentCharFormat(QTextCharFormat())
            if data.content and data.content.strip().startswith("<"):
                self.editor.setHtml(data.content)
            else:
                self.editor.setPlainText(data.content or "")
            # Re-apply base font from config
            self.apply_editor_config()
            self.editor.blockSignals(False)

    def _collect_descendants(self, node, depth=0):
        """Collecte récursivement tous les descendants ItemData d'un nœud."""
        results = []
        for i in range(node.childCount()):
            child = node.child(i)
            cd = child.data(0, Qt.ItemDataRole.UserRole)
            if isinstance(cd, ItemData):
                results.append((child, cd, depth))
                results.extend(self._collect_descendants(child, depth+1))
        return results

    def _load_composite(self, parent_node, parent_data: ItemData = None):
        """Affiche les sous-éléments récursivement avec séparateurs et zones éditables.
        Un seul QScrollArea global — pas d'ascenseur individuel par zone."""
        self._composite_mode = True
        # Collecter tous les descendants, pas seulement le premier niveau
        all_descendants = self._collect_descendants(parent_node)
        children = [(n, d) for n, d, _ in all_descendants]  # flatten avec profondeur
        depths   = {d.uid: depth for n, d, depth in all_descendants}
        self._composite_children = [(node, data) for node, data in children]
        self._composite_editors = {}

        tv_l = self.text_editor_container.layout()
        # Nettoyer l'ancien composite
        if hasattr(self, "_composite_scroll") and self._composite_scroll:
            tv_l.removeWidget(self._composite_scroll)
            self._composite_scroll.deleteLater()
            self._composite_scroll = None
        self.editor.setVisible(False)

        theme = self.themes[self.current_theme]
        bg = theme["editor_bg"]; fg = theme["text"]
        font_size = self.pm.config.get("font_size", 13)
        font_family = self.pm.config.get("font_family", "Georgia")

        # Un seul scroll global
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"QScrollArea{{background:{bg};border:none;}}")

        container = QWidget()
        container.setStyleSheet(f"background:{bg};")
        vlay = QVBoxLayout(container)
        vlay.setContentsMargins(60, 24, 60, 24); vlay.setSpacing(0)
        scroll.setWidget(container)
        tv_l.addWidget(scroll)
        self._composite_scroll = scroll

        # Scrollbar globale stylisée
        accent = theme["accent"]
        scroll.verticalScrollBar().setStyleSheet(
            f"QScrollBar:vertical{{width:8px;background:transparent;margin:0;}}"
            f"QScrollBar::handle:vertical{{background:{accent};border-radius:4px;min-height:20px;}}"
            f"QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{{height:0px;}}"
        )

        for node, data in children:
            depth = depths.get(data.uid, 0)
            indent = "    " * depth
            dash_count = max(10, 50 - depth * 6)
            sep = QLabel(f"{indent}── {data.name} " + "─" * dash_count)
            sep.setStyleSheet(
                f"color:#888;font-size:{11 - depth}px;font-weight:{'bold' if depth==0 else 'normal'};"
                f"background:{bg};padding:{12 - depth*2}px 0 4px 0;border-bottom:1px solid #ccc;"
            )
            vlay.addWidget(sep)

            # Zone éditable sans ascenseur propre (laisse le scroll global gérer)
            ed = QTextEdit()
            if data.content and data.content.strip().startswith("<"):
                ed.setHtml(data.content)
            else:
                ed.setPlainText(data.content or "")
            ed.setFrameShape(QFrame.Shape.NoFrame)
            ed.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            ed.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            ed.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            ed.setMinimumHeight(120)
            ed.setStyleSheet(
                f"background:{bg};color:{fg};font-size:{font_size}pt;"
                f"font-family:{font_family};border:none;padding:8px 0;"
            )
            # Auto-ajustement de la hauteur au contenu
            def adjust_height(e=ed):
                doc_h = e.document().size().height()
                e.setMinimumHeight(max(120, int(doc_h) + 20))
            ed.document().contentsChanged.connect(adjust_height)
            ed.textChanged.connect(lambda d=data, e=ed: self._save_composite_child(d, e))
            ed.selectionChanged.connect(self.sync_format_toolbar)
            ed.cursorPositionChanged.connect(self._typewriter_tick)
            ed.setAcceptRichText(True)
            self._composite_editors[data.uid] = ed
            vlay.addWidget(ed)

        vlay.addStretch()

    def _save_composite_child(self, data: ItemData, editor: "QTextEdit"):
        """Sauvegarde le contenu d'un enfant en mode composite."""
        data.content = editor.toHtml()
        data.content_plain = editor.toPlainText()
        data.modified_at = datetime.now().isoformat()

    def _exit_composite_mode(self):
        """Quitte le mode composite et restaure l'éditeur normal."""
        if not self._composite_mode: return
        self._composite_mode = False
        tv_l = self.text_editor_container.layout()
        if hasattr(self, "_composite_scroll") and self._composite_scroll:
            tv_l.removeWidget(self._composite_scroll)
            self._composite_scroll.deleteLater()
            self._composite_scroll = None
        self.editor.setVisible(True)
        self.editor.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

    def _switch_to_text(self):
        self.central_stack.setCurrentIndex(self.STACK["Texte"])
        self._current_view_index=self.STACK["Texte"]
        if hasattr(self,"act_text"): self.act_text.setChecked(True)  # UI-04
        if self.current_item:
            data=self.current_item.data(0,Qt.ItemDataRole.UserRole)
            if isinstance(data,ItemData):
                self._load_item_in_editor(self.current_item, data)
        else:
            self._exit_composite_mode()

    # ─── Menus ────────────────────────────────────────────────────────────────
    def create_menus(self):
        m=self.menuBar(); m.clear()
        f=m.addMenu("&Fichier")
        f.addAction("Nouveau Projet…",QKeySequence("Ctrl+Shift+N"),self.new_project)
        f.addAction("Ouvrir…",QKeySequence("Ctrl+O"),self.open_project)
        f.addSeparator()
        f.addAction("Sauvegarder",QKeySequence("Ctrl+S"),self.save_project)
        f.addSeparator()
        f.addAction("Configuration…",self.open_config)
        f.addSeparator()
        f.addAction("Quitter",self.close)
        e=m.addMenu("&Édition")
        e.addAction("Annuler",QKeySequence("Ctrl+Z"),lambda: self.editor.undo())
        e.addAction("Rétablir",QKeySequence("Ctrl+Y"),lambda: self.editor.redo())
        e.addSeparator()
        e.addAction("Couper",lambda: self.editor.cut()); e.addAction("Copier",lambda: self.editor.copy()); e.addAction("Coller",lambda: self.editor.paste())
        v=m.addMenu("&Affichage")
        v.addAction("Mode Zen",QKeySequence("F11"),self.toggle_zen)
        v.addAction("Vue Texte",QKeySequence("Ctrl+1"),self._switch_to_text)
        v.addAction("Vue Cartes",QKeySequence("Ctrl+2"),self.show_card_view)
        v.addAction("Vue Liste",QKeySequence("Ctrl+3"),self.show_list_view)
        p=m.addMenu("&Projet")
        p.addAction("Paramétrer les listes…",lambda: ListManagementDialog(self.pm,self).exec())
        for name in ["&Format","&Outils","&Aide"]: m.addMenu(name)

    # ─── Persistance ─────────────────────────────────────────────────────────
    def new_project(self):
        dlg=NewProjectDialog(self)
        if dlg.exec()!=QDialog.DialogCode.Accepted: return
        folder,title,author,goal=dlg.get_values()
        self.pm.new_project(folder,title,author)
        self.pm.project_data.word_goal=goal
        ProjectManager.add_recent(folder)
        self.setWindowTitle(f"Scriptura v1.11.1 - Jules AI — {title}")
        self.current_item = None
        self._exit_composite_mode()
        self.editor.blockSignals(True); self.editor.clear(); self.editor.blockSignals(False)
        self.goal_btn.setVisible(False); self.goal_progress.setVisible(False)
        self._selected_card_uid = None
        # Reset format actions if they exist
        if hasattr(self, "bold_action"): self.bold_action.setChecked(False)
        if hasattr(self, "italic_action"): self.italic_action.setChecked(False)
        self.init_tree_structure()
        self.central_stack.setCurrentIndex(self.STACK["Projet"]); self.refresh_project_page()
        self.apply_theme(self.pm.config.get("theme","Scriptura")); self.setup_autosave()

    def open_project(self, path=None):
        if path is None:
            dlg = RecentProjectsDialog(self)
            if dlg.exec() != QDialog.DialogCode.Accepted: return
            chosen = dlg.chosen_path
            if not chosen: return
            if chosen == "NEW":
                self.new_project(); return
            path = chosen
        if not path: return
        if not self.pm.load_project(path):
            QMessageBox.warning(self,"Erreur","project.json introuvable."); return
        ProjectManager.add_recent(path)
        self.setWindowTitle(f"Scriptura v1.11.1 - Jules AI — {self.pm.project_data.title}")
        self.current_item = None
        self.editor.blockSignals(True); self.editor.clear(); self.editor.blockSignals(False)
        self.goal_btn.setVisible(False); self.goal_progress.setVisible(False)
        self.init_tree_structure(); self._rebuild_tree_from_pm()
        self.central_stack.setCurrentIndex(self.STACK["Projet"]); self.refresh_project_page()
        self.apply_theme(self.pm.config.get("theme","Scriptura")); self.setup_autosave()

    def save_project(self):
        self._collect_tree_structure()
        # Sync trash
        self.pm.trash_items=[]
        trash_root=self.roots["Corbeille"]
        for i in range(trash_root.childCount()):
            d=trash_root.child(i).data(0,Qt.ItemDataRole.UserRole)
            if hasattr(d,"uid"): self.pm.trash_items.append(d.uid)
        if self.pm.save_project():
            self.autosave_lbl.setText(f"Sauvegardé {datetime.now().strftime('%H:%M')}")
        else:
            QMessageBox.warning(self,"Sauvegarde","Aucun projet ouvert.")

    def _autosave(self):
        if self.pm.project_dir:
            self._collect_tree_structure(); self.pm.save_project()
            self.autosave_lbl.setText(f"Auto-sauvegarde {datetime.now().strftime('%H:%M')}")

    def setup_autosave(self):
        interval=self.pm.config.get("autosave_interval",60)
        self.autosave_timer.stop()
        if interval>0: self.autosave_timer.start(interval*1000)

    # ─── Ajout d'éléments ────────────────────────────────────────────────────
    def add_tree_item(self, parent, name, icon, type_item):
        d=ItemData(name,type_item); self.pm.items[d.uid]=d
        real_icon = self._get_ms_icon(d) if hasattr(self,"_get_ms_icon") else icon
        node=QTreeWidgetItem(parent,[f"{real_icon} {name}"])
        node.setData(0,Qt.ItemDataRole.UserRole,d)
        return node

    def add_card_to_tree(self, parent, name, kind, is_folder=False):
        c=SimpleCardData(name,kind); c._is_folder=is_folder
        self.pm.cards[c.uid]=c
        icon="📁" if is_folder else c.icon
        node=QTreeWidgetItem(parent,[f"{icon} {name}"])
        node.setData(0,Qt.ItemDataRole.UserRole,c)
        return node

    def _current_module_kind(self):
        """Retourne (group_name, kind) du module actif selon l'arbre sélectionné."""
        sel = self.tree.currentItem()
        if not sel: return ("Manuscrit", None)
        # Remonter jusqu'à la racine de groupe
        node = sel
        while node:
            txt = node.text(0)
            for grp, kind in [("Personnages","Personnage"),("Lieux","Lieu"),
                               ("Notes","Note"),("Recherches","Recherche"),
                               ("Idées","Idée"),("Références","Référence")]:
                if grp in txt and node.data(0,Qt.ItemDataRole.UserRole)=="ROOT_GROUP":
                    return (grp, kind)
            node = node.parent()
        return ("Manuscrit", None)

    def add_page(self):
        """Ajoute un élément feuille dans le module actif."""
        sel = self.tree.currentItem()
        grp, kind = self._current_module_kind()
        if kind:  # module carte
            parent = sel if sel and sel.data(0,Qt.ItemDataRole.UserRole)!="ROOT_GROUP" else self.roots.get(grp, self.roots["Manuscrit"])
            self.add_card_to_tree(parent, f"Nouveau {kind}", kind, False)
            parent.setExpanded(True)
        else:  # Manuscrit
            parent = sel or self.roots["Manuscrit"]
            self.add_tree_item(parent, "Nouvelle Scène", "📄", "Scène")
            parent.setExpanded(True)

    def add_folder(self):
        """Ajoute un dossier/conteneur dans le module actif."""
        sel = self.tree.currentItem()
        grp, kind = self._current_module_kind()
        if kind:
            parent = sel if sel and sel.data(0,Qt.ItemDataRole.UserRole)!="ROOT_GROUP" else self.roots.get(grp, self.roots["Manuscrit"])
            self.add_card_to_tree(parent, "Nouveau Dossier", kind, True)
            parent.setExpanded(True)
        else:
            parent = sel or self.roots["Manuscrit"]
            self.add_tree_item(parent, "Nouveau Chapitre", "📁", "Chapitre")
            parent.setExpanded(True)

    # ─── Menu contextuel ─────────────────────────────────────────────────────
    def open_context_menu(self, position):
        item=self.tree.itemAt(position)
        if not item: return
        menu=QMenu()
        role=item.data(0,Qt.ItemDataRole.UserRole)
        is_root=(role=="ROOT_GROUP")
        is_trash="Corbeille" in item.text(0) if is_root else False
        text=item.text(0)

        # Détecter dans quel module on est
        in_ms=(not is_root and isinstance(role,ItemData)) or (is_root and "Manuscrit" in text)
        in_card_module=(not is_root and isinstance(role,SimpleCardData)) or (is_root and any(m in text for m in ["Personnages","Lieux","Notes","Recherches","Idées","Références"]))

        # Corbeille racine
        if is_trash:
            act_empty=menu.addAction("🗑 Vider la corbeille")
            action=menu.exec(self.tree.viewport().mapToGlobal(position))
            if action==act_empty: self._empty_trash()
            return

        # Élément dans la corbeille
        if not is_root:
            # Chercher si l'ancêtre est Corbeille
            p=item.parent()
            while p:
                if p==self.roots.get("Corbeille"):
                    act_restore=menu.addAction("♻ Restaurer")
                    action=menu.exec(self.tree.viewport().mapToGlobal(position))
                    if action==act_restore: self._restore_from_trash(item)
                    return
                p=p.parent()

        # Module Manuscrit
        if in_ms or (is_root and "Manuscrit" in text):
            act_folder=menu.addAction("📁 Nouveau Chapitre")
            act_page=menu.addAction("📄 Nouvelle Scène")
            menu.addSeparator()
            act_delete=None
            if not is_root: act_delete=menu.addAction("🗑️ Supprimer")
            action=menu.exec(self.tree.viewport().mapToGlobal(position))
            if action==act_folder:
                self.add_tree_item(item,"Nouveau Chapitre","📁","Chapitre"); item.setExpanded(True)
            elif action==act_page:
                self.add_tree_item(item,"Nouvelle Scène","📄","Scène"); item.setExpanded(True)
            elif act_delete and action==act_delete: self.move_to_trash(item)
            return

        # Modules cartes
        if in_card_module or (is_root and any(m in text for m in ["Personnages","Lieux","Notes","Recherches","Idées","Références"])):
            module_kind_map={"Personnages":"Personnage","Lieux":"Lieu","Notes":"Note",
                             "Recherches":"Recherche","Idées":"Idée","Références":"Référence"}
            kind=""
            for mname,mk in module_kind_map.items():
                if mname in text: kind=mk; break
            if not kind and isinstance(role,SimpleCardData): kind=role.kind
            act_folder=menu.addAction("📁 Nouveau Dossier")
            act_card=menu.addAction(f"{SimpleCardData.ICON_MAP.get(kind,'📄')} Nouvel élément")
            menu.addSeparator()
            act_delete=None
            if not is_root: act_delete=menu.addAction("🗑️ Supprimer")
            action=menu.exec(self.tree.viewport().mapToGlobal(position))
            if action==act_folder:
                self.add_card_to_tree(item,"Nouveau Dossier",kind,True); item.setExpanded(True)
            elif action==act_card:
                self.add_card_to_tree(item,f"Nouveau {kind}",kind,False); item.setExpanded(True)
            elif act_delete and action==act_delete: self.move_to_trash(item)

    def move_to_trash(self, item):
        # Mémoriser le parent d'origine
        d=item.data(0,Qt.ItemDataRole.UserRole)
        if hasattr(d,"_origin_parent_uid"):
            parent=item.parent()
            if parent:
                pd=parent.data(0,Qt.ItemDataRole.UserRole)
                d._origin_parent_uid=getattr(pd,"uid",None)
            else:
                d._origin_parent_uid=None
        parent=item.parent()
        if parent: parent.removeChild(item)
        else: self.tree.takeTopLevelItem(self.tree.indexOfTopLevelItem(item))
        self.roots["Corbeille"].addChild(item); self.roots["Corbeille"].setExpanded(True)

    def _restore_from_trash(self, item):
        d=item.data(0,Qt.ItemDataRole.UserRole)
        name=getattr(d,"name","cet élément")
        kind_label="Manuscrit" if isinstance(d,ItemData) else getattr(d,"_origin_group","module")
        origin_uid=getattr(d,"_origin_parent_uid",None)
        # Trouver le parent d'origine
        target_parent=None
        if origin_uid:
            def find_node(root_node):
                for i in range(root_node.childCount()):
                    ch=root_node.child(i)
                    cd=ch.data(0,Qt.ItemDataRole.UserRole)
                    if hasattr(cd,"uid") and cd.uid==origin_uid: return ch
                    found=find_node(ch)
                    if found: return found
                return None
            target_parent=find_node(self.tree.invisibleRootItem())
        if target_parent is None:
            # Chercher la racine du groupe
            if isinstance(d,ItemData): target_parent=self.roots.get("Manuscrit")
            elif isinstance(d,SimpleCardData):
                group_map={"Personnage":"Personnages","Lieu":"Lieux","Note":"Notes",
                           "Recherche":"Recherches","Idée":"Idées","Référence":"Références"}
                target_parent=self.roots.get(group_map.get(d.kind,"Manuscrit"))
            if target_parent is None: target_parent=self.roots.get("Manuscrit")
        dest_name=target_parent.text(0) if target_parent else "racine"
        reply=QMessageBox.question(self,"Restaurer",
            f"Restaurer « {name} » dans {dest_name} ?",
            QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)
        if reply==QMessageBox.StandardButton.Yes:
            self.roots["Corbeille"].removeChild(item)
            target_parent.addChild(item); target_parent.setExpanded(True)

    def _empty_trash(self):
        reply=QMessageBox.question(self,"Vider la corbeille","Supprimer définitivement tous les éléments de la corbeille ?")
        if reply==QMessageBox.StandardButton.Yes:
            trash=self.roots["Corbeille"]
            while trash.childCount(): trash.takeChild(0)

    # ─── Données items ────────────────────────────────────────────────────────
    def save_text_session(self):
        if self.current_item and not self._composite_mode:
            data=self.current_item.data(0,Qt.ItemDataRole.UserRole)
            if isinstance(data,ItemData):
                data.content=self.editor.toHtml()       # rich text HTML
                data.content_plain=self.editor.toPlainText()  # pour stats/mots
                data.modified_at=datetime.now().isoformat()
                self._refresh_goal_progress(data)
        # Update stats even in composite mode
        self.update_stats()

    def save_inspector(self):
        if not self.current_item: return
        data = self.current_item.data(0, Qt.ItemDataRole.UserRole)
        if not isinstance(data, ItemData): return
        # Toujours écrire dans l'objet canonique de pm.items pour éviter les doublons
        canonical = self.pm.items.get(data.uid, data)
        name,type_item,status,synopsis,notes = self.inspector.collect_properties()
        canonical.synopsis = synopsis; canonical.notes = notes
        canonical.status   = status;  canonical.type_item = type_item
        # Rafraîchir vue liste si active
        if self.central_stack.currentIndex() == self.STACK["Liste"]:
            self.list_view.refresh_row_from_inspector(canonical)
            self.list_view._uid_to_data[canonical.uid] = canonical
        # Rafraîchir vue cartes si active (BUG-03)
        if self.central_stack.currentIndex() == self.STACK["Cartes"]:
            self._refresh_card_if_visible(canonical)

    def sync_name(self, txt):
        # Guard: only update if txt actually differs from current data
        # (prevents parent being renamed when loading child)
        if not self.current_item: return
        data = self.current_item.data(0, Qt.ItemDataRole.UserRole)
        if not hasattr(data, "name"): return
        if data.name == txt: return   # no actual change — avoid cascade
        data.name = txt
        icon = self.current_item.text(0).split()[0] if self.current_item.text(0) else "📄"
        self.current_item.setText(0, f"{icon} {txt}")
        # Refresh card editor title
        if isinstance(data, SimpleCardData):
            module_map = {"Personnage":"Personnages","Lieu":"Lieux","Note":"Notes",
                          "Recherche":"Recherches","Idée":"Idées","Référence":"Références"}
            module = module_map.get(data.kind)
            if module and module in self.card_editors:
                self.card_editors[module].refresh_title(data)
        # Refresh list view row
        if self.central_stack.currentIndex() == self.STACK["Liste"] and isinstance(data, ItemData):
            self.list_view.refresh_row_from_inspector(data)

    def _toggle_session(self):
        """Démarre ou arrête une séance d'écriture."""
        if self._session_tracker.active:
            # Arrêter
            t = self.editor.toPlainText()
            s = self._session_tracker.stop(len(t.split()), len(t))
            self._session_timer.stop()
            self._session_btn.setText("⏱ Démarrer séance")
            self._session_btn.setStyleSheet("font-size:11px;")
            self._session_chrono.setText("")
            if s:
                QMessageBox.information(self,"Séance terminée",
                    f"Durée : {s['duration_s']//60} min\n"
                    f"Mots écrits : {s['words_added']}\n"
                    f"Caractères : {s['chars_added']}")
        else:
            # Choisir lieu + scène
            dlg = SessionStartDialog(self.pm, self.current_item, self)
            if dlg.exec() != QDialog.DialogCode.Accepted: return
            loc, scene_uid = dlg.get_values()
            t = self.editor.toPlainText()
            self._session_tracker.start(len(t.split()), len(t), scene_uid, loc)
            self._session_timer.start(1000)
            self._session_btn.setText("⏹ Arrêter séance")
            self._session_btn.setStyleSheet("font-size:11px;color:#E53935;")

    def _typewriter_tick(self):
        if self.pm.config.get("typewriter_mode", False):
            ed = self._active_editor()
            cursor_rect = ed.cursorRect()
            viewport_height = ed.viewport().height()
            diff = cursor_rect.top() - viewport_height // 2
            if abs(diff) > 5:
                scrollbar = ed.verticalScrollBar()
                scrollbar.setValue(scrollbar.value() + diff)

    def _session_tick(self):
        self._session_chrono.setText(self._session_tracker.elapsed_str())

    def refresh_card_tree_node(self, card: "SimpleCardData"):
        """Met à jour le texte du nœud dans l'arborescence après sauvegarde d'une fiche."""
        node = self._find_tree_node_by_uid(card.uid)
        if node:
            icon = card.icon
            node.setText(0, f"{icon} {card.name}")

    # ─── Objectif ────────────────────────────────────────────────────────────
    def open_goal_dialog(self):
        if not self.current_item: return
        data=self.current_item.data(0,Qt.ItemDataRole.UserRole)
        if not isinstance(data,ItemData): return
        dlg=GoalDialog(data,self)
        if dlg.exec()==QDialog.DialogCode.Accepted:
            unit,val=dlg.get_values()
            data.goal_unit=unit
            if unit=="mots": data.word_goal=val
            else: data.char_goal=val
            self._refresh_goal_progress(data)

    def _refresh_goal_progress(self, data: ItemData):
        txt=self.editor.toPlainText()  # always use plain for counting
        if data.goal_unit=="mots": current=len(txt.split()) if txt.strip() else 0; goal=data.word_goal
        else: current=len(txt); goal=data.char_goal
        if goal>0:
            pct=min(int(current/goal*100),100)
            self.goal_progress.setValue(pct)
            self.goal_progress.setFormat(f"{current}/{goal} {data.goal_unit} ({pct}%)")
            self.goal_progress.setVisible(True)
        else:
            self.goal_progress.setVisible(False)

    # ─── Vues ─────────────────────────────────────────────────────────────────
    def _make_card_widget(self, child, data, i, theme, selected_uid=None):
        """Carte avec liseré-poignée, effet pile, clic=sélection, dbl=éditeur."""
        label_color = "#888888"
        for lbl in self.pm.get_labels():
            if lbl["name"] == data.label: label_color = lbl["color"]; break
        has_children = child.childCount() > 0
        is_selected  = (selected_uid == data.uid)
        cb = theme["card_bg"]; ct = theme["text"]; ac = theme["accent"]

        CARD_W, CARD_H, STRIP_H = 230, 180, 12

        wrapper = QFrame()
        wrapper.setFixedSize(CARD_W + 16, CARD_H + 16)   # marge pour effet pile

        # Effet pile (ombres décalées) si sous-éléments
        if has_children:
            for off in [10, 6]:
                sh = QFrame(wrapper)
                sh.setGeometry(off, off, CARD_W, CARD_H)
                sh.setStyleSheet(
                    f"background:{cb};border:1px solid {label_color};border-radius:8px;"
                )
                sh.lower()

        # Carte principale
        card_frame = QFrame(wrapper)
        card_frame.setGeometry(0, 0, CARD_W, CARD_H)
        outline = f"border:2px solid {ac};" if is_selected else "border:1px solid #ddd;"
        card_frame.setStyleSheet(f"background:{cb};color:{ct};border-radius:8px;{outline}")

        vlayout = QVBoxLayout(card_frame)
        vlayout.setContentsMargins(0, 0, 0, 0); vlayout.setSpacing(0)

        # Liseré coloré en haut = poignée de drag (cursor main)
        strip = QFrame()
        strip.setFixedHeight(STRIP_H)
        strip.setStyleSheet(
            f"background:{label_color};border-radius:8px 8px 0 0;border:none;"
        )
        strip.setCursor(Qt.CursorShape.OpenHandCursor)
        strip.setToolTip("Maintenir pour déplacer la carte")
        vlayout.addWidget(strip)

        # Contenu de la carte
        body = QWidget()
        body.setStyleSheet(f"background:{cb};border:none;")
        bl = QVBoxLayout(body); bl.setContentsMargins(10, 8, 10, 8); bl.setSpacing(4)

        # Nom éditable (QPlainTextEdit pour le retour à la ligne)
        name_edit = QPlainTextEdit(data.name)
        name_edit.setStyleSheet(
            f"font-weight:bold;font-size:13px;border:none;background:transparent;color:{ct};"
        )
        name_edit.setFixedHeight(40)
        name_edit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        name_edit.setReadOnly(False)
        def on_name_changed(d=data, c=child, ed=name_edit):
            txt = ed.toPlainText()
            if d.name == txt: return
            d.name = txt
            icon = c.text(0).split()[0] if c.text(0) else "📄"
            c.setText(0, f"{icon} {txt}")
        name_edit.textChanged.connect(on_name_changed)
        bl.addWidget(name_edit)
        # Enregistrer pour rafraîchissement externe
        if not hasattr(self,"_card_widgets"): self._card_widgets = {}
        if data.uid not in self._card_widgets:
            self._card_widgets[data.uid] = {}
        self._card_widgets[data.uid]["name"] = name_edit
        self._card_widgets[data.uid]["frame"] = card_frame
        self._card_widgets[data.uid]["strip"] = strip

        # Synopsis éditable
        syn_edit = QTextEdit()
        syn_edit.setPlainText(data.synopsis or "")
        syn_edit.setFixedHeight(68)
        syn_edit.setStyleSheet(
            f"font-size:11px;border:none;background:transparent;color:{ct};"
        )
        syn_edit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        syn_edit.textChanged.connect(lambda d=data, e=syn_edit: setattr(d,"synopsis",e.toPlainText()))
        bl.addWidget(syn_edit)
        if not hasattr(self,"_card_widgets"): self._card_widgets = {}
        if data.uid not in self._card_widgets: self._card_widgets[data.uid] = {}
        self._card_widgets[data.uid]["syn"] = syn_edit
        vlayout.addWidget(body, 1)

        # ── Interactions ──────────────────────────────────────────────────────
        uid = data.uid
        _drag_start = [None]  # [QPoint] position de départ du drag

        def card_press(ev, c=child, d=data):
            _drag_start[0] = ev.position().toPoint() if hasattr(ev,"position") else ev.pos()
            # UI-03: effacer l'ancienne sélection
            prev_frame = getattr(self, "_selected_card_frame", None)
            prev_cb    = getattr(self, "_selected_card_prev_cb", cb)
            prev_ct    = getattr(self, "_selected_card_prev_ct", ct)
            if prev_frame and prev_frame is not card_frame:
                try:
                    prev_frame.setStyleSheet(
                        f"background:{prev_cb};color:{prev_ct};border-radius:8px;border:1px solid #ddd;"
                    )
                except RuntimeError: pass  # widget peut avoir été détruit
            # Nouvelle sélection
            self._selected_card_uid = d.uid
            self._selected_card_frame = card_frame
            self._selected_card_prev_cb = cb
            self._selected_card_prev_ct = ct
            self.current_item = c
            self.inspector.load_data(d, self.pm)
            card_frame.setStyleSheet(f"background:{cb};color:{ct};border-radius:8px;border:2px solid {ac};")

        def card_move(ev, wrapper=wrapper, d=data):
            if _drag_start[0] is None: return
            pos = ev.position().toPoint() if hasattr(ev,"position") else ev.pos()
            delta_mv = pos - _drag_start[0]
            if delta_mv.manhattanLength() < 6: return
            wrapper.setCursor(Qt.CursorShape.ClosedHandCursor)
            # UI-02 : fantôme semi-transparent qui suit le curseur
            ghost = getattr(self, "_card_ghost", None)
            if ghost is None:
                ghost = QLabel(self.card_scroll)
                ghost.setFixedSize(CARD_W, 40)
                ghost.setStyleSheet(
                    f"background:{label_color};color:white;border-radius:6px;"
                    f"font-weight:bold;font-size:12px;padding:4px 8px;opacity:0.75;"
                )
                ghost.setText(d.name)
                ghost.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
                ghost.setWindowOpacity(0.75)
                ghost.show()
                self._card_ghost = ghost
            # Positionner le fantôme sous le curseur (dans le scroll area)
            global_pos = strip.mapToGlobal(pos)
            local_pos  = self.card_scroll.mapFromGlobal(global_pos)
            ghost.move(local_pos.x() - CARD_W//2, local_pos.y() - 20)

            # Drag indicator (dotted line)
            indicator = getattr(self, "_card_drag_indicator", None)
            if indicator is None:
                indicator = QFrame(self.card_container)
                indicator.setStyleSheet(f"border: 2px dashed {ac}; background: transparent;")
                indicator.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
                self._card_drag_indicator = indicator
            
            # Find target index based on position
            grid = self.card_grid
            moved_idx = -1
            for i in range(grid.count()):
                if grid.itemAt(i).widget() is wrapper:
                    moved_idx = i; break
            
            target_col = max(0, min(2, (local_pos.x() + self.card_scroll.horizontalScrollBar().value()) // CARD_W))
            target_row = max(0, (local_pos.y() + self.card_scroll.verticalScrollBar().value()) // CARD_H)
            target_idx = min(grid.count() - 1, target_row * 3 + target_col)

            if target_idx != -1:
                target_item = grid.itemAt(target_idx)
                if target_item:
                    rect = target_item.geometry()
                    indicator.setGeometry(rect)
                    indicator.show()

        def card_release(ev, wrapper=wrapper):
            if _drag_start[0] is None: return
            end_pos = ev.position().toPoint() if hasattr(ev,"position") else ev.pos()
            delta = end_pos - _drag_start[0]
            _drag_start[0] = None
            wrapper.setCursor(Qt.CursorShape.ArrowCursor)
            # UI-02 : détruire le fantôme
            ghost = getattr(self, "_card_ghost", None)
            if ghost:
                ghost.deleteLater()
                self._card_ghost = None
            indicator = getattr(self, "_card_drag_indicator", None)
            if indicator:
                indicator.hide()
            # Si déplacement suffisant : chercher la carte cible et échanger
            if delta.manhattanLength() > 20:
                self._card_drop(wrapper, delta)

        def card_dbl(ev, c=child):
            self.open_item_in_editor(c)

        strip.mousePressEvent   = card_press
        strip.mouseMoveEvent    = card_move
        strip.mouseReleaseEvent = card_release
        card_frame.mouseDoubleClickEvent = card_dbl

        return wrapper

    def _card_drop(self, moved_wrapper, delta):
        """Échange la position de la carte déplacée avec celle sous le curseur."""
        parent = self.tree.currentItem() or self.roots["Manuscrit"]
        # Calculer quelle carte est à la destination
        grid = self.card_grid
        moved_idx = None
        for i in range(grid.count()):
            item = grid.itemAt(i)
            if item and item.widget() is moved_wrapper:
                moved_idx = i; break
        if moved_idx is None: return
        # Estimer la carte cible via le delta (grille 3 colonnes)
        row, col = divmod(moved_idx, 3)
        dx, dy = delta.x(), delta.y()
        CARD_W, CARD_H = 246, 196
        target_col = max(0, min(2, col + (1 if dx > CARD_W//2 else -1 if dx < -CARD_W//2 else 0)))
        target_row = max(0, row + (1 if dy > CARD_H//2 else -1 if dy < -CARD_H//2 else 0))
        target_idx = target_row * 3 + target_col
        total = grid.count()
        if target_idx == moved_idx or target_idx >= total: return
        # Échanger dans l'arbre principal
        moved_node  = parent.child(moved_idx)
        target_node = parent.child(target_idx)
        if not moved_node or not target_node: return
        parent.removeChild(moved_node); parent.insertChild(target_idx, moved_node)
        self._collect_tree_structure()
        # Refresh
        self.show_card_view()

    def _refresh_card_if_visible(self, data: ItemData):
        """Met à jour en direct les widgets d'une carte si elle est visible (BUG-03)."""
        widgets = getattr(self, "_card_widgets", {}).get(data.uid)
        if not widgets: return
        name_ed = widgets.get("name")
        syn_ed  = widgets.get("syn")
        strip   = widgets.get("strip")
        if name_ed:
            current_text = name_ed.toPlainText() if isinstance(name_ed, QPlainTextEdit) else name_ed.text()
            if current_text != data.name:
                name_ed.blockSignals(True)
                if isinstance(name_ed, QPlainTextEdit): name_ed.setPlainText(data.name)
                else: name_ed.setText(data.name)
                name_ed.blockSignals(False)
        if syn_ed and syn_ed.toPlainText() != data.synopsis:
            syn_ed.blockSignals(True); syn_ed.setPlainText(data.synopsis or ""); syn_ed.blockSignals(False)

        # Refresh label color (BUG-03)
        if strip:
            label_color = "#888888"
            for lbl in self.pm.get_labels():
                if lbl["name"] == data.label:
                    label_color = lbl["color"]
                    break
            strip.setStyleSheet(f"background:{label_color};border-radius:8px 8px 0 0;border:none;")

    def show_card_view(self):
        self.central_stack.setCurrentIndex(self.STACK["Cartes"])
        self._current_view_index=self.STACK["Cartes"]
        if hasattr(self,"act_cards"): self.act_cards.setChecked(True)  # UI-04
        while self.card_grid.count():
            w=self.card_grid.takeAt(0).widget()
            if w: w.deleteLater()
        self._card_widgets = {}  # uid → {"name": QLineEdit, "syn": QTextEdit, "frame": QFrame}
        self._selected_card_frame = None  # reset la sélection au rechargement de la vue (UI-03)
        if hasattr(self, "_card_ghost") and self._card_ghost:
            try: self._card_ghost.deleteLater()
            except: pass
            self._card_ghost = None
        parent=self.tree.currentItem() or self.roots["Manuscrit"]
        theme=self.themes[self.current_theme]
        selected_uid = getattr(self,"_selected_card_uid",None)
        for i in range(parent.childCount()):
            child=parent.child(i); data=child.data(0,Qt.ItemDataRole.UserRole)
            if not isinstance(data,ItemData): continue
            card_w = self._make_card_widget(child, data, i, theme, selected_uid)
            self.card_grid.addWidget(card_w, i//3, i%3)

    def show_list_view(self):
        self.central_stack.setCurrentIndex(self.STACK["Liste"])
        self._current_view_index=self.STACK["Liste"]
        if hasattr(self,"act_list"): self.act_list.setChecked(True)  # UI-04
        sel=self.tree.currentItem()
        # Si pas de sélection ou racine Manuscrit → afficher tout le manuscrit
        if not sel or sel.data(0,Qt.ItemDataRole.UserRole)=="ROOT_GROUP":
            parent=self.roots["Manuscrit"]
        else:
            parent=sel
        self._list_view_current_parent = parent
        self.list_view.refresh(parent,self.pm)

    def refresh_project_page(self): self.project_page.refresh()

    def toggle_zen(self):
        self.is_zen_mode=not self.is_zen_mode
        for w in [self.left_sidebar,self.inspector,self.status_bar,self.format_toolbar]:
            w.setVisible(not self.is_zen_mode)
        self.menuBar().setVisible(not self.is_zen_mode)
        self.main_toolbar.setVisible(not self.is_zen_mode)
        self.zen_exit_btn.setVisible(self.is_zen_mode)
        if self.is_zen_mode:
            self.showFullScreen()
            QTimer.singleShot(100,lambda: self.zen_exit_btn.move((self.width()-self.zen_exit_btn.width())//2,self.height()-70))
        else:
            self.showMaximized()

    # ─── Toolbar format ───────────────────────────────────────────────────────
    def _icon(self, name):
        """Charge une icône depuis ICON_PATH."""
        path = os.path.join(ICON_PATH, name)
        if os.path.exists(path): return QIcon(path)
        # Fallback: crée un pixmap texte
        pix = QPixmap(20,20); pix.fill(Qt.GlobalColor.transparent)
        return QIcon(pix)

    def setup_format_toolbar(self):
        # Police + taille
        self.font_box = QFontComboBox()
        self.font_box.setFontFilters(QFontComboBox.FontFilter.ScalableFonts)
        self.font_box.setFixedWidth(160)
        self.font_box.currentFontChanged.connect(self._format_font_family)
        self.format_toolbar.addWidget(self.font_box)

        self.size_box = QComboBox()
        self.size_box.setFixedWidth(55)
        for s in [7,8,9,10,11,12,13,14,16,18,20,24,28,32,36,48,64,72,96]:
            self.size_box.addItem(str(s))
        self.size_box.setCurrentText("13")
        self.size_box.currentTextChanged.connect(self._format_font_size)
        self.format_toolbar.addWidget(self.size_box)
        self.format_toolbar.addSeparator()

        # Gras / Italique / Souligné / Barré
        self.bold_action = QAction(self._icon("edit-bold.png"), "Gras", self)
        self.bold_action.setShortcut(QKeySequence("Ctrl+B")); self.bold_action.setCheckable(True)
        self.bold_action.triggered.connect(self._format_bold)
        self.format_toolbar.addAction(self.bold_action)

        self.italic_action = QAction(self._icon("edit-italic.png"), "Italique", self)
        self.italic_action.setShortcut(QKeySequence("Ctrl+I")); self.italic_action.setCheckable(True)
        self.italic_action.triggered.connect(self._format_italic)
        self.format_toolbar.addAction(self.italic_action)

        self.underline_action = QAction(self._icon("edit-underline.png"), "Souligné", self)
        self.underline_action.setShortcut(QKeySequence("Ctrl+U")); self.underline_action.setCheckable(True)
        self.underline_action.triggered.connect(self._format_underline)
        self.format_toolbar.addAction(self.underline_action)
        self.format_toolbar.addSeparator()

        # Alignement
        self.alignl_action = QAction(self._icon("edit-alignment.png"), "Gauche", self)
        self.alignl_action.setCheckable(True)
        self.alignl_action.triggered.connect(lambda: self._active_editor().setAlignment(Qt.AlignmentFlag.AlignLeft))
        self.format_toolbar.addAction(self.alignl_action)

        self.alignc_action = QAction(self._icon("edit-alignment-center.png"), "Centre", self)
        self.alignc_action.setCheckable(True)
        self.alignc_action.triggered.connect(lambda: self._active_editor().setAlignment(Qt.AlignmentFlag.AlignCenter))
        self.format_toolbar.addAction(self.alignc_action)

        self.alignr_action = QAction(self._icon("edit-alignment-right.png"), "Droite", self)
        self.alignr_action.setCheckable(True)
        self.alignr_action.triggered.connect(lambda: self._active_editor().setAlignment(Qt.AlignmentFlag.AlignRight))
        self.format_toolbar.addAction(self.alignr_action)

        self.alignj_action = QAction(self._icon("edit-alignment-justify.png"), "Justifié", self)
        self.alignj_action.setCheckable(True)
        self.alignj_action.triggered.connect(lambda: self._active_editor().setAlignment(Qt.AlignmentFlag.AlignJustify))
        self.format_toolbar.addAction(self.alignj_action)

        # Groupe exclusif alignement
        align_group = QActionGroup(self); align_group.setExclusive(True)
        for a in [self.alignl_action,self.alignc_action,self.alignr_action,self.alignj_action]:
            align_group.addAction(a)
        self.format_toolbar.addSeparator()

        # Couleur texte
        a_color = QAction(self._icon("edit-color.png"), "Couleur", self)
        a_color.triggered.connect(self.change_color)
        self.format_toolbar.addAction(a_color)

        # Couleur surlignage
        a_hl = QAction(self._icon("paint-can-color.png"), "Surlignage", self)
        a_hl.triggered.connect(self.change_highlight)
        self.format_toolbar.addAction(a_hl)
        self.format_toolbar.addSeparator()

        # Liste à puces
        #a_list = QAction("≡•", "Liste", self)
        a_list = QAction("≡•", self)
        a_list.setToolTip("Liste") # On définit le nom "Liste" comme info-bulle
        a_list.triggered.connect(lambda: self._active_editor().textCursor().insertList(
            QTextListFormat.Style.ListDisc))
        self.format_toolbar.addAction(a_list)

        # Impression
        a_print = QAction(self._icon("printer.png"), "Imprimer", self)
        a_print.setShortcut(QKeySequence("Ctrl+P"))
        a_print.triggered.connect(self.file_print)
        self.format_toolbar.addAction(a_print)

        # Wrap text toggle
        self.wrap_action = QAction("↵ Retour", self)
        self.wrap_action.setCheckable(True); self.wrap_action.setChecked(True)
        self.wrap_action.toggled.connect(self._format_wrap)
        self.format_toolbar.addAction(self.wrap_action)

        # Liste des widgets de format pour blockSignals
        self._format_actions = [self.font_box, self.size_box,
                                 self.bold_action, self.italic_action, self.underline_action]

    def _active_editor(self):
        if self._composite_mode:
            # Find which editor has focus
            for ed in self._composite_editors.values():
                if ed.hasFocus(): return ed
            # Fallback to the first one
            if self._composite_editors:
                return list(self._composite_editors.values())[0]
        return self.editor

    def _format_font_family(self, font):
        self._active_editor().setCurrentFont(font)

    def _format_font_size(self, s):
        if s.isdigit():
            self._active_editor().setFontPointSize(float(s))

    def _format_bold(self):
        ed = self._active_editor()
        fmt = ed.currentCharFormat()
        fmt.setFontWeight(QFont.Weight.Bold if self.bold_action.isChecked() else QFont.Weight.Normal)
        ed.setCurrentCharFormat(fmt)

    def _format_italic(self):
        ed = self._active_editor()
        fmt = ed.currentCharFormat()
        fmt.setFontItalic(self.italic_action.isChecked())
        ed.setCurrentCharFormat(fmt)

    def _format_underline(self):
        ed = self._active_editor()
        fmt = ed.currentCharFormat()
        fmt.setFontUnderline(self.underline_action.isChecked())
        ed.setCurrentCharFormat(fmt)

    def _format_wrap(self, on):
        mode = QTextEdit.LineWrapMode.WidgetWidth if on else QTextEdit.LineWrapMode.NoWrap
        self.editor.setLineWrapMode(mode)
        if self._composite_mode:
            for ed in self._composite_editors.values():
                ed.setLineWrapMode(mode)

    def apply_font_change(self, font):
        ed = self._active_editor()
        font.setPointSize(int(self.size_box.currentText()) if self.size_box.currentText().isdigit() else 13)
        ed.setFont(font); ed.setCurrentFont(font); ed.setFocus()

    def sync_format_toolbar(self):
        """Met à jour la toolbar en fonction de la sélection courante."""
        ed = self._active_editor()
        for o in self._format_actions: o.blockSignals(True)
        f = ed.currentFont()
        fmt = ed.currentCharFormat()
        self.font_box.setCurrentFont(f)
        sz = int(f.pointSize()) if f.pointSize()>0 else 13
        self.size_box.setCurrentText(str(sz))
        self.bold_action.setChecked(fmt.fontWeight() == QFont.Weight.Bold)
        self.italic_action.setChecked(fmt.fontItalic())
        self.underline_action.setChecked(fmt.fontUnderline())
        al = ed.alignment()
        self.alignl_action.setChecked(al == Qt.AlignmentFlag.AlignLeft)
        self.alignc_action.setChecked(al == Qt.AlignmentFlag.AlignCenter)
        self.alignr_action.setChecked(al == Qt.AlignmentFlag.AlignRight)
        self.alignj_action.setChecked(al == Qt.AlignmentFlag.AlignJustify)
        for o in self._format_actions: o.blockSignals(False)

    def change_color(self):
        c = QColorDialog.getColor()
        if c.isValid():
            ed = self._active_editor()
            ed.setTextColor(c)

    def change_highlight(self):
        c = QColorDialog.getColor()
        if c.isValid():
            ed = self._active_editor()
            ed.setTextBackgroundColor(c)

    def file_print(self):
        dlg = QPrintDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._active_editor().print_(dlg.printer())

    # ─── Thème ────────────────────────────────────────────────────────────────
    def apply_theme(self, theme_name):
        if theme_name not in self.themes: return
        c=self.themes[theme_name]; self.current_theme=theme_name; self.pm.config["theme"]=theme_name
        # Sidebar: texte blanc sur dark, texte foncé sur thème clair
        sb_text = label_text_color(c["sidebar"])
        self.left_sidebar.setStyleSheet(f"background:{c['sidebar']};color:{sb_text};")
        self.sidebar_label.setStyleSheet(f"color:{c['accent']};font-weight:bold;padding:5px;")
        border_color = "#ccc" if sb_text == "black" else "#333"
        self.status_bar.setStyleSheet(f"background:{c['sidebar']};border-top:1px solid {border_color};")
        self.editor.setStyleSheet(
            f"background:{c['editor_bg']};color:{c['text']};padding:60px;border:none;"
        )
        # Barres de défilement éditeur
        scroll_bg = "#555" if label_text_color(c["editor_bg"])=="white" else "#ccc"
        scroll_handle = c['accent']
        self.editor.verticalScrollBar().setStyleSheet(
            f"QScrollBar:vertical{{width:10px;background:{scroll_bg};border-radius:5px;}}"
            f"QScrollBar::handle:vertical{{background:{scroll_handle};border-radius:5px;min-height:24px;}}"
            f"QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{{height:0px;}}"
        )
        self.stats_label.setStyleSheet(f"color:{c['accent']};font-weight:bold;")
        self.autosave_lbl.setStyleSheet(f"color:{c['accent']};font-size:10px;")
        self.main_toolbar.setStyleSheet(f"background:{c['sidebar']};color:{sb_text};")
        self.inspector.apply_styles(c['accent'])
        # Appliquer le stylesheet global (hover, scrollbars, toolbar active)
        QApplication.instance().setStyleSheet(
            build_global_stylesheet(c['accent'], c['sidebar'], c['editor_bg'], c['text'])
        )
        # Passer la couleur de texte à la Vue Liste
        self.list_view.set_theme_text_color(c['text'])
        # Style Vue Liste tree
        self.list_view.tree.setStyleSheet(
            f"QTreeWidget{{background:{c['editor_bg']};color:{c['text']};border:none;}}"
            f"QTreeWidget::item:selected{{background:{c['highlight']};color:white;}}"
            f"QTreeWidget::branch:selected{{background:{c['highlight']};}}"
            f"QTreeWidget::item:hover{{background:{c['highlight']}40;}}"
            f"QTreeWidget::branch:hover{{background:{c['highlight']}40;}}"
        )
        # Style arborescence gauche selon thème
        sb = label_text_color(c["sidebar"])
        self.tree.setStyleSheet(
            f"QTreeWidget{{background:{c['sidebar']};color:{sb};border:none;}}"
            f"QTreeWidget::item:selected{{background:{c['accent']}80;color:{sb};border-radius:3px;}}"
            f"QTreeWidget::branch:selected{{background:{c['accent']}80;}}"
            f"QTreeWidget::item:hover{{background:{c['accent']}40;}}"
            f"QTreeWidget::branch:hover{{background:{c['accent']}40;}}"
        )
        # Goal progress bar
        self.goal_progress.setStyleSheet(f"""
            QProgressBar{{border:1px solid {c['accent']};border-radius:6px;background:#333;
                          color:white;font-size:11px;font-weight:bold;text-align:center;}}
            QProgressBar::chunk{{background:{c['accent']};border-radius:5px;}}
        """)

    def apply_editor_config(self):
        cfg=self.pm.config
        self.editor.setFont(QFont(cfg.get("font_family","Georgia"),cfg.get("font_size",13)))
        # Update word count visibility
        self.stats_label.setVisible(cfg.get("show_word_count", True))

    # ─── Stats ────────────────────────────────────────────────────────────────
    def update_stats(self):
        t=self.editor.toPlainText()
        words = len(t.split()) if t.strip() else 0
        chars = len(t)
        self.stats_label.setText(f"Mots : {words}  |  Caractères : {chars}")
        if self.current_item:
            data=self.current_item.data(0,Qt.ItemDataRole.UserRole)
            if isinstance(data,ItemData): self._refresh_goal_progress(data)

    def apply_zoom(self, txt):
        factor=int(txt.replace('%',''))/100.0
        f=self.editor.font(); f.setPointSize(int(13*factor)); self.editor.setFont(f)

    def open_config(self, tab_index=0): ConfigDialog(self,tab_index).exec()


# ─────────────────────────────────────────────────────────────────────────────
#  POINT D'ENTRÉE
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app=QApplication(sys.argv)
    app.setApplicationName("Scriptura"); app.setOrganizationName("Scriptura")

    # 1. Splash screen
    splash=SplashScreen()
    splash.exec()

    # 2. Fenêtre projets récents
    recent_dlg=RecentProjectsDialog()
    result=recent_dlg.exec()
    chosen=recent_dlg.chosen_path

    # 3. Lancer l'appli
    window=ScripturaApp()
    window.show()

    if chosen=="NEW":
        QTimer.singleShot(200,window.new_project)
    elif chosen and chosen!="NEW" and os.path.isdir(chosen):
        QTimer.singleShot(200,lambda: window.open_project(chosen))

    sys.exit(app.exec())