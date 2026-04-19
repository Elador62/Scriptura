"""
Scriptura v1.8
Application de gestion et suivi d'écriture de roman.

Nouveautés v1.6 :
  - Splash screen avec logo SVG généré
  - Fenêtre de démarrage "Projets récents" avec stats complètes
  - Personnages / Lieux / Notes / Idées / Références dans l'arborescence
  - Modules dédiés : Notes, Recherches, Idées (★ notation), Références
  - Vue Liste : simple clic → inspecteur, double clic → éditeur, pas de basculement de vue
  - Restauration depuis la Corbeille (avec clic droit + confirmation)
  - Bug Versions figées : restauration de l'élément vraiment sélectionné
  - Propriétés inspecteur : suppression du champ Objectif
  - Métadonnées : étiquettes couleur en texte blanc sur fond, mots-clefs en grille
  - Paramétrage des listes : étiquettes couleur sur fond correct
  - Toolbar : boutons Sauvegarder, Annuler, Rétablir
  - Objectif scène : données persistées + barre de progression plus haute
  
Nouveautés v1.7 :
  - Correction crash SimpleCardData (attributs manquants)
  - Vue Liste remplacée par arborescence déroulable/refermable avec inline combos
  - Barre d'outils : Sauvegarder/Annuler/Rétablir à gauche, Texte/Cartes/Liste centrés, Zen à droite
  - Versions figées : indicateur version active (◀) + compte mots/caractères
  - Mode carte : liseré coloré en haut de carte (pas de fond coloré)
  - Mode composite : éléments avec sous-éléments affichent le contenu concaténé
  - Boutons 📄+/📁+ universels (fonctionnent dans tous les modules)
  - Menu Fichier/Ouvrir : affiche la fenêtre projets récents
  - Nouveau projet : réinitialise l'éditeur
  - Barre objectif : couleur accent, toujours lisible sur fond sombre
  - SimpleCardData : ajout de tous les attributs pour compatibilité inspecteur
  
Nouveautés v1.8 :
  - Thème "Manuscrit" sobre inspiré de Scrivener
  - Toolbar : icônes x2, texte sous icônes
  - Inspecteur : suppression onglet Propriétés ; Nom dans Notes ; Type/Statut dans Métadonnées
  - Métadonnées : Étiquette avec carré couleur dans la liste déroulante
  - CARD_FIELDS : retrait des champs Nom/Titre redondants ; Nom→Surnom pour Personnages
  - Mode composite : séparateurs non-éditables (QTextBrowser) + zones éditables (QTextEdit)
  - Mode carte : clic=sélection+inspecteur, double-clic=éditeur, édition inline statut/synopsis
  - Mode carte : effet cartes empilées si sous-éléments
  - Vue Liste : couleur texte selon thème, icônes carrés couleur label
  - Restauration version : rafraîchissement immédiat
  - Arborescence : icônes dossiers préservées au rechargement
  - Boutons 📄+/📁+ : fonctionnent dans tous les modules
  - DnD Vue Liste : synchronise l'arbre principal
  - Clic "Manuscrit" : rafraîchit la vue active
  - sync_name : met à jour l'arbre et le titre de la fiche
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
    QRadioButton, QInputDialog, QSplashScreen, QTextBrowser
)
from PyQt6.QtGui import (
    QFont, QAction, QTextCharFormat, QTextCursor,
    QColor, QTextTableFormat, QTextListFormat, QIcon,
    QKeySequence, QPalette, QPixmap, QBrush, QPainter, QPen
)
from PyQt6.QtCore import Qt, QPoint, QTimer, QDate, QSize, QMimeData, QByteArray, QRect, QRectF
from PyQt6.QtSvgWidgets import QSvgWidget

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
        self.save_project()

    def save_project(self):
        if not self.project_dir: return False
        self.project_data.modified_at = datetime.now().isoformat()
        pf = {
            "project":    self.project_data.to_dict(),
            "config":     self.config,
            "tree_roots": self.tree_roots,
            "trash_items": self.trash_items,
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
        return sum(len(it.content.split()) for it in self.items.values() if it.content)

    def get_labels(self):   return self.config.get("labels",list(DEFAULT_LABELS))
    def get_statuses(self): return self.config.get("statuses",list(DEFAULT_STATUSES))
    def get_item_types(self): return self.config.get("item_types",list(DEFAULT_TYPES))

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
        # Vider l'ancien contenu
        while self._detail_v.count():
            w = self._detail_v.takeAt(0).widget()
            if w: w.deleteLater()

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

        # Infos
        form = QFormLayout()
        form.addRow("Genre :",    QLabel(s['genre'] or "—"))
        form.addRow("Statut :",   QLabel(s['status']))
        form.addRow("Créé le :",  QLabel(s['created_at']))
        form.addRow("Modifié le :",QLabel(s['modified_at']))
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
        # Type et Statut (déplacés depuis Propriétés)
        v.addWidget(QLabel("<b>Type</b>"))
        self.meta_type_lbl = QLabel("<i>—</i>")
        v.addWidget(self.meta_type_lbl)
        v.addWidget(QLabel("<b>Statut</b>"))
        self.meta_status_lbl = QLabel("<i>—</i>")
        v.addWidget(self.meta_status_lbl)
        # Étiquette avec carré couleur
        v.addWidget(QLabel("<b>Étiquette</b>"))
        self.meta_label = QComboBox()
        v.addWidget(self.meta_label)
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
            label = f"[{ver['date']}] {ver['title']}   {words} mots / {chars} car.{marker}"
            item = QListWidgetItem(label)
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
        # Labels affichés dans Métadonnées
        self.meta_type_lbl.setText(getattr(item_data,"type_item","—"))
        self.meta_status_lbl.setText(getattr(item_data,"status","—"))
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

class ListViewWidget(QWidget):
    """Vue Liste : arborescence déroulable avec colonnes de métadonnées inline."""

    HEADERS = ["Titre / Synopsis", "Étiquette", "Statut", "Type"]

    def __init__(self, pm: ProjectManager, parent=None):
        super().__init__(parent)
        self.pm = pm
        self._uid_to_node = {}   # uid ItemData → QTreeWidgetItem (arbre de l'app)
        self._build()

    def _build(self):
        v = QVBoxLayout(self); v.setContentsMargins(0,0,0,0)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(self.HEADERS)
        self.tree.setColumnCount(4)
        # Titre : 45% de l'espace, autres colonnes fixes
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col in (1,2,3):
            self.tree.header().setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        self.tree.setRootIsDecorated(True)
        self.tree.setAlternatingRowColors(True)
        self.tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tree.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tree.setUniformRowHeights(False)
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
            i = lc.count()-1
            lc.setItemData(i, lbl["name"], Qt.ItemDataRole.UserRole)
        lc.setCurrentText(data.label)
        def on_label(txt, d=data):
            d.label = txt
            self._refresh_item_colors(d)
        lc.currentTextChanged.connect(on_label)
        return lc

    def _make_status_widget(self, data, pm):
        sc = QComboBox(); sc.addItems(pm.get_statuses()); sc.setCurrentText(data.status)
        sc.currentTextChanged.connect(lambda txt,d=data: setattr(d,"status",txt))
        return sc

    def _make_type_widget(self, data, pm):
        tc = QComboBox(); tc.addItems(pm.get_item_types()); tc.setCurrentText(data.type_item)
        tc.currentTextChanged.connect(lambda txt,d=data: setattr(d,"type_item",txt))
        return tc

    def _refresh_item_colors(self, data):
        item = self._uid_to_node.get(data.uid)
        if not item: return
        # Use theme text color for readability; add color dot prefix
        label_color = "#888"
        for lbl in self.pm.get_labels():
            if lbl["name"] == data.label: label_color = lbl["color"]; break
        # Set a small color square as decoration icon on col 0
        pix = QPixmap(10,10); pix.fill(QColor(label_color if data.label != "Aucune" else "transparent"))
        item.setIcon(0, QIcon(pix))
        # Text color: use app theme text (set externally via set_theme_text_color)
        tc = getattr(self, "_theme_text_color", "#222222")
        item.setForeground(0, QBrush(QColor(tc)))

    def _add_tree_item(self, parent_widget, app_node, pm, prefix=""):
        """Ajoute récursivement un nœud de l'arbre principal dans la vue liste."""
        data = app_node.data(0, Qt.ItemDataRole.UserRole)
        if not isinstance(data, ItemData): return None
        num = self._get_numbering(app_node).rstrip(".")
        icon = app_node.text(0).split()[0] if app_node.text(0) else "📄"
        title = f"{num}  {icon} {data.name}" if num else f"{icon} {data.name}"
        syn = (data.synopsis[:100]+"…") if len(data.synopsis)>100 else data.synopsis
        display = title + (f"\n{syn}" if syn else "")

        list_item = QTreeWidgetItem(parent_widget)
        list_item.setText(0, display)
        list_item.setSizeHint(0, QSize(0, 52 if syn else 28))
        list_item.setData(0, Qt.ItemDataRole.UserRole, data.uid)
        self._uid_to_node[data.uid] = list_item

        # Icône couleur label + texte couleur thème
        label_color = "#888"
        for lbl in pm.get_labels():
            if lbl["name"] == data.label: label_color = lbl["color"]; break
        if data.label != "Aucune":
            pix = QPixmap(10,10); pix.fill(QColor(label_color))
            list_item.setIcon(0, QIcon(pix))
        tc = getattr(self, "_theme_text_color", "#222222")
        list_item.setForeground(0, QBrush(QColor(tc)))

        # Widgets inline pour cols 1-3
        self.tree.setItemWidget(list_item, 1, self._make_label_widget(data, pm))
        self.tree.setItemWidget(list_item, 2, self._make_status_widget(data, pm))
        self.tree.setItemWidget(list_item, 3, self._make_type_widget(data, pm))

        # Stocker la référence au nœud de l'arbre app pour refresh
        if not hasattr(self,"_app_node_cache"): self._app_node_cache = {}
        self._app_node_cache[data.uid] = app_node
        # Enfants récursifs
        for i in range(app_node.childCount()):
            self._add_tree_item(list_item, app_node.child(i), pm)
        list_item.setExpanded(True)
        return list_item

    def set_theme_text_color(self, color):
        self._theme_text_color = color

    def refresh(self, parent_node, pm):
        self.pm = pm
        self._uid_to_node = {}
        self._app_node_cache = {}
        self.tree.clear()
        if not parent_node: return
        for i in range(parent_node.childCount()):
            self._add_tree_item(self.tree.invisibleRootItem(), parent_node.child(i), pm)

    def refresh_row_from_inspector(self, data: ItemData):
        """Met à jour les combos et le texte titre d'une ligne."""
        item = self._uid_to_node.get(data.uid)
        if not item: return
        # Mettre à jour le texte col 0 (titre + synopsis)
        num = ""
        app_node = getattr(self,"_app_node_cache",{}).get(data.uid)
        if app_node: num = self._get_numbering(app_node).rstrip(".")
        icon_txt = item.text(0).split()[0] if item.text(0) else "📄"
        title = f"{num}  {icon_txt} {data.name}" if num else f"{icon_txt} {data.name}"
        syn = (data.synopsis[:100]+"…") if len(data.synopsis)>100 else data.synopsis
        item.setText(0, title + ("\n" + syn if syn else ""))
        item.setSizeHint(0, QSize(0, 52 if syn else 28))
        # Combos cols 1-3
        for col, getter in [(1, lambda d: d.label),(2, lambda d: d.status),(3, lambda d: d.type_item)]:
            w = self.tree.itemWidget(item, col)
            if w and isinstance(w, QComboBox):
                w.blockSignals(True); w.setCurrentText(getter(data)); w.blockSignals(False)
        self._refresh_item_colors(data)

    def _notify_app(self, attr, node):
        p = self.parent()
        while p:
            if hasattr(p, attr): getattr(p, attr)(node); break
            p = p.parent()

    def _on_rows_moved(self, *args):
        """Propage le réordonnancement vers l'arbre principal."""
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
        # Use cache first, fall back to search
        app_node = getattr(self,"_app_node_cache",{}).get(uid) or self._get_app_node_for_uid(uid)
        if app_node: self._notify_app("update_inspector_only", app_node)

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
        self.app = parent; self.setWindowTitle("Configuration — Scriptura"); self.setMinimumSize(720,520)
        layout = QHBoxLayout(self)
        self.nav = QListWidget(); self.nav.setFixedWidth(175)
        self.nav.addItems(["🎨  Thème","🔤  Éditeur","📁  Projet","📋  Listes","☁️  Synchronisation","⌨️  Raccourcis","🌲  Arborescence"])
        self.nav.currentRowChanged.connect(lambda i: self.stack.setCurrentIndex(i))
        self.stack = QStackedWidget()
        layout.addWidget(self.nav); layout.addWidget(self.stack)
        self._build_theme_panel(); self._build_editor_panel(); self._build_project_panel()
        self._build_lists_panel(); self._build_cloud_panel()
        self._build_shortcuts_panel(); self._build_tree_panel()
        self.nav.setCurrentRow(start_tab)

    def _build_theme_panel(self):
        w = QWidget(); v = QVBoxLayout(w)
        v.addWidget(QLabel("<b>Thèmes visuels</b>"))
        v.addWidget(QLabel("<small>Un seul thème actif à la fois.</small>"))
        self._tbg = QButtonGroup(w); self._tbg.setExclusive(True)
        for name,colors in self.app.themes.items():
            rw = QWidget(); r = QHBoxLayout(rw); r.setContentsMargins(0,2,0,2)
            for key in ["sidebar","editor_bg","highlight"]:
                dot = QFrame(); dot.setFixedSize(18,18)
                dot.setStyleSheet(f"background:{colors[key]};border-radius:9px;border:1px solid #555;")
                r.addWidget(dot)
            btn = QRadioButton(f"  {name}"); btn.setChecked(name==self.app.current_theme)
            btn.toggled.connect(lambda checked,n=name: self.app.apply_theme(n) if checked else None)
            self._tbg.addButton(btn); r.addWidget(btn,1); v.addWidget(rw)
        v.addStretch(); self.stack.addWidget(w)

    def _build_editor_panel(self):
        w = QWidget(); v = QVBoxLayout(w); v.addWidget(QLabel("<b>Éditeur</b>"))
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
        btn=QPushButton("Appliquer"); btn.clicked.connect(self._apply_editor)
        v.addWidget(btn); v.addStretch(); self.stack.addWidget(w)

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
        w=QWidget(); v=QVBoxLayout(w); v.addWidget(QLabel("<b>Métadonnées du projet</b>"))
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
        v.addLayout(form); btn=QPushButton("Appliquer"); btn.clicked.connect(self._apply_project)
        v.addWidget(btn); v.addStretch(); self.stack.addWidget(w)

    def _apply_project(self):
        pd=self.app.pm.project_data
        pd.title=self.cfg_title.text(); pd.author=self.cfg_author.text()
        pd.genre=self.cfg_genre.currentText(); pd.word_goal=self.cfg_goal.value()
        pd.status=self.cfg_status.currentText(); pd.description=self.cfg_desc.toPlainText()
        self.app.pm.config["autosave_interval"]=self.cfg_autosave.value()
        self.app.setup_autosave(); self.app.refresh_project_page()

    def _build_lists_panel(self):
        w=QWidget(); v=QVBoxLayout(w); v.addWidget(QLabel("<b>Paramétrage des listes</b>"))
        btn=QPushButton("Ouvrir le gestionnaire de listes…")
        btn.clicked.connect(lambda: ListManagementDialog(self.app.pm,self).exec())
        v.addWidget(btn); v.addStretch(); self.stack.addWidget(w)

    def _build_cloud_panel(self):
        w=QWidget(); v=QVBoxLayout(w); v.addWidget(QLabel("<b>☁️ Synchronisation Cloud</b>"))
        v.addWidget(QLabel("Placez votre dossier projet dans le dossier de votre client cloud.\n"))
        row=QHBoxLayout()
        self.cfg_cloud=QLineEdit(self.app.pm.config.get("cloud_path",""))
        btn_b=QPushButton("Parcourir…"); btn_b.clicked.connect(self._browse_cloud)
        row.addWidget(self.cfg_cloud); row.addWidget(btn_b); v.addLayout(row)
        v.addWidget(QLabel("• Dropbox: ~/Dropbox/\n• Google Drive: ~/Google Drive/\n• KDrive: ~/kdrive/\n• OneDrive: ~/OneDrive/"))
        btn=QPushButton("Enregistrer"); btn.clicked.connect(self._apply_cloud)
        v.addWidget(btn); v.addStretch(); self.stack.addWidget(w)

    def _browse_cloud(self):
        d=QFileDialog.getExistingDirectory(self,"Choisir le dossier cloud")
        if d: self.cfg_cloud.setText(d)

    def _apply_cloud(self):
        self.app.pm.config["cloud_path"]=self.cfg_cloud.text()
        QMessageBox.information(self,"Cloud","Chemin cloud enregistré.")

    def _build_shortcuts_panel(self):
        w=QWidget(); v=QVBoxLayout(w); v.addWidget(QLabel("<b>Raccourcis clavier</b>"))
        shortcuts=[("Sauvegarder","Ctrl+S"),("Nouveau projet","Ctrl+Shift+N"),("Ouvrir projet","Ctrl+O"),
                   ("Mode Zen","F11"),("Vue Texte","Ctrl+1"),("Vue Cartes","Ctrl+2"),("Vue Liste","Ctrl+3"),
                   ("Annuler","Ctrl+Z"),("Rétablir","Ctrl+Y"),("Gras","Ctrl+B"),("Italique","Ctrl+I")]
        form=QFormLayout()
        for lbl,key in shortcuts: form.addRow(lbl,QLabel(f"<code>{key}</code>"))
        v.addLayout(form); v.addStretch(); self.stack.addWidget(w)

    def _build_tree_panel(self):
        w=QWidget(); v=QVBoxLayout(w); v.addWidget(QLabel("<b>Arborescence</b>"))
        self.cfg_icons=QCheckBox("Afficher les icônes"); self.cfg_icons.setChecked(True)
        self.cfg_status=QCheckBox("Afficher le statut"); self.cfg_status.setChecked(True)
        v.addWidget(self.cfg_icons); v.addWidget(self.cfg_status); v.addStretch(); self.stack.addWidget(w)


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


