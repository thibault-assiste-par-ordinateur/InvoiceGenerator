"""
cli.py – Rich-powered command-line interface for generating PDF invoices.

Functions
---------
build_parser()         → argparse.ArgumentParser
prompt_missing(...)    → str
run_cli(argv=None)     → None
"""

from __future__ import annotations

import sys
import argparse
from pathlib import Path
from typing import Optional

import yaml                                    # type: ignore
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
from rich import box

from InvoiceGenerator.api import Creator, Invoice, Item, Provider, Client
from InvoiceGenerator.pdf import SimpleInvoice

# ————————————————————————————————————————————————
# Constants – feel free to move to a settings.py file
# ————————————————————————————————————————————————
KIND_CHOICES = ["devis", "facture"]
MODE_CHOICES = ["1", "2"]

# DEFAULT_OUTPUT = Path("./Factures/")
DEFAULT_KIND   = "facture"
DEFAULT_MODE   = "1"

PATH_PROVIDER = Path("provider.yaml")
PATH_CLIENTS  = Path("clients_abook.yaml")
PATH_ITEMS    = Path("items.yaml")

console = Console()


# ————————————————————————————————————————————————
# Helper functions
# ————————————————————————————————————————————————
def prompt_missing(
    value: Optional[str],
    prompt_text: str,
    *,
    default: str | None = None,
    choices: list[str] | None = None,
) -> str:
    """Return existing value or interactively ask with Rich Prompt."""
    if value is not None:
        return value
    return Prompt.ask(
        prompt_text,
        default=str(default) if default is not None else None,
        choices=choices,
        show_choices=bool(choices),
    )


def show_summary(file_path: Path, kind: str, mode: str, name: str) -> None:
    """Pretty console summary of the parsed arguments."""
    table = Table(title="CLI Arguments", box=box.MINIMAL_DOUBLE_HEAD)
    table.add_column("Argument", style="bold green")
    table.add_column("Value",    style="cyan")
    table.add_row("output", str(file_path))
    table.add_row("kind",   kind)
    table.add_row("mode",   mode)
    table.add_row("name",   name)
    console.print(table)
    console.print(Panel("[bold magenta]All arguments captured!"))


def build_parser() -> argparse.ArgumentParser:
    """Return an ArgumentParser for this CLI."""
    p = argparse.ArgumentParser(description="Rich interactive invoice CLI")
    p.add_argument("--output", type=Path,    help="Output directory or PDF path")
    p.add_argument("--kind",   choices=KIND_CHOICES, help="devis | facture")
    p.add_argument("--mode",   choices=MODE_CHOICES, help="1 = simple | 2 = droits d'auteur")
    p.add_argument("--name",   help="YAML key: which client/items set to use")
    return p


# ————————————————————————————————————————————————
# Core routine
# ————————————————————————————————————————————————
def run_cli(path, argv: list[str] | None = None) -> None:
    """Entry-point that encapsulates the full workflow."""
    parser = build_parser()
    args   = parser.parse_args(argv)

    # Prompt for missing values
    output = Path(
        prompt_missing(
            str(args.output) if args.output else None,
            "Enter output directory",
            default=str(path),
        )
    ).expanduser().resolve()

    kind = prompt_missing(args.kind, "Choose kind", choices=KIND_CHOICES, default=DEFAULT_KIND)
    mode = prompt_missing(args.mode, "Choose mode", choices=MODE_CHOICES, default=DEFAULT_MODE)
    name = prompt_missing(args.name, "Enter a name (YAML key)")

    show_summary(output, kind, mode, name)

    # ---------- Load YAML data ----------
    items_cfg   = yaml.safe_load(PATH_ITEMS.read_text(encoding="utf-8"))[name]
    provider_cfg = yaml.safe_load(PATH_PROVIDER.read_text(encoding="utf-8"))
    client_cfg   = yaml.safe_load(PATH_CLIENTS.read_text(encoding="utf-8"))[name]

    # Allow per-invoice override of mode inside items.yaml
    mode = items_cfg.get("mode", mode)

    # ---------- Objects ----------
    items = [
        Item(d.get("quantity"), d.get("unit_price"), description=d.get("description"))
        for d in items_cfg["items"]
    ]

    provider = Provider(
        provider_cfg["name"],
        address     = provider_cfg["address"],
        city        = provider_cfg["city"],
        zip_code    = str(provider_cfg["zip_code"]),
        country     = provider_cfg["country"],
        phone       = str(provider_cfg["phone"]),
        email       = provider_cfg["email"],
        siret       = str(provider_cfg["siret"]),
        bank_name   = provider_cfg["bank_name"],
        bank_account= provider_cfg["bank_account"],
        ss          = provider_cfg["ss"],
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
    invoice.mode       = mode
    invoice.objet      = items_cfg.get("object", "Unknown")
    invoice.commentaire= items_cfg.get("commentaire", "")
    invoice.set_kind(kind)

    for it in items:
        invoice.add_item(it)

    pdf_path = output / f"{kind}_{name}.pdf"
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    SimpleInvoice(invoice, pdf_path).gen()

    console.print(f"[bold green]✓ PDF generated → {pdf_path}")


# ————————————————————————————————————————————————
# If you prefer `python cli.py ...` directly:
# ————————————————————————————————————————————————
if __name__ == "__main__":          # pragma: no cover
    run_cli(sys.argv[1:])
