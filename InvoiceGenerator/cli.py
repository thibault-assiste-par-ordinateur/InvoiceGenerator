"""
cli.py – Rich-powered invoice CLI implemented as a class.
"""

from __future__ import annotations

import sys
import argparse
from pathlib import Path
from typing import Optional, Iterable

import yaml                                  # type: ignore
from rich.console import Console
from rich.table   import Table
from rich.panel   import Panel
from rich.prompt  import Prompt
from rich         import box

from InvoiceGenerator.api import Creator, Invoice, Item, Provider, Client
from InvoiceGenerator.pdf import SimpleInvoice


class InvoiceCLI:
    """Encapsulates the whole command-line workflow."""

    # ---------------------------------------------------------------------
    KIND_CHOICES = ["devis", "facture"]
    MODE_CHOICES = ["1", "2"]
    DEFAULT_KIND   = "facture"
    DEFAULT_MODE   = "1"
    # ---------------------------------------------------------------------

    def __init__(
        self,
        output:        Path,
        provider_path: Path,
        clients_path:  Path,
        items_path:    Path,
        console: Console | None = None,
    ) -> None:
        self.output        = output
        self.path_provider = provider_path
        self.path_clients  = clients_path
        self.path_items    = items_path
        self.console       = console or Console()

    # --------------- public API -----------------------------------------

    def run(self, argv: Iterable[str] | None = None) -> None:
        """Parse argv (or sys.argv when None) and generate the PDF."""
        args = self._build_parser().parse_args(argv)

        # Prompt for missing values
        output = Path(
            self._prompt_missing(
                str(args.output) if args.output else None,
                "Enter output directory",
                default=str(self.output),
            )
        ).expanduser().resolve()


        self.console.print(output)

        kind = self._prompt_missing(
            args.kind, "Choose kind",
            choices=self.KIND_CHOICES,
            default=self.DEFAULT_KIND,
        )
        mode = self._prompt_missing(
            args.mode, "Choose mode",
            choices=self.MODE_CHOICES,
            default=self.DEFAULT_MODE,
        )
        name = self._prompt_missing(args.name, "Enter a name (YAML key)")

        self._show_summary(output, kind, mode, name)
        self._generate_invoice(output, kind, mode, name)

    # --------------- helpers (instance methods) -------------------------

    def _build_parser(self) -> argparse.ArgumentParser:
        p = argparse.ArgumentParser(description="Rich interactive invoice CLI")
        p.add_argument("--output", type=Path)
        p.add_argument("--kind",   choices=self.KIND_CHOICES)
        p.add_argument("--mode",   choices=self.MODE_CHOICES)
        p.add_argument("--name")
        return p

    def _prompt_missing(
        self,
        value: Optional[str],
        prompt_text: str,
        *,
        default: str | None = None,
        choices: list[str] | None = None,
    ) -> str:
        if value is not None:
            return value
        return Prompt.ask(
            prompt_text,
            default=default,
            choices=choices,
            show_choices=bool(choices),
        )

    def _show_summary(self, file_path: Path, kind: str, mode: str, name: str) -> None:
        table = Table(title="CLI Arguments", box=box.MINIMAL_DOUBLE_HEAD)
        table.add_column("Argument", style="bold green")
        table.add_column("Value",    style="cyan")
        table.add_row("output", str(file_path))
        table.add_row("kind",   kind)
        table.add_row("mode",   mode)
        table.add_row("name",   name)
        self.console.print(table)
        self.console.print(Panel("[bold magenta]All arguments captured!"))

    # ---------------------------------------------------------------------
    #                  core business logic
    # ---------------------------------------------------------------------
    def _generate_invoice(self, output: Path, kind: str, mode: str, name: str) -> None:
        # YAML ────────────────────────────────────────────────────────────
        items_cfg    = yaml.safe_load(self.path_items.read_text(encoding="utf-8"))[name]
        provider_cfg = yaml.safe_load(self.path_provider.read_text(encoding="utf-8"))
        client_cfg   = yaml.safe_load(self.path_clients.read_text(encoding="utf-8"))[name]

        # Allow items.yaml to override mode
        mode = items_cfg.get("mode", mode)

        # Objects ─────────────────────────────────────────────────────────
        items = [
            Item(d["quantity"], d["unit_price"], description=d["description"])
            for d in items_cfg["items"]
        ]

        provider = Provider(
            provider_cfg["name"],
            address      = provider_cfg["address"],
            city         = provider_cfg["city"],
            zip_code     = str(provider_cfg["zip_code"]),
            country      = provider_cfg["country"],
            phone        = str(provider_cfg["phone"]),
            email        = provider_cfg["email"],
            siret        = str(provider_cfg["siret"]),
            bank_name    = provider_cfg["bank_name"],
            bank_account = provider_cfg["bank_account"],
            ss           = provider_cfg["ss"],
        )

        client = Client(
            client_cfg["name"],
            additional_name = client_cfg.get("additional_name"),
            address         = client_cfg["address"],
            city            = client_cfg["city"],
            zip_code        = str(client_cfg["zip_code"]),
            country         = client_cfg["country"],
            phone           = str(client_cfg["phone"]),
            email           = client_cfg["email"],
            bank_name       = client_cfg.get("bank_name"),
            bank_account    = client_cfg.get("bank_account"),
            siret           = str(client_cfg.get("siret")),
            note            = client_cfg.get("note"),
        )

        creator = Creator(provider_cfg["name"])
        invoice = Invoice(client, provider, creator)
        invoice.objet       = items_cfg.get("object", "Unknown")
        invoice.commentaire = items_cfg.get("commentaire", "")
        invoice.mode        = mode
        invoice.set_kind(kind)

        for it in items:
            invoice.add_item(it)

        # pdf_path = output / f"{kind}_{name}.pdf"
        # pdf_path.parent.mkdir(parents=True, exist_ok=True)
        SimpleInvoice(invoice, output).gen()

        self.console.print(f"[bold green]PDF generated -> {output}")


# -------------------------------------------------------------------------
# Optional top-level entry point (keeps `python cli.py …` working)
# -------------------------------------------------------------------------
if __name__ == "__main__":              # pragma: no cover
    InvoiceCLI(
        output        = Path("./Factures/"),
        provider_path = Path("provider.yaml"),
        clients_path  = Path("clients_abook.yaml"),
        items_path    = Path("items.yaml"),
    ).run() # defaults to sys.argv[1:] for optional arguments
