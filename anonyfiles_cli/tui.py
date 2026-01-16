from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import (
    Header,
    Footer,
    Button,
    DataTable,
    Input,
    Label,
    Static,
    RichLog,
)
from rich.text import Text


class LogViewer(Static):
    """
    Widget principal affichant les logs.
    Utilise RichLog pour un affichage coloré et performant.
    """

    def compose(self) -> ComposeResult:
        # Textual 7.0.2 compat : markup=True par défaut pour RichLog ? Vérifions.
        yield RichLog(highlight=True, markup=True, id="log_display")

    def append_log(self, line: str):
        rich_log = self.query_one(RichLog)

        # Coloration syntaxique basique en fonction du contenu
        text = Text(line)
        if "ERROR" in line or "CRITICAL" in line:
            text.stylize("bold red")
        elif "WARNING" in line:
            text.stylize("yellow")
        elif "INFO" in line:
            text.stylize("green")
        elif "DEBUG" in line:
            text.stylize("dim cyan")

        rich_log.write(text)

    def clear(self):
        self.query_one(RichLog).clear()


class LogControlPanel(Static):
    """Barre latérale ou supérieure pour les contrôles."""

    def compose(self) -> ComposeResult:
        yield Label("Filtre (Regex):")
        yield Input(placeholder="Ex: ERROR|CRITICAL", id="filter_input")
        yield Horizontal(
            Button("Recharger", id="btn_reload", variant="primary"),
            Button("Effacer", id="btn_clear", variant="error"),
            classes="button-row",
        )
        yield Label("Fichiers récents:", classes="mt-2")
        yield DataTable(id="files_table", cursor_type="row")


class LogsApp(App):
    """Application TUI pour visualiser les logs."""

    CSS = """
    Screen {
        layout: grid;
        grid-size: 4 1; /* 1 col sidebar, 3 cols content */
        grid-columns: 25% 1fr;
    }

    LogControlPanel {
        padding: 1;
        background: $surface;
        border-right: solid $primary;
        height: 100%;
    }

    LogViewer {
        height: 100%;
        background: $background;
    }
    
    .button-row {
        margin-top: 1;
        height: auto;
    }
    
    Button {
        margin-right: 1;
        width: auto;
    }
    
    .mt-2 {
        margin-top: 2;
        text-style: bold;
    }
    
    DataTable {
        height: 1fr;
        border: solid $secondary;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quitter"),
        ("r", "reload", "Recharger"),
        ("c", "clear_logs", "Effacer vue"),
    ]

    def __init__(self, log_dir: Path):
        super().__init__()
        self.log_dir = log_dir
        self.current_file: Path | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield LogControlPanel()
        yield LogViewer()
        yield Footer()

    def on_mount(self) -> None:
        self.title = "Anonyfiles Logs Viewer"
        self.refresh_file_list()

    def refresh_file_list(self):
        table = self.query_one(DataTable)
        table.clear(columns=True)
        table.add_columns("Nom", "Taille")

        if not self.log_dir.exists():
            return

        files = sorted(
            self.log_dir.glob("*.log"), key=lambda f: f.stat().st_mtime, reverse=True
        )
        # Ajoutons aussi les jsonl ou autres formats si nécessaires
        files.extend(
            sorted(
                self.log_dir.glob("*.jsonl"),
                key=lambda f: f.stat().st_mtime,
                reverse=True,
            )
        )

        # Tri global
        files = sorted(files, key=lambda f: f.stat().st_mtime, reverse=True)

        for f in files:
            size_str = f"{f.stat().st_size / 1024:.1f} KB"
            table.add_row(f.name, size_str, key=str(f))

    def load_file(self, file_path: Path, filter_text: str = ""):
        viewer = self.query_one(LogViewer)
        viewer.clear()

        if not file_path.exists():
            viewer.append_log(f"[bold red]Fichier {file_path} introuvable.[/]")
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            lines = content.splitlines()
            count = 0
            for line in lines:
                if (
                    not filter_text or filter_text.lower() in line.lower()
                ):  # Simple case-insensitive search
                    # Regex support could be added here if Input regex is valid
                    viewer.append_log(line)
                    count += 1

            if count == 0:
                viewer.append_log(
                    f"[yellow]Aucune ligne ne correspond au filtre '{filter_text}'[/]"
                )

        except Exception as e:
            viewer.append_log(f"[bold red]Erreur de lecture: {e}[/]")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "btn_reload":
            self.action_reload()
        elif button_id == "btn_clear":
            self.action_clear_logs()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Charge le fichier sélectionné dans le tableau."""
        if event.row_key:
            self.current_file = Path(event.row_key.value)
            # Récupérer le filtre actuel
            filter_text = self.query_one("#filter_input", Input).value
            self.load_file(self.current_file, filter_text)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Recharge avec le filtre quand on appuie sur Entrée."""
        if self.current_file:
            self.load_file(self.current_file, event.value)

    def action_reload(self) -> None:
        """Recharge la liste des fichiers et le fichier courant."""
        self.refresh_file_list()
        if self.current_file:
            filter_text = self.query_one("#filter_input", Input).value
            self.load_file(self.current_file, filter_text)
        else:
            self.notify("Aucun fichier sélectionné.")

    def action_clear_logs(self) -> None:
        self.query_one(LogViewer).clear()


if __name__ == "__main__":
    # Test autonome
    app = LogsApp(Path("logs"))
    app.run()
