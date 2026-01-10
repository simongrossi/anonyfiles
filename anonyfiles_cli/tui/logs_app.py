from pathlib import Path
import yaml
import asyncio
import logging
from functools import lru_cache
from datetime import datetime

from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, DataTable, Static, DirectoryTree, Button, Input, Switch, Label, RichLog
from textual.containers import Vertical, Horizontal, Grid
from textual.validation import Integer, Regex


# --- Constantes et Configuration ---
PROFILES_DIR = Path(__file__).parent.parent / "log_profiles"
HISTORY_FILE = Path.home() / ".anonyfiles" / "tui_history.yaml"


# --- Fonctions de cache pour les performances ---

@lru_cache(maxsize=32)
def load_profile_config(profile_path: str) -> dict:
    """Charge et met en cache un fichier de configuration de profil."""
    try:
        with open(profile_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.error(f"Erreur lors du chargement du profil {profile_path}: {e}")
        return {}


@lru_cache(maxsize=1)
def get_profiles_list() -> list:
    """Récupère et met en cache la liste des profils disponibles."""
    if not PROFILES_DIR.is_dir():
        return []
    return sorted(list(PROFILES_DIR.glob("*.yaml")))


# --- Système d'historique ---

def save_to_history(profile: str, input_path: Path, options: dict, success: bool) -> None:
    """Sauvegarde un traitement dans l'historique."""
    try:
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)

        # Charge l'historique existant
        history = []
        if HISTORY_FILE.is_file():
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                history = yaml.safe_load(f) or []

        # Convertit tous les objets Path en strings pour la sérialisation YAML
        serializable_options = {}
        for key, value in options.items():
            if isinstance(value, Path):
                serializable_options[key] = str(value)
            else:
                serializable_options[key] = value

        # Ajoute le nouveau traitement
        history.insert(0, {
            "timestamp": datetime.now().isoformat(),
            "profile": profile,
            "input_path": str(input_path),
            "options": serializable_options,
            "success": success,
        })

        # Garde seulement les 50 derniers
        history = history[:50]

        # Sauvegarde avec safe_dump pour éviter les tags Python personnalisés
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            yaml.safe_dump(history, f, indent=2, sort_keys=False, allow_unicode=True)

    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde de l'historique: {e}")


def get_history() -> list:
    """Récupère l'historique des traitements."""
    try:
        if HISTORY_FILE.is_file():
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or []
    except Exception as e:
        logger.error(f"Erreur lors de la lecture de l'historique: {e}")
    return []


# --- Écrans de l'application ---

logger = logging.getLogger(__name__)