# ─────────────────────────────────────────────────────────────────────────────
#  APPLICATION PRINCIPALE
# ─────────────────────────────────────────────────────────────────────────────

class ScripturaApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Scriptura v1.8"); self.setGeometry(50,50,1400,900)
        self.pm = ProjectManager()
        self.current_item = None
        self._current_view_index = 1   # mémorise la vue active
        self._composite_mode = False   # True si affichage sous-éléments concaténés
        self._composite_children = []  # liste de (node, ItemData) en mode composite
        self._composite_editors  = {}  # uid → QTextEdit en mode composite
        self._composite_scroll   = None  # QScrollArea du mode composite
        self._selected_card_uid  = None  # uid de la carte sélectionnée
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
        self.editor = QTextEdit()
        self.init_ui()
        self.apply_theme(self.current_theme)

    # ─── UI ──────────────────────────────────────────────────────────────────
    def init_ui(self):
        self.showMaximized()
        self.create_menus(); self.create_main_toolbar()
        container=QWidget(); self.setCentralWidget(container)
        self.main_layout=QVBoxLayout(container); self.main_layout.setContentsMargins(0,0,0,0); self.main_layout.setSpacing(0)
        self.middle_area=QHBoxLayout(); self.middle_area.setSpacing(0)

        # ── Sidebar gauche ─────────────────────────────────────────────────
        self.left_sidebar=QWidget(); self.left_sidebar.setFixedWidth(250)
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
        self.editor=QTextEdit()
        self.editor.textChanged.connect(self.save_text_session)
        self.editor.textChanged.connect(self.update_stats)
        self.editor.cursorPositionChanged.connect(self.sync_format_toolbar)
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

        # Index fixes
        self.STACK = {
            "Projet":0,"Texte":1,"Cartes":2,
            "Personnages":3,"Lieux":4,"Notes":5,"Recherches":6,"Idées":7,"Références":8,
            "Liste":9
        }

        # ── Sidebar droite (inspecteur) ────────────────────────────────────
        self.inspector=InspectorPanel(self.pm); self.inspector.setFixedWidth(275)
        self.inspector.ins_name.textChanged.connect(self.sync_name)
        self.inspector.ins_synopsis.textChanged.connect(self.save_inspector)
        self.inspector.ins_status.currentTextChanged.connect(self.save_inspector)

        self.middle_area.addWidget(self.left_sidebar)
        self.middle_area.addWidget(self.central_stack)
        self.middle_area.addWidget(self.inspector)
        self.main_layout.addLayout(self.middle_area)

        # ── Barre de statut ────────────────────────────────────────────────
        self.status_bar=QWidget(); self.status_bar.setFixedHeight(45)
        sl=QHBoxLayout(self.status_bar); sl.setContentsMargins(4,0,8,0)

        self.status_left=QWidget(); self.status_left.setFixedWidth(250)
        sll=QHBoxLayout(self.status_left)
        self.btn_page=QPushButton("📄+"); self.btn_page.setFixedWidth(50)
        self.btn_folder=QPushButton("📁+"); self.btn_folder.setFixedWidth(50)
        self.btn_cfg=QPushButton("⚙"); self.btn_cfg.setFixedWidth(50)
        for b in [self.btn_page,self.btn_folder,self.btn_cfg]:
            b.setStyleSheet("color:white;font-weight:bold;font-size:16px;border:none;"); sll.addWidget(b)
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
        # Manuscrit
        ms_root=self.roots["Manuscrit"]; ms_root.takeChildren()
        def add_ms(parent_widget,uid):
            d=self.pm.items.get(uid)
            if not d: return
            icon=self._get_ms_icon(d)
            node=QTreeWidgetItem(parent_widget,[f"{icon} {d.name}"])
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
                icon = "📁" if c._is_folder else SimpleCardData.ICON_MAP.get(c.kind,"📄")
                node=QTreeWidgetItem(parent_widget,[f"{icon} {c.name}"])
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
                # Auto-refresh des vues
                if self._current_view_index==self.STACK["Liste"]:
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

    def sync_tree_order_from_listview(self, lv: "ListViewWidget"):
        """Resynchronise l'arbre principal depuis l'ordre affiché en Vue Liste."""
        ms_root = self.roots["Manuscrit"]
        # Collecter l'ordre des uid depuis la listview (top level)
        def get_uid_order(lv_parent):
            uids = []
            for i in range(lv_parent.childCount()):
                child = lv_parent.child(i)
                uid = child.data(0, Qt.ItemDataRole.UserRole)
                if uid:
                    uids.append((uid, child))
            return uids
        # Réordonner les enfants de ms_root
        uid_order = get_uid_order(lv.tree.invisibleRootItem())
        # Détacher et réattacher dans le nouvel ordre
        for i, (uid, _) in enumerate(uid_order):
            app_node = self._find_tree_node_by_uid(uid)
            if app_node and app_node.parent():
                parent = app_node.parent()
                idx = parent.indexOfChild(app_node)
                if idx != i:
                    parent.takeChild(idx)
                    parent.insertChild(i, app_node)

    def update_inspector_only(self, node):
        """Appelé depuis ListViewWidget (simple clic)."""
        data=node.data(0,Qt.ItemDataRole.UserRole)
        if isinstance(data,ItemData):
            self.inspector.load_data(data,self.pm)

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
        self.act_text  = make_action("📝","Texte",self);  self.act_text.triggered.connect(self._switch_to_text)
        self.act_cards = make_action("🗂","Cartes",self);  self.act_cards.triggered.connect(self.show_card_view)
        self.act_list  = make_action("☰","Liste",self);   self.act_list.triggered.connect(self.show_list_view)
        self.act_zen   = make_action("🧘","Zen",self);    self.act_zen.triggered.connect(self.toggle_zen)

        # Left: Sauvegarder, Annuler, Rétablir
        for act in [act_save, act_undo, act_redo]:
            self.main_toolbar.addAction(act)
        # Spacer centre-gauche
        sp_cl = QWidget(); sp_cl.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Preferred)
        self.main_toolbar.addWidget(sp_cl)
        # Centre: Texte, Cartes, Liste
        for act in [self.act_text, self.act_cards, self.act_list]:
            self.main_toolbar.addAction(act)
        # Spacer centre-droit
        sp_cr = QWidget(); sp_cr.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Preferred)
        self.main_toolbar.addWidget(sp_cr)
        # Right: Zen
        self.main_toolbar.addAction(self.act_zen)

    def _load_item_in_editor(self, tree_node, data: ItemData):
        """Charge un item dans l'éditeur. Si il a des enfants, mode composite."""
        child_items = []
        for i in range(tree_node.childCount()):
            ch = tree_node.child(i)
            cd = ch.data(0, Qt.ItemDataRole.UserRole)
            if isinstance(cd, ItemData): child_items.append((ch, cd))

        if child_items:
            self._load_composite(tree_node, data, child_items)
        else:
            self._exit_composite_mode()
            self.editor.blockSignals(True)
            self.editor.setPlainText(data.content)
            self.editor.blockSignals(False)

    def _load_composite(self, parent_node, parent_data: ItemData, children):
        """Affiche les sous-éléments avec séparateurs non-éditables (QTextBrowser)
        et zones éditables (QTextEdit) dans un QScrollArea vertical."""
        self._composite_mode = True
        self._composite_children = [(node, data) for node, data in children]
        self._composite_editors = {}  # uid → QTextEdit

        # Vider et recréer le conteneur composite dans le stack
        # On remplace temporairement le widget central de l'éditeur texte
        tv_l = self.text_editor_container.layout()

        # Supprimer l'ancien widget composite s'il existe
        if hasattr(self, "_composite_scroll") and self._composite_scroll:
            tv_l.removeWidget(self._composite_scroll)
            self._composite_scroll.deleteLater()
            self._composite_scroll = None

        # Cacher l'éditeur normal
        self.editor.setVisible(False)

        # Créer le scroll composite
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.Shape.NoFrame)
        container = QWidget()
        vlay = QVBoxLayout(container); vlay.setContentsMargins(60,24,60,24); vlay.setSpacing(0)
        scroll.setWidget(container)
        tv_l.addWidget(scroll)
        self._composite_scroll = scroll

        theme = self.themes[self.current_theme]
        font_size = self.pm.config.get("font_size", 13)

        for node, data in children:
            # Séparateur non-éditable
            sep = QTextBrowser()
            sep.setFixedHeight(32)
            sep.setFrameShape(QFrame.Shape.NoFrame)
            sep.setHtml(f"<div style='color:#888;font-weight:bold;font-size:11px;"
                        f"border-bottom:1px solid #ccc;padding:6px 0;'>"
                        f"── {data.name} {'─'*40}</div>")
            sep.setStyleSheet(f"background:{theme['editor_bg']};border:none;")
            sep.setReadOnly(True)
            vlay.addWidget(sep)

            # Zone éditable pour le contenu de cet enfant
            ed = QTextEdit()
            ed.setPlainText(data.content or "")
            ed.setFrameShape(QFrame.Shape.NoFrame)
            ed.setMinimumHeight(120)
            ed.setStyleSheet(
                f"background:{theme['editor_bg']};color:{theme['text']};"
                f"font-size:{font_size}pt;border:none;padding:8px 0;"
            )
            # Barres de défilement bien visibles
            ed.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            # Sauvegarder à chaque changement
            ed.textChanged.connect(lambda d=data, e=ed: self._save_composite_child(d, e))
            self._composite_editors[data.uid] = ed
            vlay.addWidget(ed)

        vlay.addStretch()

    def _save_composite_child(self, data: ItemData, editor: "QTextEdit"):
        """Sauvegarde le contenu d'un enfant en mode composite."""
        data.content = editor.toPlainText()
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

    def _switch_to_text(self):
        self.central_stack.setCurrentIndex(self.STACK["Texte"])
        self._current_view_index=self.STACK["Texte"]
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
        self.setWindowTitle(f"Scriptura v1.8 — {title}")
        self.current_item = None
        self._exit_composite_mode()
        self.editor.blockSignals(True); self.editor.clear(); self.editor.blockSignals(False)
        self.goal_btn.setVisible(False); self.goal_progress.setVisible(False)
        self._selected_card_uid = None
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
        self.setWindowTitle(f"Scriptura v1.8 — {self.pm.project_data.title}")
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
                data.content=self.editor.toPlainText()
                data.modified_at=datetime.now().isoformat()
                self._refresh_goal_progress(data)
        # Update stats even in composite mode
        self.update_stats()

    def save_inspector(self):
        if self.current_item:
            data=self.current_item.data(0,Qt.ItemDataRole.UserRole)
            if isinstance(data,ItemData):
                name,type_item,status,synopsis,notes=self.inspector.collect_properties()
                data.synopsis=synopsis; data.notes=notes
                data.status=status; data.type_item=type_item
                # Update meta display labels
                self.inspector.meta_type_lbl.setText(type_item or "—")
                self.inspector.meta_status_lbl.setText(status or "—")
                # Refresh list view if active
                if self.central_stack.currentIndex()==self.STACK["Liste"]:
                    self.list_view.refresh_row_from_inspector(data)

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
        txt=self.editor.toPlainText()
        if data.goal_unit=="mots": current=len(txt.split()); goal=data.word_goal
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
        """Crée un widget carte avec liseré, effets empilés, clic pour sélection."""
        label_color="#888888"
        for lbl in self.pm.get_labels():
            if lbl["name"]==data.label: label_color=lbl["color"]; break
        has_children = child.childCount() > 0
        is_selected  = (selected_uid == data.uid)

        # Conteneur externe avec ombre et effet de pile
        wrapper = QWidget()
        wrapper.setFixedSize(240, 185)
        wl = QVBoxLayout(wrapper); wl.setContentsMargins(0,0,0,0)

        if has_children:
            # Effet "cartes empilées" : 2 pseudo-ombres décalées
            for offset in [8, 4]:
                shadow = QFrame(wrapper)
                shadow.setGeometry(offset, offset, 224, 165)
                shadow.setStyleSheet(
                    f"background:{theme['card_bg']};border:1px solid {label_color}40;"
                    f"border-radius:8px;opacity:0.5;"
                )

        # Outer (liseré couleur en haut)
        outer = QFrame(wrapper); outer.setGeometry(0, 0, 224, 165)
        outer.setStyleSheet(f"background:{label_color};border-radius:8px;")
        outer_l = QVBoxLayout(outer); outer_l.setContentsMargins(0,5,0,0); outer_l.setSpacing(0)

        # Inner card
        card = QFrame()
        bg = theme["highlight"] if is_selected else theme["card_bg"]
        card.setStyleSheet(
            f"background:{bg};color:{theme['text']};border:none;border-radius:0 0 8px 8px;"
        )
        card_l = QVBoxLayout(card); card_l.setContentsMargins(10,8,10,8); card_l.setSpacing(4)

        # Titre éditable au clic
        title_lbl = QLabel(f"<b>{data.name}</b>"); title_lbl.setWordWrap(True)
        title_lbl.setCursor(Qt.CursorShape.PointingHandCursor)
        card_l.addWidget(title_lbl)

        # Statut
        status_combo = QComboBox()
        status_combo.addItems(self.pm.get_statuses())
        status_combo.setCurrentText(data.status)
        status_combo.setStyleSheet("font-size:10px;max-width:140px;")
        status_combo.currentTextChanged.connect(lambda txt,d=data: setattr(d,"status",txt))
        card_l.addWidget(status_combo)

        # Synopsis
        syn_edit = QTextEdit(); syn_edit.setPlainText(data.synopsis or "")
        syn_edit.setFixedHeight(52); syn_edit.setStyleSheet("font-size:10px;border:none;background:transparent;")
        syn_edit.textChanged.connect(lambda d=data,e=syn_edit: setattr(d,"synopsis",e.toPlainText()))
        card_l.addWidget(syn_edit)

        outer_l.addWidget(card,1)
        wl.addWidget(outer)

        # Clic sur titre → ouvre l'éditeur inline de titre
        def on_title_click(ev, d=data, lbl=title_lbl, c=child):
            # Sélectionner la carte
            self._selected_card_uid = d.uid
            self.show_card_view()  # refresh pour surbrillance
            # Charger dans inspecteur
            self.current_item = c
            self.inspector.load_data(d, self.pm)
        title_lbl.mousePressEvent = on_title_click

        # Double-clic sur outer → ouvre l'éditeur texte
        def on_dbl(ev, c=child, d=data):
            self.open_item_in_editor(c)
        outer.mouseDoubleClickEvent = on_dbl

        return wrapper

    def show_card_view(self):
        self.central_stack.setCurrentIndex(self.STACK["Cartes"])
        self._current_view_index=self.STACK["Cartes"]
        while self.card_grid.count():
            w=self.card_grid.takeAt(0).widget()
            if w: w.deleteLater()
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
        sel=self.tree.currentItem()
        # Si pas de sélection ou racine Manuscrit → afficher tout le manuscrit
        if not sel or sel.data(0,Qt.ItemDataRole.UserRole)=="ROOT_GROUP":
            parent=self.roots["Manuscrit"]
        else:
            parent=sel
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
    def setup_format_toolbar(self):
        self.font_box=QFontComboBox(); self.font_box.setFontFilters(QFontComboBox.FontFilter.ScalableFonts)
        self.font_box.currentFontChanged.connect(self.apply_font_change)
        self.size_box=QSpinBox(); self.size_box.setValue(13)
        self.size_box.valueChanged.connect(lambda v: self.editor.setFontPointSize(float(v)))
        self.format_toolbar.addWidget(self.font_box); self.format_toolbar.addWidget(self.size_box)
        self.format_toolbar.addSeparator()
        for label,fn in [("G",lambda: self.editor.setFontWeight(700 if self.editor.fontWeight()<700 else 400)),
                          ("I",lambda: self.editor.setFontItalic(not self.editor.fontItalic())),
                          ("S",lambda: self.editor.setFontUnderline(not self.editor.fontUnderline()))]:
            a=QAction(label,self); a.triggered.connect(fn); self.format_toolbar.addAction(a)
        self.format_toolbar.addSeparator()
        for label,flag in [("◀",Qt.AlignmentFlag.AlignLeft),("≡",Qt.AlignmentFlag.AlignCenter),
                           ("▶",Qt.AlignmentFlag.AlignRight),("▬",Qt.AlignmentFlag.AlignJustify)]:
            a=QAction(label,self); a.triggered.connect(lambda _,f=flag: self.editor.setAlignment(f))
            self.format_toolbar.addAction(a)
        self.format_toolbar.addSeparator()
        a_c=QAction("🎨",self); a_c.triggered.connect(self.change_color); self.format_toolbar.addAction(a_c)

    def apply_font_change(self,font):
        font.setPointSize(self.size_box.value())
        self.editor.setFont(font); self.editor.setCurrentFont(font); self.editor.setFocus()

    def sync_format_toolbar(self):
        f=self.editor.currentCharFormat().font(); self.font_box.setCurrentFont(f)
        if f.pointSize()>0: self.size_box.setValue(int(f.pointSize()))

    def change_color(self):
        c=QColorDialog.getColor()
        if c.isValid(): self.editor.setTextColor(c)

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
        # Passer la couleur de texte à la Vue Liste
        self.list_view.set_theme_text_color(c['text'])
        # Style Vue Liste tree
        self.list_view.tree.setStyleSheet(
            f"QTreeWidget{{background:{c['editor_bg']};color:{c['text']};border:none;}}"
            f"QTreeWidget::item:selected{{background:{c['highlight']};color:white;}}"
            f"QTreeWidget::item:hover{{background:{c['highlight']}40;}}"
        )
        # Style arborescence gauche selon thème
        sb = label_text_color(c["sidebar"])
        self.tree.setStyleSheet(
            f"QTreeWidget{{background:{c['sidebar']};color:{sb};border:none;}}"
            f"QTreeWidget::item:selected{{background:{c['accent']}80;color:{sb};border-radius:3px;}}"
            f"QTreeWidget::item:hover{{background:{c['accent']}40;}}"
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

    # ─── Stats ────────────────────────────────────────────────────────────────
    def update_stats(self):
        t=self.editor.toPlainText()
        self.stats_label.setText(f"Mots : {len(t.split())}  |  Caractères : {len(t)}")
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