class ProfileSelectionScreen(Screen):
    """Écran pour sélectionner un profil d'anonymisation."""

    BINDINGS = [
        ("enter", "select_profile", "Valider"),
        ("escape", "app.quit", "Quitter"),
        ("/", "toggle_search", "Rechercher"),
        ("ctrl+r", "refresh", "Actualiser"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.search_mode = False
        self.all_profiles = []

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(classes="main-container"):
            yield Static("📋 Étape 1/4 : Sélectionnez un profil d'anonymisation", id="status_line")
            yield Input(placeholder="🔍 Tapez pour rechercher... (/ pour activer)", id="search_input", classes="mt1")
            yield DataTable(id="profiles_table", cursor_type="row")
        yield Footer()

    def on_mount(self) -> None:
        # Cache le champ de recherche par défaut
        self.query_one("#search_input").display = False
        self.load_profiles()

    def load_profiles(self, filter_text: str = "") -> None:
        """Charge les profils avec cache et filtre optionnel."""
        table = self.query_one(DataTable)
        table.clear(columns=True)
        table.add_columns("🏷️  Profil", "📝 Description")

        if not PROFILES_DIR.is_dir():
            table.add_row("[bold red]❌ Erreur[/bold red]", f"Le dossier des profils est introuvable: {PROFILES_DIR}")
            self.notify("Dossier des profils introuvable", severity="error", timeout=5)
            return

        # Utilise le cache pour récupérer la liste
        profile_files = get_profiles_list()
        if not profile_files:
            table.add_row("[bold yellow]⚠️  Aucun profil[/bold yellow]", "Aucun fichier .yaml trouvé.")
            self.notify("Aucun profil disponible", severity="warning", timeout=5)
            return

        default_profile_key = None
        if "profile" in self.app.state:
            default_profile_key = self.app.state["profile"]

        # Stocke tous les profils
        self.all_profiles = []
        matched_count = 0

        for profile_path in profile_files:
            # Utilise le cache pour charger la config
            config_data = load_profile_config(str(profile_path))
            description = config_data.get("description", "[dim italic]Aucune description[/dim italic]")

            profile_name = profile_path.stem

            # Applique le filtre si nécessaire
            if filter_text:
                search_in = f"{profile_name} {description}".lower()
                if filter_text.lower() not in search_in:
                    continue

            matched_count += 1
            try:
                table.add_row(f"[cyan bold]{profile_name}[/cyan bold]", description, key=profile_name)
                self.all_profiles.append(profile_name)
            except Exception as e:
                table.add_row(f"[red]{profile_name}[/red]", f"[bold red]❌ Erreur: {e}[/bold red]")

        # Message de statut
        if filter_text:
            status_msg = f"🔍 {matched_count}/{len(profile_files)} profil(s) correspondant(s)"
            self.notify(status_msg, timeout=2)
        else:
            self.notify(f"✅ {len(profile_files)} profil(s) chargé(s)", timeout=2)

        # Positionne le curseur
        if table.row_count > 0:
            if default_profile_key and default_profile_key in self.all_profiles:
                try:
                    table.move_cursor(row=table.get_row_index(default_profile_key))
                    self.query_one("#status_line").update(f"📋 Étape 1/4 : Profil précédent : [bold green]{default_profile_key}[/bold green] • Entrée pour valider")
                except KeyError:
                    table.move_cursor(row=0)
            else:
                table.move_cursor(row=0)
            table.focus()

    def action_toggle_search(self) -> None:
        """Active/désactive le mode recherche."""
        search_input = self.query_one("#search_input")
        self.search_mode = not self.search_mode

        if self.search_mode:
            search_input.display = True
            search_input.focus()
            self.notify("🔍 Mode recherche activé", timeout=2)
        else:
            search_input.display = False
            search_input.value = ""
            self.load_profiles()
            self.query_one(DataTable).focus()
            self.notify("❌ Recherche désactivée", timeout=2)

    def action_refresh(self) -> None:
        """Actualise la liste des profils."""
        # Vide le cache
        get_profiles_list.cache_clear()
        load_profile_config.cache_clear()

        self.load_profiles()
        self.notify("🔄 Liste des profils actualisée", timeout=2)

    def on_input_changed(self, event: Input.Changed) -> None:
        """Filtre les profils en temps réel."""
        if event.input.id == "search_input":
            self.load_profiles(filter_text=event.value)

    def action_select_profile(self) -> None:
        """Action pour sélectionner le profil actuel."""
        table = self.query_one(DataTable)
        if table.cursor_row < table.row_count:
            # Trigger row selected event
            table.action_select_cursor()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        profile_name = event.row_key.value
        if not profile_name:
            return
        self.app.state["profile"] = profile_name
        self.notify(f"✅ Profil '{profile_name}' sélectionné", timeout=2)
        self.app.push_screen(FileSelectionScreen())


class FileSelectionScreen(Screen):
    """Écran pour sélectionner un fichier ou un dossier."""

    BINDINGS = [
        ("backspace", "go_up", "Parent"),
        ("escape", "app.pop_screen", "Retour"),
        ("enter", "select_path", "Valider"),
        ("p", "preview", "Aperçu"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(classes="main-container"):
            yield Static("📁 Étape 2/4 : Sélectionnez un fichier ou dossier", id="status_line")
            yield Button("⬆️  Dossier Parent (Backspace)", id="go-up-button", classes="go-up-button")
            yield DirectoryTree(str(Path.cwd()), id="file_tree")
            with Horizontal(classes="mt1 button-row"):
                yield Button("👁️  Aperçu (P)", id="preview_button")
                yield Button("✅ Utiliser ce chemin (Enter)", id="select_path", variant="primary")
        yield Footer()

    def on_mount(self) -> None:
        tree = self.query_one(DirectoryTree)
        path_to_select = self.app.state.get("input_path", Path.cwd())

        if path_to_select.exists():
            start_path = path_to_select.parent if path_to_select.is_file() else path_to_select
            tree.path = start_path
        else:
            tree.path = Path.cwd()
        self._update_path_display(Path(tree.path))
        tree.focus()

    def action_go_up(self) -> None:
        """Remonte au dossier parent."""
        tree = self.query_one(DirectoryTree)
        current_path = Path(tree.path)
        parent = current_path.parent
        if parent != current_path:  # Évite de remonter au-delà de la racine
            tree.path = parent
            self._update_path_display(tree.path)
            self.notify(f"📁 {parent.name}", timeout=1)

    def action_select_path(self) -> None:
        """Action pour valider le chemin sélectionné."""
        tree = self.query_one(DirectoryTree)
        current_path = tree.cursor_node.data.path if tree.cursor_node else Path(tree.path)

        if not current_path:
            self.notify("❌ Aucun chemin sélectionné", severity="error", timeout=3)
            return

        self.app.state["input_path"] = current_path
        file_type = "📄 Fichier" if current_path.is_file() else "📁 Dossier"
        self.notify(f"✅ {file_type} sélectionné: {current_path.name}", timeout=2)
        self.app.push_screen(OptionsScreen())

    def _update_path_display(self, path: Path) -> None:
        """Met à jour l'affichage du statut."""
        self.query_one("#status_line").update(f"📁 Étape 2/4 : [bold cyan]{path}[/bold cyan]")

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        """Affiche le chemin du fichier sélectionné."""
        self.notify(f"📄 {event.path.name}", timeout=1)

    def on_directory_tree_directory_selected(self, event: DirectoryTree.DirectorySelected) -> None:
        """Entre dans le dossier sélectionné."""
        tree = self.query_one(DirectoryTree)
        tree.path = event.path
        self._update_path_display(event.path)
        self.notify(f"📁 {event.path.name}", timeout=1)

    def action_preview(self) -> None:
        """Affiche un aperçu du fichier sélectionné."""
        tree = self.query_one(DirectoryTree)
        current_path = tree.cursor_node.data.path if tree.cursor_node else Path(tree.path)

        if not current_path or not current_path.is_file():
            self.notify("⚠️  Sélectionnez un fichier pour l'aperçu", severity="warning", timeout=3)
            return

        # Vérifie la taille du fichier
        file_size = current_path.stat().st_size
        if file_size > 1_000_000:  # 1 MB
            self.notify("⚠️  Fichier trop volumineux pour l'aperçu (> 1 MB)", severity="warning", timeout=3)
            return

        try:
            with open(current_path, 'r', encoding='utf-8', errors='ignore') as f:
                # Lit les 50 premières lignes
                lines = []
                for i, line in enumerate(f):
                    if i >= 50:
                        break
                    lines.append(line.rstrip())

            preview_text = "\n".join(lines)
            if len(lines) == 50:
                preview_text += "\n\n[dim italic]... (50 premières lignes affichées)[/dim italic]"

            # Affiche dans une notification longue
            self.notify(
                f"📄 Aperçu de {current_path.name}:\n\n{preview_text[:500]}...",
                timeout=10
            )
        except Exception as e:
            self.notify(f"❌ Impossible de lire le fichier: {e}", severity="error", timeout=3)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "select_path":
            self.action_select_path()
        elif event.button.id == "go-up-button":
            self.action_go_up()
        elif event.button.id == "preview_button":
            self.action_preview()


class DirectorySelectionScreen(Screen):
    """Écran générique pour sélectionner un dossier."""

    BINDINGS = [
        ("backspace", "go_up", "Parent"),
        ("escape", "app.pop_screen", "Annuler"),
        ("enter", "select_path", "Valider"),
    ]

    def __init__(self, title: str, target_state_key: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.screen_title = title
        self.target_state_key = target_state_key

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(classes="main-container"):
            yield Static(f"📂 {self.screen_title}", id="status_line")
            yield Button("⬆️  Dossier Parent (Backspace)", id="go-up-button", classes="go-up-button")
            yield DirectoryTree(str(Path.cwd()), id="dir_tree")
            yield Button("✅ Valider ce dossier (Enter)", id="select_path", variant="primary", classes="mt1")
        yield Footer()

    def on_mount(self) -> None:
        tree = self.query_one(DirectoryTree)
        path_to_select = self.app.state.get(self.target_state_key) or self.app.state.get("input_path") or Path.cwd()

        if path_to_select.exists():
            tree.path = path_to_select
        else:
            tree.path = Path.cwd()
        self._update_path_display(Path(tree.path))
        tree.focus()

    def action_go_up(self) -> None:
        """Remonte au dossier parent."""
        tree = self.query_one(DirectoryTree)
        current_path = Path(tree.path)
        parent = current_path.parent
        if parent != current_path:
            tree.path = parent
            self._update_path_display(parent)
            self.notify(f"📁 {parent.name}", timeout=1)

    def action_select_path(self) -> None:
        """Action pour valider le dossier sélectionné."""
        tree = self.query_one(DirectoryTree)
        current_path = Path(tree.path)
        self.app.state[self.target_state_key] = current_path
        self.notify(f"✅ Dossier sélectionné: {current_path.name}", timeout=2)
        self.app.pop_screen()

    def _update_path_display(self, path: Path) -> None:
        """Met à jour l'affichage du chemin."""
        self.query_one("#status_line").update(f"📂 {self.screen_title}: [bold cyan]{path}[/bold cyan]")

    def on_directory_tree_directory_selected(self, event: DirectoryTree.DirectorySelected) -> None:
        tree = self.query_one(DirectoryTree)
        tree.path = event.path
        self._update_path_display(event.path)
        self.notify(f"📁 {event.path.name}", timeout=1)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "select_path":
            self.action_select_path()
        elif event.button.id == "go-up-button":
            self.action_go_up()


class OptionsScreen(Screen):
    """Écran pour configurer les options d'anonymisation."""

    BINDINGS = [
        ("escape", "app.pop_screen", "Retour"),
        ("ctrl+l", "launch", "Lancer"),
        ("f1", "help", "Aide"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(classes="main-container"):
            yield Static("⚙️  Étape 3/4 : Configurez les options d'anonymisation", id="status_line")

            # Section pour les dossiers avec boutons
            with Vertical(classes="mt1"):
                # Dossier de sortie
                with Horizontal(classes="dir-selector-row"):
                    yield Label("📤 Sortie:", classes="dir-label")
                    yield Static("[dim italic]Défaut : à côté de l'entrée[/dim italic]", id="output_path_display", classes="dir-path")
                    yield Button("📂", id="select_output_path", classes="dir-button")

                # Dossier des audits
                with Horizontal(classes="dir-selector-row"):
                    yield Label("📊 Audits:", classes="dir-label")
                    yield Static("[dim italic]Non sauvegardés[/dim italic]", id="audit_path_display", classes="dir-path")
                    yield Button("📂", id="select_audit_path", classes="dir-button")

            # Section pour les autres options (2 colonnes)
            with Grid(classes="option-grid mt1"):
                # Mapping global
                yield Label("🗺️  Fichier de mapping:")
                yield Input(
                    placeholder="/chemin/vers/mapping.csv",
                    id="global_mapping_path",
                    classes="input-container",
                    validators=[
                        Regex(r"^$|.*\.csv$", failure_description="Le chemin doit se terminer par .csv")
                    ]
                )

                # Pattern
                yield Label("🔍 Pattern de fichier:")
                yield Input(value="*.log", id="pattern", classes="input-container")

                # Parallèle
                yield Label("⚡ Traitement parallèle:")
                yield Input(
                    value="0",
                    id="parallel",
                    classes="input-container",
                    validators=[
                        Integer(minimum=0, failure_description="Doit être un nombre ≥ 0")
                    ]
                )

                # Récursif
                yield Label("🔄 Recherche récursive:")
                yield Switch(id="recursive")

                # Dry-run
                yield Label("🧪 Mode test (dry-run):")
                yield Switch(id="dry_run")

            with Horizontal(classes="mt2"):
                yield Button("🚀 Lancer l'anonymisation (Ctrl+L)", id="launch_button", variant="success")
        yield Footer()
    
    def on_mount(self) -> None:
        self.update_displays()
        self.call_after_refresh(self.update_launch_button_state)
        # Affiche un résumé des paramètres
        profile = self.app.state.get("profile", "?")
        input_path = self.app.state.get("input_path", Path.cwd())
        self.notify(f"Profil: {profile} | Entrée: {input_path.name}", timeout=3)

    def on_screen_resume(self) -> None:
        """Appelé lorsqu'un sous-écran (comme DirectorySelectionScreen) est fermé."""
        # Notifie l'utilisateur des chemins sélectionnés
        output_path = self.app.state.get("output_path")
        audit_path = self.app.state.get("audit_logs_dir")

        if output_path:
            self.notify(f"✅ Dossier de sortie: {output_path.name}", timeout=3)
        if audit_path:
            self.notify(f"✅ Dossier des audits: {audit_path.name}", timeout=3)

        self.update_displays()
        self.call_after_refresh(self.update_launch_button_state)

    def on_input_changed(self, _: Input.Changed) -> None:
        """Met à jour l'état du bouton de lancement à chaque modification d'un champ."""
        self.update_launch_button_state()

    def action_launch(self) -> None:
        """Action pour lancer le traitement."""
        if not self.query_one("#launch_button").disabled:
            self.on_button_pressed(type('Event', (), {'button': type('Button', (), {'id': 'launch_button'})()})())

    def action_help(self) -> None:
        """Affiche l'aide."""
        help_text = """
⚙️  Options disponibles:
• Dossier de sortie: où sauvegarder les fichiers anonymisés
• Dossier des audits: logs de traitement détaillés
• Mapping global: fichier CSV avec correspondances
• Pattern: filtre les fichiers (ex: *.log)
• Parallèle: nb de processus (0 = séquentiel)
• Récursif: chercher dans les sous-dossiers
        """
        self.notify(help_text.strip(), timeout=8)

    def update_launch_button_state(self) -> None:
        """Active ou désactive le bouton de lancement en fonction de la validité des champs."""
        is_valid = all(inp.is_valid for inp in self.query(Input))
        self.query_one("#launch_button").disabled = not is_valid

        if not is_valid:
            invalid_inputs = [inp for inp in self.query(Input) if not inp.is_valid]
            if invalid_inputs:
                self.notify("⚠️  Certains champs contiennent des erreurs", severity="warning", timeout=2)

    def update_displays(self) -> None:
        """Met à jour tous les affichages de chemin et les champs de saisie."""
        self._update_path_display("output_path", self.app.state.get("output_path"), "[dim italic]Défaut : à côté de l'entrée[/dim italic]")
        self._update_path_display("audit_path", self.app.state.get("audit_logs_dir"), "[dim italic]Non sauvegardés[/dim italic]")

        last_options = self.app.state.get("options", {})
        if last_options:
            self.query_one("#global_mapping_path", Input).value = last_options.get("global_mapping_path", "")
            self.query_one("#pattern", Input).value = last_options.get("pattern", "*.log")
            self.query_one("#parallel", Input).value = str(last_options.get("parallel", 0))
            self.query_one("#recursive", Switch).value = last_options.get("recursive", False)
            self.query_one("#dry_run", Switch).value = last_options.get("dry_run", False)

    def _update_path_display(self, base_id: str, path: Path | None, default_text: str):
        display = self.query_one(f"#{base_id}_display", Static)
        if path:
            # Affiche les 2 derniers niveaux du chemin pour plus de contexte
            parts = path.parts
            if len(parts) >= 2:
                short_path = f"{parts[-2]}/{parts[-1]}"
            else:
                short_path = path.name
            display.update(f"[bold green]✓ {short_path}[/bold green]")
        else:
            display.update(default_text)

        # Force le refresh du widget
        display.refresh()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "select_output_path":
            self.app.push_screen(DirectorySelectionScreen("Sélectionnez le dossier de sortie", "output_path"))
        elif event.button.id == "select_audit_path":
            self.app.push_screen(DirectorySelectionScreen("Sélectionnez le dossier des audits", "audit_logs_dir"))
        elif event.button.id == "launch_button":
            # Récupère les valeurs et valide
            parallel_value = self.query_one("#parallel").value
            try:
                # Validation de la valeur parallèle
                int(parallel_value) if parallel_value else 0
            except ValueError:
                self.notify("❌ Valeur parallèle invalide", severity="error", timeout=3)
                return

            is_dry_run = self.query_one("#dry_run").value

            self.app.state["options"] = {
                "output_path": self.app.state.get("output_path"),
                "audit_logs_dir": self.app.state.get("audit_logs_dir"),
                "global_mapping_path": self.query_one("#global_mapping_path").value,
                "pattern": self.query_one("#pattern").value,
                "parallel": parallel_value,
                "recursive": self.query_one("#recursive").value,
                "dry_run": is_dry_run,
            }

            # Message de confirmation
            if is_dry_run:
                self.notify("🧪 Mode test activé - Aucun fichier ne sera modifié", timeout=3)
            else:
                self.notify("🚀 Lancement du traitement...", timeout=2)
            self.app.push_screen(ProcessingScreen())


class ProcessingScreen(Screen):
    """Écran qui lance et affiche le résultat du traitement."""

    BINDINGS = [
        ("escape", "cancel", "Annuler"),
        ("r", "restart", "Recommencer"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(classes="main-container"):
            yield Static("🚀 Étape 4/4 : Traitement en cours...", id="status_line")
            yield Static("", id="stats_line", classes="info-message mt1")
            yield RichLog(id="log-container", highlight=True, markup=True)
        yield Footer()

    def on_mount(self) -> None:
        # Affiche un résumé avant de commencer
        state = self.app.state
        profile = state.get("profile", "?")
        input_path = state.get("input_path", Path.cwd())
        opts = state.get("options", {})
        parallel = opts.get("parallel", "0")

        summary = f"📋 Profil: {profile} | 📁 Entrée: {input_path.name}"
        if parallel and parallel != "0":
            summary += f" | ⚡ Parallèle: {parallel}"

        self.query_one("#stats_line").update(summary)
        self.notify("🚀 Démarrage du traitement...", timeout=2)
        self.run_worker(self.run_anonymization, thread=True)

    def action_cancel(self) -> None:
        """Permet d'annuler et revenir en arrière."""
        # Note: Dans une version future, on pourrait tuer le processus ici
        self.notify("⚠️  Utilisez Ctrl+C pour arrêter le processus", severity="warning", timeout=3)

    def action_restart(self) -> None:
        """Recommence une nouvelle analyse depuis le début."""
        # Réinitialise l'état de l'application
        self.app.state.clear()

        # Utilise une approche simple avec try/except pour gérer les erreurs
        try:
            # Ferme les écrans un par un de manière synchrone
            # Pile: ProfileSelectionScreen -> FileSelectionScreen -> OptionsScreen -> ProcessingScreen (actuel)
            self.app.pop_screen()  # ProcessingScreen
            self.app.pop_screen()  # OptionsScreen
            self.app.pop_screen()  # FileSelectionScreen
            # On reste sur ProfileSelectionScreen

            self.app.notify("🔄 Nouvelle analyse - Sélectionnez un profil", timeout=3)
        except Exception as e:
            self.app.notify(f"⚠️ Erreur lors du redémarrage: {e}", severity="error", timeout=5)

    async def run_anonymization(self) -> None:
        log = self.query_one(RichLog)
        state = self.app.state

        # Construit la commande CLI à partir de l'état de l'application
        command = [
            "anonyfiles-cli", "logs", "anonymize",
            str(state["input_path"]),
            "--profile", state["profile"]
        ]
        opts = state.get("options", {})
        output_path = opts.get("output_path")
        if output_path:
            command.extend(["--output", str(output_path)])
        audit_dir = opts.get("audit_logs_dir")
        if audit_dir:
            command.extend(["--audit-logs-dir", str(audit_dir)])
        global_mapping = opts.get("global_mapping_path")
        if global_mapping:
            command.extend(["--global-mapping", global_mapping])
        if opts.get("pattern"):
            command.extend(["--pattern", opts["pattern"]])
        if opts.get("recursive"):
            command.append("--recursive")
        if opts.get("parallel") and int(opts.get("parallel", 0)) > 0:
            command.extend(["--parallel", str(opts["parallel"])])

        # Affiche la commande exécutée de manière formatée
        log.write("╔═══════════════════════════════════════════════════════════════╗")
        log.write("║          [bold cyan]COMMANDE EXÉCUTÉE[/bold cyan]                                    ║")
        log.write("╚═══════════════════════════════════════════════════════════════╝")

        # Affiche la commande sur plusieurs lignes pour une meilleure lisibilité
        log.write(f"[bold yellow]$[/bold yellow] [bold cyan]{command[0]}[/bold cyan] \\")

        i = 1
        while i < len(command):
            arg = command[i]
            # Si c'est une option (commence par --), on affiche l'option et sa valeur
            if arg.startswith("--"):
                # Vérifie si l'argument suivant est la valeur de cette option
                if i + 1 < len(command) and not command[i + 1].startswith("--"):
                    next_arg = command[i + 1]
                    log.write(f"    {arg} [yellow]{next_arg}[/yellow] \\")
                    i += 2  # Saute la valeur
                    continue
                else:
                    log.write(f"    {arg} \\")
            else:
                # C'est un argument positionnel
                log.write(f"    [yellow]{arg}[/yellow] \\")
            i += 1

        log.write("")  # Ligne vide après la commande

        # Lance la commande en sous-processus et stream la sortie
        import time
        start_time = time.time()

        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # Lit stdout et stderr en temps réel avec statistiques
        line_count = 0
        async def read_stream(stream, log_widget, is_stderr=False):
            nonlocal line_count
            while True:
                line = await stream.readline()
                if line:
                    line_count += 1
                    decoded = line.decode('utf-8').strip()

                    # Colore les lignes selon le type
                    if is_stderr:
                        formatted = f"[red]⚠️  {decoded}[/red]"
                    elif "succès" in decoded.lower() or "success" in decoded.lower():
                        formatted = f"[green]✅ {decoded}[/green]"
                    elif "erreur" in decoded.lower() or "error" in decoded.lower():
                        formatted = f"[red]❌ {decoded}[/red]"
                    elif "traitement" in decoded.lower() or "processing" in decoded.lower():
                        formatted = f"[cyan]⚙️  {decoded}[/cyan]"
                    else:
                        formatted = decoded

                    # Appelle la méthode dans le thread principal de la TUI
                    self.app.call_from_thread(log_widget.write, formatted)

                    # Met à jour les stats toutes les 5 lignes
                    if line_count % 5 == 0:
                        elapsed = time.time() - start_time
                        self.app.call_from_thread(
                            self.query_one("#stats_line").update,
                            f"⏱️  Temps écoulé: {elapsed:.1f}s | 📊 Lignes: {line_count}"
                        )
                else:
                    break

        await asyncio.gather(
            read_stream(process.stdout, log, is_stderr=False),
            read_stream(process.stderr, log, is_stderr=True)
        )

        await process.wait()

        # Calcule le temps total
        total_time = time.time() - start_time

        status_line = self.query_one("#status_line")
        stats_line = self.query_one("#stats_line")

        success = process.returncode == 0

        # Sauvegarde dans l'historique
        save_to_history(
            profile=state["profile"],
            input_path=state["input_path"],
            options=opts,
            success=success
        )

        if success:
            log.write("\n╔═══════════════════════════════════════════════════════════════╗")
            log.write("║          [bold green]✅ TRAITEMENT TERMINÉ AVEC SUCCÈS[/bold green]                    ║")
            log.write("╚═══════════════════════════════════════════════════════════════╝")

            status_line.update("[bold green]✅ Traitement terminé avec succès ! (r pour recommencer, q pour quitter)[/bold green]")
            stats_line.update(f"⏱️  Temps total: {total_time:.2f}s | 📊 Lignes traitées: {line_count}")
            self.notify("✅ Traitement terminé avec succès !", timeout=5)
        else:
            log.write("\n╔═══════════════════════════════════════════════════════════════╗")
            log.write("║          [bold red]❌ ERREUR DURANT LE TRAITEMENT[/bold red]                     ║")
            log.write("╚═══════════════════════════════════════════════════════════════╝")

            status_line.update(f"[bold red]❌ Erreur (code: {process.returncode}) - (r pour recommencer, q pour quitter)[/bold red]")
            stats_line.update(f"⏱️  Temps écoulé: {total_time:.2f}s | ❌ Code d'erreur: {process.returncode}")
            self.notify(f"❌ Erreur durant le traitement (code {process.returncode})", severity="error", timeout=5)


class LogsApp(App):
    """Une interface textuelle pour l'anonymisation des logs."""

    CSS_PATH = "logs_app.css"
    BINDINGS = [
        ("q", "quit", "Quitter"),
        ("d", "toggle_dark", "Thème"),
        ("ctrl+c", "quit", "Quitter"),
        ("f1", "help_global", "Aide"),
        ("h", "show_history", "Historique"),
    ]
    SCREENS = {
        "profiles": ProfileSelectionScreen,
        "files": FileSelectionScreen,
        "options": OptionsScreen,
        "process": ProcessingScreen,
    }
    TITLE = "🔒 Anonyfiles - Anonymiseur de Logs"
    SUB_TITLE = "Interface Textuelle Interactive"
    TUI_STATE_FILE = Path.home() / ".anonyfiles" / "tui_state.yaml"

    def __init__(self):
        super().__init__()
        self.state = self._load_state()

    def action_help_global(self) -> None:
        """Affiche l'aide globale."""
        help_text = """
╔═══════════════════════════════════════════════════════════════╗
║                  🔒 ANONYFILES - AIDE                         ║
╚═══════════════════════════════════════════════════════════════╝

📋 WORKFLOW:
  1. Sélectionnez un profil d'anonymisation (/ pour rechercher)
  2. Choisissez un fichier ou dossier à traiter (P pour aperçu)
  3. Configurez les options (mode dry-run disponible)
  4. Lancez le traitement et observez les résultats

⌨️  RACCOURCIS CLÉS:
  • Q / Ctrl+C : Quitter l'application
  • D : Basculer entre thème sombre/clair
  • H : Afficher l'historique des traitements
  • / : Rechercher dans les profils
  • P : Aperçu du fichier sélectionné
  • Ctrl+R : Actualiser la liste des profils
  • Escape : Retour à l'écran précédent
  • Enter : Valider la sélection
  • F1 : Afficher cette aide
  • ↑/↓ : Navigation dans les listes

💡 ASTUCES:
  • Cache intelligent pour performances optimales
  • Paramètres sauvegardés automatiquement
  • Historique des 50 derniers traitements
  • Mode dry-run pour tester sans modifier
  • Recherche instantanée dans les profils
        """
        self.notify(help_text.strip(), timeout=15)

    def action_show_history(self) -> None:
        """Affiche l'historique des traitements."""
        history = get_history()

        if not history:
            self.notify("📜 Aucun historique disponible", timeout=3)
            return

        # Affiche les 10 derniers traitements
        history_text = "📜 HISTORIQUE DES TRAITEMENTS (10 derniers):\n\n"

        for i, entry in enumerate(history[:10], 1):
            timestamp = entry.get("timestamp", "?")
            profile = entry.get("profile", "?")
            input_path = Path(entry.get("input_path", "?")).name
            success = entry.get("success", False)
            status = "✅" if success else "❌"

            # Parse timestamp
            try:
                dt = datetime.fromisoformat(timestamp)
                time_str = dt.strftime("%d/%m %H:%M")
            except:
                time_str = timestamp[:16]

            history_text += f"{i}. {status} {time_str} | {profile} | {input_path}\n"

        history_text += f"\n💾 Total: {len(history)} traitement(s) enregistré(s)"

        self.notify(history_text, timeout=10)

    def _load_state(self) -> dict:
        """Charge l'état de la TUI depuis un fichier."""
        if self.TUI_STATE_FILE.is_file():
            try:
                with open(self.TUI_STATE_FILE, 'r', encoding='utf-8') as f:
                    loaded_state = yaml.safe_load(f)
                    # Convert paths back to Path objects
                    if isinstance(loaded_state, dict):
                        for key in ["input_path", "output_path", "audit_logs_dir"]:
                            if key in loaded_state and loaded_state[key]:
                                try:
                                    loaded_state[key] = Path(loaded_state[key])
                                except TypeError:
                                    loaded_state[key] = None # Handle potential invalid data
                    return loaded_state if isinstance(loaded_state, dict) else {}
            except Exception as e:
                logger.error(f"Erreur lors du chargement de l'état de la TUI: {e}")
                # Fallback to empty state if loading fails
                return {}
        return {}

    def _save_state(self) -> None:
        """Sauvegarde l'état actuel de la TUI dans un fichier."""
        try:
            self.TUI_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
            # Convert Path objects to strings for serialization
            state_to_save = self.state.copy()
            for key in ["input_path", "output_path", "audit_logs_dir"]:
                if key in state_to_save and isinstance(state_to_save[key], Path):
                    state_to_save[key] = str(state_to_save[key])

            # Gère aussi les Path dans le dictionnaire options
            if "options" in state_to_save and isinstance(state_to_save["options"], dict):
                serializable_options = {}
                for opt_key, opt_value in state_to_save["options"].items():
                    if isinstance(opt_value, Path):
                        serializable_options[opt_key] = str(opt_value)
                    else:
                        serializable_options[opt_key] = opt_value
                state_to_save["options"] = serializable_options

            with open(self.TUI_STATE_FILE, 'w', encoding='utf-8') as f:
                yaml.safe_dump(state_to_save, f, indent=2, sort_keys=False, allow_unicode=True)
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de l'état de la TUI: {e}")

    def on_mount(self) -> None:
        """Pousse le premier écran au démarrage."""
        self.push_screen("profiles")

    def on_unmount(self) -> None:
        """Sauvegarde l'état avant de quitter l'application."""
        self._save_state()


if __name__ == "__main__":
    app = LogsApp()
    app.run()